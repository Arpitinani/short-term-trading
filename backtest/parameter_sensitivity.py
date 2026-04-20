"""Parameter sensitivity analysis — check for plateaus vs spikes."""

from __future__ import annotations

from itertools import product
from typing import Type

import pandas as pd

from strategies.base import Strategy, StrategyConfig
from .engine import run_backtest
from .costs import CostModel


def parameter_sensitivity(
    strategy_class: Type[Strategy],
    df: pd.DataFrame,
    base_config: StrategyConfig,
    param_grid: dict[str, list],
    initial_capital: float = 100_000,
    cost_model: CostModel | None = None,
    risk_per_trade: float = 0.01,
) -> pd.DataFrame:
    """
    Sweep parameter combinations and record metrics for each.

    Args:
        strategy_class: Strategy class to instantiate
        df: OHLCV DataFrame
        base_config: Base configuration (params will be overridden)
        param_grid: e.g., {"entry_threshold": [2,3,5,7,10], "exit_threshold": [50,65,80]}
        initial_capital: Starting capital
        cost_model: Transaction cost model

    Returns:
        DataFrame with one row per param combo, sorted by sharpe_ratio descending
    """
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    results = []

    for combo in product(*values):
        overrides = dict(zip(keys, combo))
        config = base_config.with_params(**overrides)
        strategy = strategy_class(config)

        result = run_backtest(
            strategy, df,
            initial_capital=initial_capital,
            cost_model=cost_model,
            risk_per_trade=risk_per_trade,
        )

        row = {**overrides, **result.metrics}
        results.append(row)

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("profit_factor", ascending=False)
    return results_df


def assess_stability(results_df: pd.DataFrame, metric: str = "profit_factor") -> dict:
    """
    Assess parameter stability.

    Returns:
        stability_score: fraction of combos that are profitable
        plateau_score: low variance in top half means plateau (good), high means spike (bad)
    """
    profitable = (results_df[metric] > 1.0).mean() if metric == "profit_factor" else (results_df[metric] > 0).mean()

    top_half = results_df.nlargest(max(1, len(results_df) // 2), metric)
    mean_val = top_half[metric].mean()
    std_val = top_half[metric].std()

    plateau_score = 1 - (std_val / (abs(mean_val) + 1e-10)) if mean_val != 0 else 0

    return {
        "stability_score": float(profitable),
        "plateau_score": float(plateau_score),
        "total_combos": len(results_df),
        "profitable_combos": int(profitable * len(results_df)),
        "best_metric": float(results_df[metric].max()),
        "worst_metric": float(results_df[metric].min()),
        "median_metric": float(results_df[metric].median()),
    }
