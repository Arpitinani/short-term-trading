"""
Alpaca broker integration.

Supports paper and live trading via Alpaca's REST API.
Provides a clean interface for order submission, position management,
and account queries that the orchestrator and API layer use.

Setup:
  1. Create account at alpaca.markets
  2. Set environment variables:
     ALPACA_API_KEY=your_key
     ALPACA_SECRET_KEY=your_secret
     ALPACA_PAPER=true  (set to false for live trading)
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending_new"
    ACCEPTED = "accepted"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class OrderResult:
    order_id: str
    ticker: str
    side: str
    qty: int
    order_type: str
    status: str
    filled_price: float | None = None
    filled_qty: int = 0
    submitted_at: str = ""
    error: str | None = None


@dataclass
class PositionInfo:
    ticker: str
    qty: int
    side: str  # "long" or "short"
    entry_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


@dataclass
class AccountInfo:
    equity: float
    cash: float
    buying_power: float
    portfolio_value: float
    day_trade_count: int
    is_paper: bool


class AlpacaBroker:
    """
    Alpaca broker client. Works in three modes:
    - paper: Connects to Alpaca paper trading API
    - live: Connects to Alpaca live trading API
    - dry_run: No API calls — logs what would happen (for testing)
    """

    def __init__(self, mode: str = "dry_run"):
        """
        Args:
            mode: "paper", "live", or "dry_run"
        """
        self.mode = mode
        self._api = None
        self._connected = False

        if mode in ("paper", "live"):
            self._connect()

    def _connect(self):
        """Initialize Alpaca API client."""
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.enums import OrderSide as AlpacaSide

            api_key = os.environ.get("ALPACA_API_KEY")
            secret_key = os.environ.get("ALPACA_SECRET_KEY")

            if not api_key or not secret_key:
                logger.error("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set")
                self.mode = "dry_run"
                return

            is_paper = self.mode == "paper"
            self._api = TradingClient(api_key, secret_key, paper=is_paper)
            self._connected = True
            logger.info(f"Connected to Alpaca ({'paper' if is_paper else 'LIVE'})")

        except ImportError:
            logger.warning("alpaca-py not installed. Falling back to dry_run mode.")
            self.mode = "dry_run"
        except Exception as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            self.mode = "dry_run"

    # -------------------------------------------------------------------
    # Orders
    # -------------------------------------------------------------------

    def submit_market_order(
        self,
        ticker: str,
        qty: int,
        side: OrderSide = OrderSide.BUY,
    ) -> OrderResult:
        """Submit a market order."""
        if self.mode == "dry_run":
            return self._dry_run_order(ticker, qty, side, "market")

        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce

        request = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=AlpacaSide.BUY if side == OrderSide.BUY else AlpacaSide.SELL,
            time_in_force=TimeInForce.DAY,
        )

        try:
            order = self._api.submit_order(request)
            return self._parse_order(order)
        except Exception as e:
            return OrderResult(
                order_id="", ticker=ticker, side=side.value, qty=qty,
                order_type="market", status="error", error=str(e),
            )

    def submit_bracket_order(
        self,
        ticker: str,
        qty: int,
        side: OrderSide = OrderSide.BUY,
        take_profit_price: float | None = None,
        stop_loss_price: float | None = None,
    ) -> OrderResult:
        """Submit a bracket order (entry + stop loss + take profit)."""
        if self.mode == "dry_run":
            return self._dry_run_order(
                ticker, qty, side, "bracket",
                extra=f"TP={take_profit_price}, SL={stop_loss_price}",
            )

        from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
        from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce, OrderClass

        order_data = MarketOrderRequest(
            symbol=ticker,
            qty=qty,
            side=AlpacaSide.BUY if side == OrderSide.BUY else AlpacaSide.SELL,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=take_profit_price) if take_profit_price else None,
            stop_loss=StopLossRequest(stop_price=stop_loss_price) if stop_loss_price else None,
        )

        try:
            order = self._api.submit_order(order_data)
            return self._parse_order(order)
        except Exception as e:
            return OrderResult(
                order_id="", ticker=ticker, side=side.value, qty=qty,
                order_type="bracket", status="error", error=str(e),
            )

    def submit_limit_order(
        self,
        ticker: str,
        qty: int,
        limit_price: float,
        side: OrderSide = OrderSide.BUY,
    ) -> OrderResult:
        """Submit a limit order."""
        if self.mode == "dry_run":
            return self._dry_run_order(ticker, qty, side, "limit", extra=f"@{limit_price}")

        from alpaca.trading.requests import LimitOrderRequest
        from alpaca.trading.enums import OrderSide as AlpacaSide, TimeInForce

        request = LimitOrderRequest(
            symbol=ticker,
            qty=qty,
            side=AlpacaSide.BUY if side == OrderSide.BUY else AlpacaSide.SELL,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
        )

        try:
            order = self._api.submit_order(request)
            return self._parse_order(order)
        except Exception as e:
            return OrderResult(
                order_id="", ticker=ticker, side=side.value, qty=qty,
                order_type="limit", status="error", error=str(e),
            )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if self.mode == "dry_run":
            logger.info(f"[DRY RUN] Cancel order {order_id}")
            return True

        try:
            self._api.cancel_order_by_id(order_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def cancel_all_orders(self) -> bool:
        """Cancel all open orders."""
        if self.mode == "dry_run":
            logger.info("[DRY RUN] Cancel all orders")
            return True

        try:
            self._api.cancel_orders()
            return True
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return False

    # -------------------------------------------------------------------
    # Positions
    # -------------------------------------------------------------------

    def get_positions(self) -> list[PositionInfo]:
        """Get all open positions."""
        if self.mode == "dry_run":
            return []

        try:
            positions = self._api.get_all_positions()
            return [
                PositionInfo(
                    ticker=p.symbol,
                    qty=int(p.qty),
                    side="long" if float(p.qty) > 0 else "short",
                    entry_price=float(p.avg_entry_price),
                    current_price=float(p.current_price),
                    market_value=float(p.market_value),
                    unrealized_pnl=float(p.unrealized_pl),
                    unrealized_pnl_pct=float(p.unrealized_plpc),
                )
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    def close_position(self, ticker: str) -> OrderResult:
        """Close an entire position."""
        if self.mode == "dry_run":
            logger.info(f"[DRY RUN] Close position: {ticker}")
            return OrderResult(
                order_id="dry_run", ticker=ticker, side="sell", qty=0,
                order_type="market", status="filled",
            )

        try:
            order = self._api.close_position(ticker)
            return self._parse_order(order)
        except Exception as e:
            return OrderResult(
                order_id="", ticker=ticker, side="sell", qty=0,
                order_type="market", status="error", error=str(e),
            )

    # -------------------------------------------------------------------
    # Account
    # -------------------------------------------------------------------

    def get_account(self) -> AccountInfo:
        """Get account info."""
        if self.mode == "dry_run":
            return AccountInfo(
                equity=100_000, cash=100_000, buying_power=200_000,
                portfolio_value=100_000, day_trade_count=0, is_paper=True,
            )

        try:
            acct = self._api.get_account()
            return AccountInfo(
                equity=float(acct.equity),
                cash=float(acct.cash),
                buying_power=float(acct.buying_power),
                portfolio_value=float(acct.portfolio_value),
                day_trade_count=int(acct.daytrade_count),
                is_paper=self.mode == "paper",
            )
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return AccountInfo(
                equity=0, cash=0, buying_power=0,
                portfolio_value=0, day_trade_count=0, is_paper=True,
            )

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _dry_run_order(
        self, ticker: str, qty: int, side: OrderSide, order_type: str, extra: str = "",
    ) -> OrderResult:
        detail = f" ({extra})" if extra else ""
        logger.info(f"[DRY RUN] {side.value.upper()} {qty} {ticker} {order_type}{detail}")
        return OrderResult(
            order_id=f"dry_run_{datetime.now().strftime('%H%M%S')}",
            ticker=ticker,
            side=side.value,
            qty=qty,
            order_type=order_type,
            status="filled",  # simulate immediate fill in dry run
            filled_price=0.0,
            filled_qty=qty,
        )

    def _parse_order(self, order) -> OrderResult:
        return OrderResult(
            order_id=str(order.id),
            ticker=order.symbol,
            side=str(order.side),
            qty=int(order.qty),
            order_type=str(order.type),
            status=str(order.status),
            filled_price=float(order.filled_avg_price) if order.filled_avg_price else None,
            filled_qty=int(order.filled_qty) if order.filled_qty else 0,
            submitted_at=str(order.submitted_at) if order.submitted_at else "",
        )

    @property
    def is_connected(self) -> bool:
        return self._connected or self.mode == "dry_run"

    def status_summary(self) -> str:
        acct = self.get_account()
        positions = self.get_positions()
        lines = [
            f"Broker: Alpaca ({self.mode})",
            f"Connected: {self.is_connected}",
            f"Equity: ${acct.equity:,.0f}",
            f"Cash: ${acct.cash:,.0f}",
            f"Buying Power: ${acct.buying_power:,.0f}",
            f"Open Positions: {len(positions)}",
        ]
        for p in positions:
            lines.append(
                f"  {p.ticker}: {p.qty} shares @ ${p.entry_price:.2f} "
                f"(${p.unrealized_pnl:+,.0f} / {p.unrealized_pnl_pct:+.1%})"
            )
        return "\n".join(lines)
