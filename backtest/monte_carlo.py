"""Monte Carlo simulation for trading system robustness analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .engine import Trade


@dataclass
class MonteCarloResult:
    n_simulations: int
    median_return: float
    return_5th: float
    return_95th: float
    median_max_drawdown: float
    drawdown_5th: float       # best case (shallowest)
    drawdown_95th: float      # worst case (deepest)
    probability_of_ruin: float
    all_returns: np.ndarray
    all_drawdowns: np.ndarray


def monte_carlo_trades(
    trades: list[Trade],
    n_simulations: int = 10_000,
    initial_capital: float = 100_000,
    ruin_threshold: float = -0.50,
    seed: int = 42,
) -> MonteCarloResult:
    """
    Monte Carlo simulation via trade resampling.

    Shuffles the order of trade P&Ls and replays them to see
    the range of possible equity curves from the same trades.

    Args:
        trades: List of Trade objects from a backtest
        n_simulations: Number of random permutations
        initial_capital: Starting capital
        ruin_threshold: Drawdown level that constitutes "ruin" (e.g., -0.50 = -50%)
        seed: Random seed for reproducibility
    """
    if not trades:
        return MonteCarloResult(
            n_simulations=0, median_return=0, return_5th=0, return_95th=0,
            median_max_drawdown=0, drawdown_5th=0, drawdown_95th=0,
            probability_of_ruin=0, all_returns=np.array([]), all_drawdowns=np.array([]),
        )

    rng = np.random.default_rng(seed)

    # Extract trade P&L as percentage of capital at time of trade
    trade_pnl_pcts = np.array([t.pnl_pct for t in trades])
    n_trades = len(trade_pnl_pcts)

    all_returns = np.zeros(n_simulations)
    all_drawdowns = np.zeros(n_simulations)

    for sim in range(n_simulations):
        # Randomly permute trade order
        shuffled = rng.permutation(trade_pnl_pcts)

        # Replay trades
        equity = initial_capital
        peak = equity
        max_dd = 0.0

        for pnl_pct in shuffled:
            # Apply trade P&L (as fraction of position, not total equity)
            # Use fixed position size approximation
            position_value = equity * 0.05  # approximate position size
            trade_pnl = position_value * pnl_pct
            equity += trade_pnl

            if equity > peak:
                peak = equity
            dd = (equity - peak) / peak
            if dd < max_dd:
                max_dd = dd

        all_returns[sim] = (equity / initial_capital) - 1
        all_drawdowns[sim] = max_dd

    return MonteCarloResult(
        n_simulations=n_simulations,
        median_return=float(np.median(all_returns)),
        return_5th=float(np.percentile(all_returns, 5)),
        return_95th=float(np.percentile(all_returns, 95)),
        median_max_drawdown=float(np.median(all_drawdowns)),
        drawdown_5th=float(np.percentile(all_drawdowns, 5)),     # shallowest
        drawdown_95th=float(np.percentile(all_drawdowns, 95)),   # deepest
        probability_of_ruin=float(np.mean(all_drawdowns < ruin_threshold)),
        all_returns=all_returns,
        all_drawdowns=all_drawdowns,
    )


def format_monte_carlo(result: MonteCarloResult) -> str:
    """Pretty-print Monte Carlo results."""
    return "\n".join([
        f"Monte Carlo Simulation ({result.n_simulations:,} runs)",
        f"{'=' * 50}",
        f"Returns:",
        f"  Median:         {result.median_return:.1%}",
        f"  5th percentile: {result.return_5th:.1%}",
        f"  95th percentile:{result.return_95th:.1%}",
        f"",
        f"Max Drawdown:",
        f"  Median:         {result.median_max_drawdown:.1%}",
        f"  5th pctile:     {result.drawdown_5th:.1%} (best case)",
        f"  95th pctile:    {result.drawdown_95th:.1%} (worst case)",
        f"",
        f"P(Ruin):          {result.probability_of_ruin:.2%}",
        f"                  {'PASS' if result.probability_of_ruin < 0.05 else 'FAIL'} (threshold: <5%)",
    ])
