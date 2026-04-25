"""
Trade orchestrator — the end-to-end workflow.

Ties together: regime detection → screening → strategy signals →
risk management → order execution → position management.

This is what Claude Code (or a cron job) calls to run the trading system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from core.data.market_data import get_price_history, fetch_close_cached
from core.data.macro import get_fear_greed
from core.indicators import calculate_rsi, calculate_sma, calculate_atr
from core.regime.detector import RegimeDetector, RegimeState, Regime, format_regime
from core.risk.manager import RiskManager, Position
from execution.alpaca_broker import AlpacaBroker, OrderSide, OrderResult

logger = logging.getLogger(__name__)


@dataclass
class TradeSignal:
    ticker: str
    strategy: str
    action: str          # "buy" or "sell"
    entry_price: float
    stop_price: float
    target_price: float | None = None
    reason: str = ""


@dataclass
class OrchestratorResult:
    timestamp: str
    regime: RegimeState
    signals: list[TradeSignal]
    orders_placed: list[OrderResult]
    orders_skipped: list[dict]  # {signal, reason}
    positions_closed: list[OrderResult]
    summary: str = ""


class Orchestrator:
    """
    Main trading orchestrator.

    Usage:
        orch = Orchestrator(broker_mode="dry_run")
        result = orch.run_scan()  # evening scan
        result = orch.check_exits()  # check if open positions need closing
    """

    def __init__(
        self,
        broker_mode: str = "dry_run",
        initial_equity: float = 100_000,
        strategies: list[str] | None = None,
    ):
        self.broker = AlpacaBroker(mode=broker_mode)
        self.risk_manager = RiskManager(equity=initial_equity)
        self.regime_detector = RegimeDetector()
        self.strategies = strategies or ["connors_rsi2", "turtle_system2"]

        # Update equity from broker if connected
        if broker_mode != "dry_run":
            acct = self.broker.get_account()
            self.risk_manager.equity = acct.equity

    def run_scan(self) -> OrchestratorResult:
        """
        Full scan cycle:
        1. Detect market regime
        2. Check existing positions for exits
        3. Scan for new entry signals
        4. Risk-check and execute
        """
        timestamp = datetime.now().isoformat()
        signals: list[TradeSignal] = []
        orders_placed: list[OrderResult] = []
        orders_skipped: list[dict] = []
        positions_closed: list[OrderResult] = []

        # --- Step 1: Detect regime ---
        regime = self._detect_regime()
        self.risk_manager.update_regime(regime)

        logger.info(f"Regime: {regime.regime.value} (score: {regime.score:+.3f})")

        # --- Step 2: Check exits on existing positions ---
        exits = self._check_exits()
        for exit_result in exits:
            positions_closed.append(exit_result)

        # --- Step 3: Generate entry signals ---
        for strategy_name in self.strategies:
            if strategy_name not in regime.allowed_strategies:
                logger.info(f"Skipping {strategy_name} — not allowed in {regime.regime.value}")
                continue

            strategy_signals = self._scan_strategy(strategy_name)
            signals.extend(strategy_signals)

        # --- Step 4: Risk-check and execute ---
        for signal in signals:
            risk_check = self.risk_manager.check_new_trade(
                ticker=signal.ticker,
                entry_price=signal.entry_price,
                stop_price=signal.stop_price,
                strategy=signal.strategy,
            )

            if not risk_check.allowed:
                orders_skipped.append({
                    "signal": f"{signal.action} {signal.ticker} ({signal.strategy})",
                    "reason": risk_check.reason,
                })
                logger.info(f"Skipped {signal.ticker}: {risk_check.reason}")
                continue

            # Execute
            order = self.broker.submit_bracket_order(
                ticker=signal.ticker,
                qty=risk_check.adjusted_shares,
                side=OrderSide.BUY if signal.action == "buy" else OrderSide.SELL,
                stop_loss_price=signal.stop_price,
                take_profit_price=signal.target_price,
            )
            orders_placed.append(order)

            # Track position in risk manager
            if order.status in ("filled", "accepted", "pending_new"):
                self.risk_manager.add_position(Position(
                    ticker=signal.ticker,
                    shares=risk_check.adjusted_shares,
                    entry_price=signal.entry_price,
                    stop_price=signal.stop_price,
                    current_price=signal.entry_price,
                    strategy=signal.strategy,
                ))

            logger.info(
                f"Executed: {signal.action} {risk_check.adjusted_shares} {signal.ticker} "
                f"@ ~${signal.entry_price:.2f}, stop ${signal.stop_price:.2f} "
                f"({signal.strategy}) — {order.status}"
            )

        # Build summary
        summary = self._build_summary(regime, signals, orders_placed, orders_skipped, positions_closed)

        return OrchestratorResult(
            timestamp=timestamp,
            regime=regime,
            signals=signals,
            orders_placed=orders_placed,
            orders_skipped=orders_skipped,
            positions_closed=positions_closed,
            summary=summary,
        )

    def check_exits(self) -> list[OrderResult]:
        """Check if any open positions need to be closed based on strategy signals."""
        return self._check_exits()

    # -------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------

    def _detect_regime(self) -> RegimeState:
        """Fetch macro data and detect current regime."""
        spx = fetch_close_cached("^GSPC", period="1y")
        vix = fetch_close_cached("^VIX", period="1y")
        tnx = fetch_close_cached("^TNX", period="1y")
        irx = fetch_close_cached("^IRX", period="1y")

        fg = get_fear_greed()

        data = {"spx": spx, "vix": vix, "tnx": tnx, "irx": irx}
        if fg.get("score") is not None:
            data["fear_greed_score"] = fg["score"]

        return self.regime_detector.detect(data)

    def _scan_strategy(self, strategy_name: str) -> list[TradeSignal]:
        """Generate entry signals for a specific strategy."""
        signals = []

        if strategy_name == "connors_rsi2":
            signals = self._scan_connors_rsi2()
        elif strategy_name == "turtle_system2":
            signals = self._scan_turtle()

        return signals

    def _scan_connors_rsi2(self) -> list[TradeSignal]:
        """Scan SPY for RSI(2) entry signals."""
        signals = []

        for ticker in ["SPY"]:
            df = get_price_history(ticker, period="1y")
            if df.empty or len(df) < 200:
                continue

            close = df["Close"]
            rsi2 = calculate_rsi(close, period=2)
            sma200 = calculate_sma(close, period=200)
            atr = calculate_atr(df["High"], df["Low"], close, period=14)

            current_rsi = float(rsi2.iloc[-1])
            current_price = float(close.iloc[-1])
            current_sma200 = float(sma200.iloc[-1])
            current_atr = float(atr.iloc[-1])

            # Entry: RSI(2) < 5 and price > SMA(200)
            if current_rsi < 5 and current_price > current_sma200:
                stop = current_price - 2 * current_atr  # 2 ATR stop
                target = current_price + 3 * current_atr  # 3 ATR target

                signals.append(TradeSignal(
                    ticker=ticker,
                    strategy="connors_rsi2",
                    action="buy",
                    entry_price=current_price,
                    stop_price=round(stop, 2),
                    target_price=round(target, 2),
                    reason=f"RSI(2)={current_rsi:.1f} < 5, above 200 SMA",
                ))

        return signals

    def _scan_turtle(self) -> list[TradeSignal]:
        """Scan SPY for Turtle System 2 breakout signals."""
        signals = []

        for ticker in ["SPY"]:
            df = get_price_history(ticker, period="1y")
            if df.empty or len(df) < 60:
                continue

            high = df["High"]
            low = df["Low"]
            close = df["Close"]
            atr = calculate_atr(high, low, close, period=20)

            # 55-day high (prior day)
            entry_high = float(high.rolling(55).max().iloc[-2])
            current_high = float(high.iloc[-1])
            current_price = float(close.iloc[-1])
            current_atr = float(atr.iloc[-1])

            # Entry: today's high breaks above prior 55-day high
            if current_high > entry_high and current_atr > 0:
                stop = current_price - 2 * current_atr
                # Turtle exit is at 20-day low, but set initial target at 4 ATR
                target = current_price + 4 * current_atr

                signals.append(TradeSignal(
                    ticker=ticker,
                    strategy="turtle_system2",
                    action="buy",
                    entry_price=current_price,
                    stop_price=round(stop, 2),
                    target_price=round(target, 2),
                    reason=f"55-day breakout: high {current_high:.2f} > {entry_high:.2f}",
                ))

        return signals

    def _check_exits(self) -> list[OrderResult]:
        """Check open positions for exit signals."""
        results = []

        for position in list(self.risk_manager.positions):
            df = get_price_history(position.ticker, period="6mo")
            if df.empty:
                continue

            close = df["Close"]
            current_price = float(close.iloc[-1])
            position.current_price = current_price

            should_exit = False
            reason = ""

            if position.strategy == "connors_rsi2":
                rsi2 = calculate_rsi(close, period=2)
                if float(rsi2.iloc[-1]) > 65:
                    should_exit = True
                    reason = f"RSI(2) exit: {float(rsi2.iloc[-1]):.1f} > 65"

            elif position.strategy == "turtle_system2":
                exit_low = float(df["Low"].rolling(20).min().iloc[-2])
                if current_price < exit_low:
                    should_exit = True
                    reason = f"20-day low exit: {current_price:.2f} < {exit_low:.2f}"

            # Stop loss check (all strategies)
            if current_price <= position.stop_price:
                should_exit = True
                reason = f"Stop loss hit: {current_price:.2f} <= {position.stop_price:.2f}"

            if should_exit:
                logger.info(f"Exit signal: {position.ticker} — {reason}")
                order = self.broker.close_position(position.ticker)
                self.risk_manager.remove_position(position.ticker)
                self.risk_manager.record_realized_pnl(position.unrealized_pnl)
                results.append(order)

        return results

    def _build_summary(
        self,
        regime: RegimeState,
        signals: list[TradeSignal],
        orders: list[OrderResult],
        skipped: list[dict],
        closed: list[OrderResult],
    ) -> str:
        lines = [
            f"=== Trading Scan Summary ===",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Regime: {regime.regime.value} (score: {regime.score:+.3f})",
            f"Signals: {len(signals)}",
            f"Orders placed: {len(orders)}",
            f"Orders skipped: {len(skipped)}",
            f"Positions closed: {len(closed)}",
            f"",
        ]

        if orders:
            lines.append("Orders:")
            for o in orders:
                lines.append(f"  {o.side} {o.qty} {o.ticker} ({o.order_type}) — {o.status}")

        if skipped:
            lines.append("Skipped:")
            for s in skipped:
                lines.append(f"  {s['signal']} — {s['reason']}")

        if closed:
            lines.append("Closed:")
            for c in closed:
                lines.append(f"  {c.ticker} — {c.status}")

        lines.append(f"\n{self.risk_manager.format_status()}")

        return "\n".join(lines)
