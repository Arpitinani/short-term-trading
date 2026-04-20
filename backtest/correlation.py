"""Strategy correlation analysis — prove diversification benefit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .engine import BacktestResult


@dataclass
class CorrelationReport:
    return_correlation: float
    drawdown_correlation: float
    diversification_ratio: float
    combined_sharpe: float
    individual_sharpes: dict[str, float]
    combined_max_drawdown: float
    individual_max_drawdowns: dict[str, float]
    combined_total_return: float
    individual_total_returns: dict[str, float]


def analyze_correlation(
    results: dict[str, BacktestResult],
    weights: dict[str, float] | None = None,
) -> CorrelationReport:
    """
    Analyze correlation between multiple strategy equity curves.

    Args:
        results: {"strategy_name": BacktestResult, ...}
        weights: {"strategy_name": weight, ...} — default equal weight

    Returns:
        CorrelationReport with correlation metrics and combined performance
    """
    names = list(results.keys())

    if weights is None:
        weights = {name: 1.0 / len(names) for name in names}

    # Build aligned daily returns from equity curves
    equity_curves = {}
    for name, result in results.items():
        ec = result.equity_curve
        if not ec.empty:
            equity_curves[name] = ec

    if len(equity_curves) < 2:
        raise ValueError("Need at least 2 strategies for correlation analysis")

    # Align to common date range
    eq_df = pd.DataFrame(equity_curves)
    eq_df = eq_df.ffill().bfill()

    # Daily returns
    returns_df = eq_df.pct_change().dropna()

    # --- Return correlation ---
    if len(returns_df.columns) == 2:
        return_corr = float(returns_df.corr().iloc[0, 1])
    else:
        return_corr = float(returns_df.corr().mean().mean())

    # --- Drawdown correlation ---
    dd_series = {}
    for name in names:
        if name in eq_df.columns:
            ec = eq_df[name].dropna()
            running_max = ec.expanding().max()
            dd = (ec - running_max) / running_max
            dd_series[name] = dd

    dd_df = pd.DataFrame(dd_series)
    dd_df = dd_df.dropna()

    if len(dd_df.columns) == 2:
        dd_corr = float(dd_df.corr().iloc[0, 1])
    else:
        dd_corr = float(dd_df.corr().mean().mean())

    # --- Individual metrics ---
    individual_sharpes = {}
    individual_max_dds = {}
    individual_returns = {}

    for name in names:
        if name in returns_df.columns:
            r = returns_df[name].dropna()
            if len(r) > 1 and r.std() > 0:
                individual_sharpes[name] = float(r.mean() / r.std() * np.sqrt(252))
            else:
                individual_sharpes[name] = 0.0

            ec = eq_df[name].dropna()
            if not ec.empty:
                running_max = ec.expanding().max()
                individual_max_dds[name] = float(((ec - running_max) / running_max).min())
                individual_returns[name] = float((ec.iloc[-1] / ec.iloc[0]) - 1)
            else:
                individual_max_dds[name] = 0.0
                individual_returns[name] = 0.0

    # --- Combined portfolio ---
    # Weight the equity curves
    initial = 100_000
    combined_equity = pd.Series(0.0, index=eq_df.index)
    for name in names:
        if name in eq_df.columns:
            w = weights.get(name, 1.0 / len(names))
            # Normalize each equity curve to start at the allocated amount
            ec = eq_df[name].dropna()
            if not ec.empty:
                normalized = ec / ec.iloc[0] * (initial * w)
                combined_equity = combined_equity.add(normalized, fill_value=0)

    combined_equity = combined_equity.dropna()
    combined_equity = combined_equity[combined_equity > 0]

    if len(combined_equity) > 1:
        combined_returns = combined_equity.pct_change().dropna()
        if combined_returns.std() > 0:
            combined_sharpe = float(combined_returns.mean() / combined_returns.std() * np.sqrt(252))
        else:
            combined_sharpe = 0.0

        running_max = combined_equity.expanding().max()
        combined_max_dd = float(((combined_equity - running_max) / running_max).min())
        combined_total_return = float((combined_equity.iloc[-1] / combined_equity.iloc[0]) - 1)
    else:
        combined_sharpe = 0.0
        combined_max_dd = 0.0
        combined_total_return = 0.0

    # --- Diversification ratio ---
    # DR = weighted avg vol / portfolio vol (higher = more diversification benefit)
    vols = {name: returns_df[name].std() for name in names if name in returns_df.columns}
    weighted_avg_vol = sum(weights.get(n, 0) * v for n, v in vols.items())
    if len(combined_equity) > 1:
        portfolio_vol = combined_equity.pct_change().dropna().std()
        div_ratio = weighted_avg_vol / portfolio_vol if portfolio_vol > 0 else 1.0
    else:
        div_ratio = 1.0

    return CorrelationReport(
        return_correlation=return_corr,
        drawdown_correlation=dd_corr,
        diversification_ratio=div_ratio,
        combined_sharpe=combined_sharpe,
        individual_sharpes=individual_sharpes,
        combined_max_drawdown=combined_max_dd,
        individual_max_drawdowns=individual_max_dds,
        combined_total_return=combined_total_return,
        individual_total_returns=individual_returns,
    )


def format_correlation(report: CorrelationReport) -> str:
    """Pretty-print correlation report."""
    lines = [
        "Strategy Correlation Analysis",
        "=" * 55,
        "",
        f"Return Correlation:    {report.return_correlation:.3f}",
        f"Drawdown Correlation:  {report.drawdown_correlation:.3f}",
        f"Diversification Ratio: {report.diversification_ratio:.2f}",
        "",
        "Individual Performance:",
    ]

    for name in report.individual_sharpes:
        lines.append(
            f"  {name:20s}  Sharpe {report.individual_sharpes[name]:6.2f}  "
            f"MaxDD {report.individual_max_drawdowns.get(name, 0):.1%}  "
            f"Return {report.individual_total_returns.get(name, 0):.1%}"
        )

    lines.extend([
        "",
        "Combined Portfolio (equal weight):",
        f"  Sharpe:     {report.combined_sharpe:.2f}",
        f"  Max DD:     {report.combined_max_drawdown:.1%}",
        f"  Return:     {report.combined_total_return:.1%}",
        "",
    ])

    # Assessment
    corr = report.return_correlation
    if corr < 0.3:
        corr_label = "EXCELLENT — nearly uncorrelated"
    elif corr < 0.5:
        corr_label = "GOOD — moderate diversification"
    elif corr < 0.7:
        corr_label = "FAIR — some diversification"
    else:
        corr_label = "POOR — highly correlated, limited benefit"

    dd_corr = report.drawdown_correlation
    if dd_corr < 0.3:
        dd_label = "EXCELLENT — don't blow up together"
    elif dd_corr < 0.5:
        dd_label = "GOOD"
    else:
        dd_label = "WARNING — may draw down together"

    lines.extend([
        f"Assessment:",
        f"  Return correlation:   {corr_label}",
        f"  Drawdown correlation: {dd_label}",
    ])

    if report.combined_sharpe > max(report.individual_sharpes.values()):
        lines.append("  Combined Sharpe BEATS all individual strategies")
    if report.combined_max_drawdown > min(report.individual_max_drawdowns.values()):
        lines.append("  Combined Max DD BETTER than worst individual")

    return "\n".join(lines)
