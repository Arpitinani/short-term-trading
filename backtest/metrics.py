"""Backtest performance metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import Trade


def compute_metrics(
    trades: list[Trade],
    equity_curve: pd.Series,
    initial_capital: float = 100_000,
    risk_free_rate: float = 0.04,
) -> dict:
    """Compute all standard backtest performance metrics."""
    metrics = {}

    # --- Trade-level metrics ---
    if not trades:
        return _empty_metrics()

    pnls = np.array([t.pnl for t in trades])
    pnl_pcts = np.array([t.pnl_pct for t in trades])
    bars_held = np.array([t.bars_held for t in trades])
    costs = np.array([t.cost for t in trades])

    winners = pnls[pnls > 0]
    losers = pnls[pnls < 0]

    metrics["total_trades"] = len(trades)
    metrics["win_rate"] = len(winners) / len(trades) if trades else 0
    metrics["avg_win_pct"] = float(np.mean(pnl_pcts[pnl_pcts > 0])) if len(winners) > 0 else 0
    metrics["avg_loss_pct"] = float(np.mean(pnl_pcts[pnl_pcts < 0])) if len(losers) > 0 else 0
    metrics["avg_trade_pct"] = float(np.mean(pnl_pcts))
    metrics["avg_bars_held"] = float(np.mean(bars_held))
    metrics["total_costs"] = float(np.sum(costs))

    # Profit factor
    gross_profit = float(np.sum(winners)) if len(winners) > 0 else 0
    gross_loss = float(abs(np.sum(losers))) if len(losers) > 0 else 0
    metrics["profit_factor"] = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Expectancy (avg $ per trade)
    metrics["expectancy"] = float(np.mean(pnls))

    # --- Equity curve metrics ---
    if equity_curve.empty:
        metrics.update(_empty_equity_metrics())
        return metrics

    total_return = (equity_curve.iloc[-1] / initial_capital) - 1
    metrics["total_return"] = total_return

    # Annualized return
    trading_days = len(equity_curve)
    years = trading_days / 252
    if years > 0 and total_return > -1:
        metrics["annual_return"] = (1 + total_return) ** (1 / years) - 1
    else:
        metrics["annual_return"] = -1.0

    # Daily returns for Sharpe/Sortino
    daily_returns = equity_curve.pct_change().dropna()

    if len(daily_returns) > 1 and daily_returns.std() > 0:
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
        excess = daily_returns - daily_rf
        metrics["sharpe_ratio"] = float(excess.mean() / excess.std() * np.sqrt(252))

        downside = daily_returns[daily_returns < 0]
        if len(downside) > 0 and downside.std() > 0:
            metrics["sortino_ratio"] = float(excess.mean() / downside.std() * np.sqrt(252))
        else:
            metrics["sortino_ratio"] = float("inf")
    else:
        metrics["sharpe_ratio"] = 0.0
        metrics["sortino_ratio"] = 0.0

    # Max drawdown
    running_max = equity_curve.expanding().max()
    drawdowns = (equity_curve - running_max) / running_max
    metrics["max_drawdown"] = float(drawdowns.min())

    # Max drawdown duration (in trading days)
    in_drawdown = equity_curve < running_max
    if in_drawdown.any():
        dd_groups = (~in_drawdown).cumsum()
        dd_durations = in_drawdown.groupby(dd_groups).sum()
        metrics["max_drawdown_duration"] = int(dd_durations.max())
    else:
        metrics["max_drawdown_duration"] = 0

    return metrics


def _empty_metrics() -> dict:
    return {
        "total_trades": 0, "win_rate": 0, "avg_win_pct": 0, "avg_loss_pct": 0,
        "avg_trade_pct": 0, "avg_bars_held": 0, "total_costs": 0,
        "profit_factor": 0, "expectancy": 0,
        **_empty_equity_metrics(),
    }


def _empty_equity_metrics() -> dict:
    return {
        "total_return": 0, "annual_return": 0, "sharpe_ratio": 0,
        "sortino_ratio": 0, "max_drawdown": 0, "max_drawdown_duration": 0,
    }


def format_metrics(metrics: dict) -> str:
    """Pretty-print metrics."""
    lines = [
        f"Total Trades:       {metrics['total_trades']}",
        f"Win Rate:           {metrics['win_rate']:.1%}",
        f"Avg Win:            {metrics['avg_win_pct']:.2%}",
        f"Avg Loss:           {metrics['avg_loss_pct']:.2%}",
        f"Avg Trade:          {metrics['avg_trade_pct']:.2%}",
        f"Avg Bars Held:      {metrics['avg_bars_held']:.1f}",
        f"Profit Factor:      {metrics['profit_factor']:.2f}",
        f"Expectancy:         ${metrics['expectancy']:.2f}",
        f"Total Return:       {metrics['total_return']:.1%}",
        f"Annual Return:      {metrics['annual_return']:.1%}",
        f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}",
        f"Sortino Ratio:      {metrics['sortino_ratio']:.2f}",
        f"Max Drawdown:       {metrics['max_drawdown']:.1%}",
        f"Max DD Duration:    {metrics['max_drawdown_duration']} days",
        f"Total Costs:        ${metrics['total_costs']:.2f}",
    ]
    return "\n".join(lines)
