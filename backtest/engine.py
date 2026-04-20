"""Core backtesting engine. Event-driven for correct position sizing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from .costs import CostModel
from .metrics import compute_metrics
from core.risk.position_sizing import fixed_fractional_size
from strategies.base import Strategy


@dataclass
class Trade:
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    shares: int
    direction: int        # 1 = long, -1 = short
    pnl: float            # dollar P&L after costs
    pnl_pct: float        # percentage return on position
    bars_held: int
    cost: float           # total transaction costs


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    metrics: dict
    signals_df: pd.DataFrame


def run_backtest(
    strategy: Strategy,
    df: pd.DataFrame,
    initial_capital: float = 100_000,
    cost_model: CostModel | None = None,
    risk_per_trade: float = 0.01,
    stop_loss_pct: float | None = None,
) -> BacktestResult:
    """
    Run a single backtest.

    Args:
        strategy: Strategy instance with generate_signals()
        df: OHLCV DataFrame
        initial_capital: Starting capital
        cost_model: Transaction cost model (default: 15 bps round trip)
        risk_per_trade: Fraction of equity to risk per trade
        stop_loss_pct: Optional fixed stop-loss percentage (e.g., 0.07 = 7%)

    Returns:
        BacktestResult with trades, equity curve, metrics, and signals DataFrame
    """
    if cost_model is None:
        cost_model = CostModel()

    # Generate signals
    signals_df = strategy.generate_signals(df.copy())

    if "signal" not in signals_df.columns:
        raise ValueError("Strategy must add a 'signal' column")

    # State
    equity = initial_capital
    cash = initial_capital
    trades: list[Trade] = []
    equity_values = []
    dates = []

    in_position = False
    entry_price = 0.0
    entry_date = None
    shares = 0
    entry_bar = 0

    close_col = signals_df["Close"]
    signal_col = signals_df["signal"]
    index = signals_df.index

    for i in range(len(signals_df)):
        date = index[i]
        price = float(close_col.iloc[i])
        signal = int(signal_col.iloc[i])

        # Check stop loss
        if in_position and stop_loss_pct is not None:
            if price <= entry_price * (1 - stop_loss_pct):
                # Stop loss triggered — force exit
                signal = -1

        if signal == 1 and not in_position:
            # --- ENTER ---
            # Position sizing: use a stop based on stop_loss_pct or default 5%
            stop_distance = price * (stop_loss_pct if stop_loss_pct else 0.05)
            stop_price = price - stop_distance

            shares = fixed_fractional_size(equity, risk_per_trade, price, stop_price)
            if shares <= 0:
                continue

            adj_price = cost_model.adjusted_entry_price(price, direction=1)
            entry_cost = cost_model.entry_cost(price, shares)

            cash -= shares * adj_price
            entry_price = adj_price
            entry_date = date
            entry_bar = i
            in_position = True

        elif signal == -1 and in_position:
            # --- EXIT ---
            adj_price = cost_model.adjusted_exit_price(price, direction=1)
            exit_cost = cost_model.exit_cost(price, shares)

            position_pnl = shares * (adj_price - entry_price)
            total_cost = cost_model.entry_cost(entry_price, shares) + exit_cost
            net_pnl = position_pnl

            cash += shares * adj_price
            equity = cash  # fully in cash after exit

            trades.append(Trade(
                entry_date=entry_date,
                exit_date=date,
                entry_price=entry_price,
                exit_price=adj_price,
                shares=shares,
                direction=1,
                pnl=net_pnl,
                pnl_pct=net_pnl / (entry_price * shares) if entry_price * shares > 0 else 0,
                bars_held=i - entry_bar,
                cost=total_cost,
            ))

            in_position = False
            shares = 0

        # Mark-to-market
        if in_position:
            mtm = cash + shares * price
        else:
            mtm = cash

        equity = mtm
        equity_values.append(mtm)
        dates.append(date)

    # Close any open position at end
    if in_position:
        price = float(close_col.iloc[-1])
        adj_price = cost_model.adjusted_exit_price(price, direction=1)
        exit_cost = cost_model.exit_cost(price, shares)
        position_pnl = shares * (adj_price - entry_price)
        total_cost = cost_model.entry_cost(entry_price, shares) + exit_cost

        trades.append(Trade(
            entry_date=entry_date,
            exit_date=index[-1],
            entry_price=entry_price,
            exit_price=adj_price,
            shares=shares,
            direction=1,
            pnl=position_pnl,
            pnl_pct=position_pnl / (entry_price * shares) if entry_price * shares > 0 else 0,
            bars_held=len(signals_df) - 1 - entry_bar,
            cost=total_cost,
        ))

    equity_curve = pd.Series(equity_values, index=dates, name="equity")
    metrics = compute_metrics(trades, equity_curve, initial_capital)

    return BacktestResult(
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        signals_df=signals_df,
    )
