"""Walk-forward optimization — the industry standard for strategy validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Type

import numpy as np
import pandas as pd

from strategies.base import Strategy, StrategyConfig
from .engine import run_backtest, Trade, BacktestResult
from .costs import CostModel
from .metrics import compute_metrics


@dataclass
class WFWindow:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    best_params: dict = field(default_factory=dict)
    is_sharpe: float = 0.0
    oos_sharpe: float = 0.0
    oos_trades: list[Trade] = field(default_factory=list)
    oos_metrics: dict = field(default_factory=dict)


@dataclass
class WalkForwardResult:
    windows: list[WFWindow]
    combined_oos_trades: list[Trade]
    combined_oos_equity: pd.Series
    combined_oos_metrics: dict
    wfe: float  # walk-forward efficiency: OOS Sharpe / avg IS Sharpe


def walk_forward(
    strategy_class: Type[Strategy],
    df: pd.DataFrame,
    base_config: StrategyConfig,
    param_grid: dict[str, list],
    train_bars: int = 756,       # ~3 years
    test_bars: int = 126,        # ~6 months
    step_bars: int = 126,        # non-overlapping OOS
    warmup_bars: int = 250,      # indicator lookback (e.g., SMA 200 + buffer)
    optimize_metric: str = "profit_factor",
    min_trades: int = 10,
    initial_capital: float = 100_000,
    cost_model: CostModel | None = None,
    risk_per_trade: float = 0.01,
) -> WalkForwardResult:
    """
    Rolling walk-forward optimization.

    For each window:
      1. Optimize params on training data
      2. Test best params on out-of-sample data
      3. Record OOS trades and metrics

    Returns combined OOS results and walk-forward efficiency.
    """
    if cost_model is None:
        cost_model = CostModel()

    # Generate parameter combinations
    param_keys = list(param_grid.keys())
    param_values = list(param_grid.values())
    param_combos = [dict(zip(param_keys, combo)) for combo in product(*param_values)]

    # Generate windows
    windows: list[WFWindow] = []
    n = len(df)
    i = 0

    while i + train_bars + test_bars <= n:
        train_start_idx = i
        train_end_idx = i + train_bars
        test_start_idx = train_end_idx
        test_end_idx = min(test_start_idx + test_bars, n)

        windows.append(WFWindow(
            train_start=df.index[train_start_idx],
            train_end=df.index[train_end_idx - 1],
            test_start=df.index[test_start_idx],
            test_end=df.index[test_end_idx - 1],
        ))
        i += step_bars

    if not windows:
        return WalkForwardResult(
            windows=[], combined_oos_trades=[], combined_oos_equity=pd.Series(dtype=float),
            combined_oos_metrics={}, wfe=0.0,
        )

    # Run walk-forward
    all_oos_trades: list[Trade] = []

    for window in windows:
        train_df = df[window.train_start:window.train_end]

        # Include warmup data before test period so indicators can calculate
        test_start_idx = df.index.get_loc(window.test_start)
        warmup_start_idx = max(0, test_start_idx - warmup_bars)
        test_end_idx = df.index.get_loc(window.test_end)
        test_df_with_warmup = df.iloc[warmup_start_idx:test_end_idx + 1]

        # --- Optimize on training data ---
        best_metric_val = -np.inf
        best_params = param_combos[0] if param_combos else {}
        best_is_sharpe = 0.0

        for params in param_combos:
            config = base_config.with_params(**params)
            strategy = strategy_class(config)

            result = run_backtest(
                strategy, train_df,
                initial_capital=initial_capital,
                cost_model=cost_model,
                risk_per_trade=risk_per_trade,
            )

            if result.metrics["total_trades"] < min_trades:
                continue

            metric_val = result.metrics.get(optimize_metric, 0)
            if metric_val > best_metric_val:
                best_metric_val = metric_val
                best_params = params
                best_is_sharpe = result.metrics.get("sharpe_ratio", 0)

        # --- Test on OOS data (with warmup for indicators) ---
        config = base_config.with_params(**best_params)
        strategy = strategy_class(config)

        oos_result = run_backtest(
            strategy, test_df_with_warmup,
            initial_capital=initial_capital,
            cost_model=cost_model,
            risk_per_trade=risk_per_trade,
        )

        # Filter to only trades that entered during the actual test window
        oos_trades = [
            t for t in oos_result.trades
            if t.entry_date >= window.test_start
        ]

        # Recompute metrics for filtered trades
        if oos_trades:
            oos_equity = _build_equity_from_trades(oos_trades, initial_capital)
            oos_metrics = compute_metrics(oos_trades, oos_equity, initial_capital)
        else:
            oos_equity = pd.Series(dtype=float)
            oos_metrics = {}

        window.best_params = best_params
        window.is_sharpe = best_is_sharpe
        window.oos_sharpe = oos_metrics.get("sharpe_ratio", 0)
        window.oos_trades = oos_trades
        window.oos_metrics = oos_metrics

        all_oos_trades.extend(oos_result.trades)

    # --- Build combined OOS equity curve ---
    combined_equity = _build_equity_from_trades(all_oos_trades, initial_capital)
    combined_metrics = compute_metrics(all_oos_trades, combined_equity, initial_capital)

    # Walk-forward efficiency
    is_sharpes = [w.is_sharpe for w in windows if w.is_sharpe != 0]
    avg_is_sharpe = np.mean(is_sharpes) if is_sharpes else 0
    oos_sharpe = combined_metrics.get("sharpe_ratio", 0)
    wfe = oos_sharpe / avg_is_sharpe if avg_is_sharpe != 0 else 0

    return WalkForwardResult(
        windows=windows,
        combined_oos_trades=all_oos_trades,
        combined_oos_equity=combined_equity,
        combined_oos_metrics=combined_metrics,
        wfe=wfe,
    )


def _build_equity_from_trades(trades: list[Trade], initial_capital: float) -> pd.Series:
    """Build an equity curve from a list of trades."""
    if not trades:
        return pd.Series(dtype=float)

    equity = initial_capital
    points = [(trades[0].entry_date, equity)]

    for trade in trades:
        equity += trade.pnl
        points.append((trade.exit_date, equity))

    dates, values = zip(*points)
    return pd.Series(values, index=dates, name="equity")


def format_walk_forward(result: WalkForwardResult) -> str:
    """Pretty-print walk-forward results."""
    lines = [
        f"Walk-Forward Optimization Results",
        f"{'=' * 50}",
        f"Windows:          {len(result.windows)}",
        f"Total OOS Trades: {len(result.combined_oos_trades)}",
        f"WFE:              {result.wfe:.2f} ({'ROBUST' if result.wfe > 0.5 else 'CAUTION' if result.wfe > 0.3 else 'OVERFIT'})",
        f"",
        f"Combined OOS Metrics:",
    ]

    m = result.combined_oos_metrics
    if m:
        lines.extend([
            f"  Win Rate:       {m.get('win_rate', 0):.1%}",
            f"  Profit Factor:  {m.get('profit_factor', 0):.2f}",
            f"  Avg Trade:      {m.get('avg_trade_pct', 0):.2%}",
            f"  Total Return:   {m.get('total_return', 0):.1%}",
        ])

    lines.append(f"\nPer-Window Breakdown:")
    for i, w in enumerate(result.windows):
        lines.append(
            f"  W{i+1}: Train {w.train_start.date()}-{w.train_end.date()} | "
            f"Test {w.test_start.date()}-{w.test_end.date()} | "
            f"IS Sharpe {w.is_sharpe:.2f} | OOS Sharpe {w.oos_sharpe:.2f} | "
            f"Params {w.best_params} | Trades {len(w.oos_trades)}"
        )

    return "\n".join(lines)
