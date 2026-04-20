"""Technical indicators: RSI, MACD, Bollinger Bands, Stochastic, ADX, ATR, SMA."""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI using Wilder's smoothing (EMA), matching Fidelity/TradingView."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing: EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# ---------------------------------------------------------------------------
# SMA / EMA
# ---------------------------------------------------------------------------


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=period).mean()


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=period, adjust=False).mean()


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------


def calculate_macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD indicator.

    Returns (macd_line, signal_line, histogram).
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.

    Returns (upper_band, middle_band, lower_band).
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


# ---------------------------------------------------------------------------
# Stochastic Oscillator
# ---------------------------------------------------------------------------


def calculate_stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator.

    Returns (%K, %D).
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    denom = highest_high - lowest_low
    denom = denom.replace(0, np.nan)  # avoid division by zero

    k = 100 * (close - lowest_low) / denom
    d = k.rolling(window=d_period).mean()
    return k, d


# ---------------------------------------------------------------------------
# ADX (Average Directional Index)
# ---------------------------------------------------------------------------


def calculate_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Average Directional Index.

    Returns (adx, plus_di, minus_di).
    """
    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Directional movement
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low

    plus_dm = pd.Series(0.0, index=high.index)
    minus_dm = pd.Series(0.0, index=high.index)

    plus_mask = (up_move > down_move) & (up_move > 0)
    minus_mask = (down_move > up_move) & (down_move > 0)

    plus_dm[plus_mask] = up_move[plus_mask]
    minus_dm[minus_mask] = down_move[minus_mask]

    # Smoothed averages (Wilder's smoothing = EMA with alpha=1/period)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di_smooth = plus_dm.ewm(alpha=1 / period, adjust=False).mean()
    minus_di_smooth = minus_dm.ewm(alpha=1 / period, adjust=False).mean()

    # Directional indicators
    plus_di = 100 * plus_di_smooth / atr.replace(0, np.nan)
    minus_di = 100 * minus_di_smooth / atr.replace(0, np.nan)

    # DX and ADX
    di_sum = plus_di + minus_di
    di_sum = di_sum.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / di_sum

    adx = dx.ewm(alpha=1 / period, adjust=False).mean()

    return adx, plus_di, minus_di


# ---------------------------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------------------------


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Average True Range.

    Returns ATR series.
    """
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


# ---------------------------------------------------------------------------
# Volume Ratio
# ---------------------------------------------------------------------------


def calculate_volume_ratio(volume: pd.Series, period: int = 20) -> pd.Series:
    """
    Current volume / SMA(volume, period).

    >1.5 = high volume, <0.5 = low volume.
    """
    avg = volume.rolling(window=period).mean()
    return volume / avg.replace(0, np.nan)


def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume. Cumulative volume signed by price direction."""
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    return (volume * direction).cumsum()


def calculate_bb_width(
    upper: pd.Series, lower: pd.Series, middle: pd.Series,
) -> pd.Series:
    """Bollinger Band width as percentage of middle band."""
    return ((upper - lower) / middle.replace(0, np.nan)) * 100


# ---------------------------------------------------------------------------
# Ichimoku Cloud
# ---------------------------------------------------------------------------


def calculate_ichimoku(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
    displacement: int = 26,
) -> dict[str, pd.Series | int]:
    """
    Ichimoku Cloud indicator.

    Returns dict with keys: tenkan, kijun, senkou_a, senkou_b, chikou, displacement.
    senkou_a/b are raw (un-shifted) — caller should shift forward by *displacement*.
    chikou is already shifted backward.
    """
    tenkan = (high.rolling(tenkan_period).max() + low.rolling(tenkan_period).min()) / 2
    kijun = (high.rolling(kijun_period).max() + low.rolling(kijun_period).min()) / 2

    senkou_a = (tenkan + kijun) / 2
    senkou_b = (high.rolling(senkou_b_period).max() + low.rolling(senkou_b_period).min()) / 2

    chikou = close.shift(-displacement)

    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "senkou_a": senkou_a,
        "senkou_b": senkou_b,
        "chikou": chikou,
        "displacement": displacement,
    }


# ---------------------------------------------------------------------------
# Support & Resistance
# ---------------------------------------------------------------------------


def calculate_relative_strength(
    ticker_close: pd.Series,
    benchmark_close: pd.Series,
    period: int = 63,
) -> pd.Series:
    """Relative performance: ticker return minus benchmark return over rolling period."""
    ticker_ret = ticker_close.pct_change(period)
    bench_ret = benchmark_close.pct_change(period)
    return ticker_ret - bench_ret


def calculate_anchored_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    anchor_date: pd.Timestamp,
) -> pd.Series:
    """VWAP anchored from a specific date forward."""
    typical_price = (high + low + close) / 3
    mask = close.index >= anchor_date
    tp_vol = (typical_price * volume).loc[mask].cumsum()
    cum_vol = volume.loc[mask].cumsum()
    vwap = tp_vol / cum_vol.replace(0, np.nan)
    return vwap.reindex(close.index)


# ---------------------------------------------------------------------------
# Support & Resistance
# ---------------------------------------------------------------------------


def calculate_support_resistance(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series | None = None,
    window: int = 20,
    num_levels: int = 5,
    cluster_pct: float | None = None,
    atr_series: pd.Series | None = None,
    atr_multiplier: float = 0.5,
) -> list[dict]:
    """
    Detect support and resistance levels using local min/max peaks with
    volume confirmation and bounce-quality scoring.

    cluster_pct: Fixed % band for clustering. If None and atr_series is
    provided, uses atr_multiplier * ATR / price * 100 (adapts to volatility).
    Falls back to 1.5% if neither is provided.

    Each touch is scored:
      - Base: 1.0
      - Volume bonus: +0.5 if bar volume > 1.3x average
      - Bounce bonus: +0.5 if price reversed within 3 bars (clean bounce)
      - Pass-through penalty: -0.3 if price broke through the level

    Returns list of dicts with: price, type, strength (composite score),
    touches, bounces, volume_confirmed, quality, label.
    """
    if len(close) < window * 2:
        return []

    half = window // 2

    # Average volume for volume confirmation
    avg_vol = float(volume.mean()) if volume is not None and not volume.empty else 0

    # Each candidate: (price, type, per-touch score)
    candidates: list[tuple[float, str, float]] = []

    for i in range(half, len(close) - half):
        local_high = high.iloc[i - half : i + half + 1]
        local_low = low.iloc[i - half : i + half + 1]

        is_local_high = high.iloc[i] == local_high.max()
        is_local_low = low.iloc[i] == local_low.min()

        for is_peak, level_type, peak_price in [
            (is_local_high, "resistance", float(high.iloc[i])),
            (is_local_low, "support", float(low.iloc[i])),
        ]:
            if not is_peak:
                continue

            score = 1.0

            # Volume confirmation
            if volume is not None and avg_vol > 0:
                bar_vol = float(volume.iloc[i])
                if bar_vol > avg_vol * 1.3:
                    score += 0.5

            # Bounce quality: did price reverse or break through?
            lookahead = min(3, len(close) - i - 1)
            if lookahead > 0:
                future_close = float(close.iloc[i + lookahead])
                if level_type == "support":
                    if future_close > peak_price * 1.005:
                        score += 0.5   # clean bounce up
                    elif future_close < peak_price * 0.995:
                        score -= 0.3   # broke through down
                else:
                    if future_close < peak_price * 0.995:
                        score += 0.5   # clean rejection down
                    elif future_close > peak_price * 1.005:
                        score -= 0.3   # broke through up

            candidates.append((peak_price, level_type, max(score, 0.1)))

    if not candidates:
        return []

    # Determine effective cluster percentage
    current_price = float(close.iloc[-1])
    if cluster_pct is not None:
        eff_cluster_pct = cluster_pct
    elif atr_series is not None and not atr_series.empty:
        atr_val = float(atr_series.iloc[-1])
        eff_cluster_pct = atr_multiplier * atr_val / current_price * 100 if current_price > 0 else 1.5
    else:
        eff_cluster_pct = 1.5

    # Cluster nearby levels
    candidates.sort(key=lambda x: x[0])
    clusters: list[dict] = []

    for price, level_type, touch_score in candidates:
        merged = False
        for cluster in clusters:
            if abs(price - cluster["price"]) / cluster["price"] * 100 <= eff_cluster_pct:
                n = cluster["touches"]
                cluster["price"] = (cluster["price"] * n + price) / (n + 1)
                cluster["touches"] += 1
                cluster["total_score"] += touch_score
                if touch_score >= 1.5:
                    cluster["bounces"] += 1
                if touch_score >= 1.4:
                    cluster["vol_confirmed"] += 1
                if level_type == "resistance":
                    cluster["type"] = "resistance"
                merged = True
                break
        if not merged:
            clusters.append({
                "price": price,
                "type": level_type,
                "touches": 1,
                "total_score": touch_score,
                "bounces": 1 if touch_score >= 1.5 else 0,
                "vol_confirmed": 1 if touch_score >= 1.4 else 0,
            })

    # Rank by composite score
    clusters.sort(key=lambda x: x["total_score"], reverse=True)
    current_price = float(close.iloc[-1])

    results = []
    for c in clusters[:num_levels]:
        c_type = "resistance" if c["price"] > current_price else "support"
        total = round(c["total_score"], 1)
        touches = c["touches"]
        bounces = c["bounces"]
        vol_conf = c["vol_confirmed"]

        if bounces >= 2 and vol_conf >= 1:
            quality = "Strong"
        elif bounces >= 1 or vol_conf >= 1:
            quality = "Moderate"
        else:
            quality = "Weak"

        type_word = "Support" if c_type == "support" else "Resistance"
        results.append({
            "price": round(c["price"], 2),
            "type": c_type,
            "strength": total,
            "touches": touches,
            "bounces": bounces,
            "volume_confirmed": vol_conf,
            "quality": quality,
            "label": f"{type_word} ${c['price']:.2f} ({quality}, {touches} touches, {bounces} bounces)",
        })

    results.sort(key=lambda x: x["price"])
    return results
