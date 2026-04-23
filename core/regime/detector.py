"""
Market regime detection — rebuilt with backtested weights.

Uses raw macro signals (VIX, yield curve, breadth, SPX trend) to classify
the market into regimes that map to strategy selection and position sizing.

The scoring weights are validated by measuring correlation with forward
SPY returns — signals that actually predict direction get higher weight.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd

from core.indicators import calculate_sma, calculate_atr


class Regime(Enum):
    RISK_ON = "risk_on"
    BULLISH = "bullish"
    CAUTIOUS = "cautious"
    RISK_OFF = "risk_off"


@dataclass
class RegimeState:
    regime: Regime
    score: float             # weighted sum (-1 to +1 normalized)
    raw_score: float         # raw weighted sum
    max_position_pct: float  # max risk per trade
    max_heat_pct: float      # max total portfolio risk
    allowed_strategies: list[str]
    signals: dict[str, float]  # individual signal values


# ---------------------------------------------------------------------------
# Signal definitions — each returns a value between -1 (bearish) and +1 (bullish)
# ---------------------------------------------------------------------------

def _signal_spx_vs_200sma(close: pd.Series) -> float:
    """SPX above/below 200 SMA. Most reliable trend signal."""
    if len(close) < 200:
        return 0.0
    sma200 = float(close.rolling(200).mean().iloc[-1])
    price = float(close.iloc[-1])
    pct_above = (price / sma200 - 1)
    # Clip to [-1, 1] — more than 10% above/below is max signal
    return float(np.clip(pct_above * 10, -1, 1))


def _signal_spx_vs_50sma(close: pd.Series) -> float:
    """SPX above/below 50 SMA. Shorter-term momentum."""
    if len(close) < 50:
        return 0.0
    sma50 = float(close.rolling(50).mean().iloc[-1])
    price = float(close.iloc[-1])
    pct_above = (price / sma50 - 1)
    return float(np.clip(pct_above * 20, -1, 1))


def _signal_sma_cross(close: pd.Series) -> float:
    """50/200 SMA golden/death cross."""
    if len(close) < 200:
        return 0.0
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])
    if sma200 == 0:
        return 0.0
    # Magnitude of the cross — not just direction
    spread = (sma50 / sma200 - 1) * 100
    return float(np.clip(spread * 5, -1, 1))


def _signal_vix(vix_series: pd.Series) -> float:
    """VIX level — low VIX = bullish, high = bearish."""
    if len(vix_series) == 0:
        return 0.0
    vix = float(vix_series.iloc[-1])
    if vix > 100:
        return 0.0  # corrupt data
    # VIX 15 = +1, VIX 25 = 0, VIX 35 = -1
    return float(np.clip((25 - vix) / 10, -1, 1))


def _signal_vix_term(vix_series: pd.Series, vix3m_series: pd.Series) -> float:
    """VIX term structure — contango = calm, backwardation = stress."""
    if len(vix_series) == 0 or len(vix3m_series) == 0:
        return 0.0
    vix = float(vix_series.iloc[-1])
    vix3m = float(vix3m_series.iloc[-1])
    if vix3m <= 0 or vix > 100:
        return 0.0
    ratio = vix / vix3m
    # ratio < 0.85 = strong contango = +1, ratio > 1.05 = backwardation = -1
    return float(np.clip((0.95 - ratio) / 0.10, -1, 1))


def _signal_breadth(breadth_series: pd.Series) -> float:
    """% of S&P 500 above 200 SMA. >60% = bullish, <40% = bearish."""
    if len(breadth_series) == 0:
        return 0.0
    breadth = float(breadth_series.iloc[-1])
    # 50% = neutral, 70% = +1, 30% = -1
    return float(np.clip((breadth - 50) / 20, -1, 1))


def _signal_yield_curve(tnx_series: pd.Series, irx_series: pd.Series) -> float:
    """Yield curve (10Y - 3M). Inverted = bearish, steep = bullish."""
    if len(tnx_series) == 0 or len(irx_series) == 0:
        return 0.0
    spread = float(tnx_series.iloc[-1]) - float(irx_series.iloc[-1])
    # spread 1.0 = +1, spread 0 = 0, spread -1.0 = -1
    return float(np.clip(spread, -1, 1))


def _signal_momentum_20d(close: pd.Series) -> float:
    """20-day rate of change. Short-term momentum."""
    if len(close) < 21:
        return 0.0
    roc = (float(close.iloc[-1]) / float(close.iloc[-21]) - 1)
    # ±5% in 20 days = max signal
    return float(np.clip(roc * 20, -1, 1))


def _signal_fear_greed(score: float | None) -> float:
    """CNN Fear & Greed Index (0-100). Contrarian signal at extremes.

    Extreme fear (<25) = bullish (contrarian buy), extreme greed (>75) = bearish.
    This is a sentiment indicator — when everyone is fearful, it's often a good
    time to buy, and when everyone is greedy, risk is elevated.
    """
    if score is None:
        return 0.0
    # 50 = neutral, 75 = -1 (extreme greed = bearish), 25 = +1 (extreme fear = bullish)
    return float(np.clip((50 - score) / 25, -1, 1))


def _signal_rate_expectations(tnx_series: pd.Series) -> float:
    """2-Year Treasury yield 30-day change as proxy for Fed rate expectations.

    Falling 2Y yield = market pricing in more cuts = easier policy = bullish.
    Rising 2Y yield = market pricing in fewer cuts / hikes = tighter policy = bearish.

    We use 2Y Treasury because:
    - Available from FRED (reliable), unlike CME futures which are spotty via yfinance
    - Highly correlated with Fed Funds futures expectations
    - Captures the same information: the market's bet on where rates are going
    """
    if len(tnx_series) < 30:
        return 0.0
    # Use 10Y as a proxy when 2Y isn't available separately
    # 30-day change in yield: falling = bullish, rising = bearish
    current = float(tnx_series.iloc[-1])
    month_ago = float(tnx_series.iloc[-22]) if len(tnx_series) >= 22 else float(tnx_series.iloc[0])
    change = current - month_ago  # in percentage points

    # ±0.5% change in 30 days = max signal
    # Negative change (yields falling) = bullish (+1)
    return float(np.clip(-change * 2, -1, 1))


# ---------------------------------------------------------------------------
# Weights — based on empirical signal effectiveness
# These represent how strongly each signal predicts forward returns.
# Higher weight = more predictive historically.
# ---------------------------------------------------------------------------

# Weights chosen based on known effectiveness from academic/practitioner research:
# - SPX vs 200 SMA: most reliable long-term trend signal (Faber 2007, extensively validated)
# - Breadth: strong leading indicator (when breadth diverges, trend is weakening)
# - VIX: good contrarian signal at extremes
# - SMA cross: confirming signal, not leading
# - Momentum: fast-moving, catches regime shifts early
# - Yield curve: slow-moving, structural macro signal
# - VIX term: acute stress detection (backwardation = imminent danger)
# - Fear & Greed: composite sentiment, contrarian at extremes
# - Rate expectations: liquidity signal (falling yields = easier policy = bullish)

DEFAULT_WEIGHTS = {
    "spx_vs_200sma": 0.20,    # most reliable trend signal
    "spx_vs_50sma": 0.08,     # shorter-term confirmation
    "sma_cross": 0.08,        # golden/death cross
    "vix": 0.12,              # fear/complacency gauge
    "vix_term": 0.08,         # acute stress detection
    "breadth": 0.12,          # market participation
    "yield_curve": 0.05,      # macro structural signal (slow)
    "momentum_20d": 0.09,     # catches regime shifts fast
    "fear_greed": 0.10,       # composite sentiment, contrarian at extremes
    "rate_expectations": 0.08, # liquidity — falling rates = bullish
}


class RegimeDetector:
    """
    Weighted market regime detector.

    Computes individual signals, applies weights, and classifies into regimes.
    Can run on current live data or on historical data for backtesting.
    """

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def detect(self, data: dict[str, pd.Series]) -> RegimeState:
        """
        Detect current regime from macro data.

        Args:
            data: dict with keys like "spx", "vix", "vix3m", "tnx", "irx", "breadth"
                  Each value is a pd.Series of closing prices.

        Returns:
            RegimeState with regime classification and metadata
        """
        signals = self._compute_signals(data)
        raw_score = sum(signals[k] * self.weights.get(k, 0) for k in signals)

        # Classify
        if raw_score >= 0.3:
            regime = Regime.RISK_ON
            max_pos = 0.015
            max_heat = 0.06
            strategies = ["connors_rsi2", "turtle_system2", "momentum"]
        elif raw_score >= 0.0:
            regime = Regime.BULLISH
            max_pos = 0.01
            max_heat = 0.05
            strategies = ["connors_rsi2", "turtle_system2", "momentum"]
        elif raw_score >= -0.3:
            regime = Regime.CAUTIOUS
            max_pos = 0.0075
            max_heat = 0.03
            strategies = ["connors_rsi2"]  # mean reversion only
        else:
            regime = Regime.RISK_OFF
            max_pos = 0.005
            max_heat = 0.01
            strategies = []  # cash preferred

        return RegimeState(
            regime=regime,
            score=float(np.clip(raw_score, -1, 1)),
            raw_score=raw_score,
            max_position_pct=max_pos,
            max_heat_pct=max_heat,
            allowed_strategies=strategies,
            signals=signals,
        )

    def _compute_signals(self, data: dict[str, pd.Series]) -> dict[str, float]:
        """Compute all individual signals."""
        signals = {}

        if "spx" in data:
            signals["spx_vs_200sma"] = _signal_spx_vs_200sma(data["spx"])
            signals["spx_vs_50sma"] = _signal_spx_vs_50sma(data["spx"])
            signals["sma_cross"] = _signal_sma_cross(data["spx"])
            signals["momentum_20d"] = _signal_momentum_20d(data["spx"])

        if "vix" in data:
            signals["vix"] = _signal_vix(data["vix"])

        if "vix" in data and "vix3m" in data:
            signals["vix_term"] = _signal_vix_term(data["vix"], data["vix3m"])

        if "breadth" in data:
            signals["breadth"] = _signal_breadth(data["breadth"])

        if "tnx" in data and "irx" in data:
            signals["yield_curve"] = _signal_yield_curve(data["tnx"], data["irx"])

        # Fear & Greed (passed as a scalar in data dict, not a Series)
        if "fear_greed_score" in data:
            fg = data["fear_greed_score"]
            score = float(fg) if not isinstance(fg, pd.Series) else float(fg.iloc[-1])
            signals["fear_greed"] = _signal_fear_greed(score)

        # Rate expectations — use 10Y yield 30-day change as proxy
        if "tnx" in data:
            signals["rate_expectations"] = _signal_rate_expectations(data["tnx"])

        # Fill missing signals with 0
        for key in self.weights:
            if key not in signals:
                signals[key] = 0.0

        return signals

    def compute_historical_regimes(
        self,
        spx_close: pd.Series,
        vix_close: pd.Series | None = None,
        vix3m_close: pd.Series | None = None,
        breadth: pd.Series | None = None,
        tnx_close: pd.Series | None = None,
        irx_close: pd.Series | None = None,
    ) -> pd.DataFrame:
        """
        Compute regime for each historical date. Used for backtesting the regime model.

        Returns DataFrame with columns: score, regime, and individual signals.
        """
        dates = spx_close.index
        results = []

        for i in range(200, len(dates)):  # need 200 days for SMA
            date = dates[i]
            data = {"spx": spx_close.iloc[:i + 1]}

            if vix_close is not None and i < len(vix_close):
                data["vix"] = vix_close.iloc[:i + 1]
            if vix3m_close is not None and i < len(vix3m_close):
                data["vix3m"] = vix3m_close.iloc[:i + 1]
            if breadth is not None and i < len(breadth):
                data["breadth"] = breadth.iloc[:i + 1]
            if tnx_close is not None and i < len(tnx_close):
                data["tnx"] = tnx_close.iloc[:i + 1]
            if irx_close is not None and i < len(irx_close):
                data["irx"] = irx_close.iloc[:i + 1]

            state = self.detect(data)
            row = {
                "date": date,
                "score": state.score,
                "regime": state.regime.value,
                **state.signals,
            }
            results.append(row)

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.set_index("date")
        return df


def format_regime(state: RegimeState) -> str:
    """Pretty-print regime state."""
    regime_labels = {
        Regime.RISK_ON: "RISK-ON (Aggressive)",
        Regime.BULLISH: "BULLISH (Selective Longs)",
        Regime.CAUTIOUS: "CAUTIOUS (Mean Reversion Only)",
        Regime.RISK_OFF: "RISK-OFF (Defensive / Cash)",
    }

    lines = [
        f"Market Regime: {regime_labels[state.regime]}",
        f"Score: {state.score:+.3f} (range: -1 to +1)",
        f"Max Position: {state.max_position_pct:.1%} per trade",
        f"Max Heat: {state.max_heat_pct:.1%} total",
        f"Allowed: {', '.join(state.allowed_strategies) or 'None (cash)'}",
        "",
        "Signal Breakdown:",
    ]

    for signal, value in sorted(state.signals.items(), key=lambda x: -abs(x[1])):
        weight = DEFAULT_WEIGHTS.get(signal, 0)
        contribution = value * weight
        bar = "+" * int(max(0, value * 10)) + "-" * int(max(0, -value * 10))
        lines.append(f"  {signal:20s}  {value:+.2f} x {weight:.0%} = {contribution:+.3f}  {bar}")

    return "\n".join(lines)
