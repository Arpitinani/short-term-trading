"""
Portfolio risk manager.

Enforces position limits, portfolio heat, and daily loss limits.
Integrates with regime detector for dynamic sizing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from core.regime.detector import Regime, RegimeState


@dataclass
class Position:
    ticker: str
    shares: int
    entry_price: float
    stop_price: float
    current_price: float = 0.0
    strategy: str = ""

    @property
    def position_value(self) -> float:
        return self.shares * self.current_price

    @property
    def risk_dollars(self) -> float:
        """Dollar risk = shares * (entry - stop)."""
        return self.shares * abs(self.entry_price - self.stop_price)

    @property
    def unrealized_pnl(self) -> float:
        return self.shares * (self.current_price - self.entry_price)

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.entry_price <= 0:
            return 0.0
        return (self.current_price / self.entry_price - 1)


@dataclass
class RiskCheck:
    allowed: bool
    reason: str = ""
    adjusted_shares: int = 0
    adjusted_risk_pct: float = 0.0


@dataclass
class DailyPnL:
    realized: float = 0.0
    unrealized: float = 0.0

    @property
    def total(self) -> float:
        return self.realized + self.unrealized


class RiskManager:
    """
    Portfolio-level risk management.

    Enforces:
      - Max risk per trade (regime-dependent)
      - Max portfolio heat (sum of all open position risks)
      - Max daily loss (stop trading for the day)
      - Strategy allowlist based on regime
    """

    def __init__(
        self,
        equity: float = 100_000,
        max_risk_per_trade: float = 0.01,     # 1% default
        max_portfolio_heat: float = 0.05,      # 5% default
        max_daily_loss_pct: float = 0.03,      # 3% default
    ):
        self.equity = equity
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_heat = max_portfolio_heat
        self.max_daily_loss_pct = max_daily_loss_pct
        self.positions: list[Position] = []
        self.daily_pnl = DailyPnL()
        self._current_regime: RegimeState | None = None

    def update_regime(self, regime_state: RegimeState) -> None:
        """Update risk limits based on current market regime."""
        self._current_regime = regime_state
        self.max_risk_per_trade = regime_state.max_position_pct
        self.max_portfolio_heat = regime_state.max_heat_pct

    def check_new_trade(
        self,
        ticker: str,
        entry_price: float,
        stop_price: float,
        strategy: str = "",
    ) -> RiskCheck:
        """
        Check if a new trade is allowed under current risk rules.

        Returns RiskCheck with allowed=True/False and adjusted_shares.
        """
        # Check strategy allowlist
        if self._current_regime and strategy:
            if strategy not in self._current_regime.allowed_strategies:
                return RiskCheck(
                    allowed=False,
                    reason=f"Strategy '{strategy}' not allowed in {self._current_regime.regime.value} regime",
                )

        # Check daily loss limit
        if self.daily_pnl.total <= -(self.equity * self.max_daily_loss_pct):
            return RiskCheck(
                allowed=False,
                reason=f"Daily loss limit hit ({self.daily_pnl.total:,.0f} / {-self.equity * self.max_daily_loss_pct:,.0f})",
            )

        # Check portfolio heat
        current_heat = self.portfolio_heat
        remaining_heat = self.max_portfolio_heat - current_heat
        if remaining_heat <= 0:
            return RiskCheck(
                allowed=False,
                reason=f"Portfolio heat at limit ({current_heat:.1%} / {self.max_portfolio_heat:.1%})",
            )

        # Calculate position size
        risk_per_share = abs(entry_price - stop_price)
        if risk_per_share <= 0:
            return RiskCheck(allowed=False, reason="Invalid stop price (no risk)")

        # Risk budget = min(per-trade limit, remaining heat)
        max_risk_dollars = min(
            self.equity * self.max_risk_per_trade,
            self.equity * remaining_heat,
        )

        shares = int(max_risk_dollars / risk_per_share)
        if shares <= 0:
            return RiskCheck(allowed=False, reason="Position too small after risk adjustment")

        actual_risk_pct = (shares * risk_per_share) / self.equity

        return RiskCheck(
            allowed=True,
            adjusted_shares=shares,
            adjusted_risk_pct=actual_risk_pct,
        )

    @property
    def portfolio_heat(self) -> float:
        """Sum of all open position risks as fraction of equity."""
        if self.equity <= 0:
            return 0.0
        total_risk = sum(p.risk_dollars for p in self.positions)
        return total_risk / self.equity

    @property
    def total_exposure(self) -> float:
        """Total position value as fraction of equity."""
        if self.equity <= 0:
            return 0.0
        total_value = sum(p.position_value for p in self.positions)
        return total_value / self.equity

    def add_position(self, position: Position) -> None:
        self.positions.append(position)

    def remove_position(self, ticker: str) -> Position | None:
        for i, p in enumerate(self.positions):
            if p.ticker == ticker:
                return self.positions.pop(i)
        return None

    def record_realized_pnl(self, pnl: float) -> None:
        self.daily_pnl.realized += pnl

    def reset_daily(self) -> None:
        """Call at start of each trading day."""
        self.daily_pnl = DailyPnL()

    def status(self) -> dict:
        """Current risk status."""
        return {
            "equity": self.equity,
            "positions": len(self.positions),
            "portfolio_heat": f"{self.portfolio_heat:.1%}",
            "max_heat": f"{self.max_portfolio_heat:.1%}",
            "total_exposure": f"{self.total_exposure:.1%}",
            "daily_pnl": f"${self.daily_pnl.total:,.0f}",
            "daily_loss_limit": f"${-self.equity * self.max_daily_loss_pct:,.0f}",
            "regime": self._current_regime.regime.value if self._current_regime else "unknown",
            "max_risk_per_trade": f"{self.max_risk_per_trade:.1%}",
        }

    def format_status(self) -> str:
        s = self.status()
        return "\n".join([
            f"Risk Manager Status",
            f"{'=' * 40}",
            f"Equity:          ${s['equity']:,.0f}",
            f"Positions:       {s['positions']}",
            f"Portfolio Heat:  {s['portfolio_heat']} / {s['max_heat']}",
            f"Total Exposure:  {s['total_exposure']}",
            f"Daily P&L:       {s['daily_pnl']}",
            f"Daily Loss Limit:{s['daily_loss_limit']}",
            f"Regime:          {s['regime']}",
            f"Max Risk/Trade:  {s['max_risk_per_trade']}",
        ])
