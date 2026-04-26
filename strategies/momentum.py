"""
Academic Momentum Factor (12-1 Month).

Source: Jegadeesh & Titman (1993), peer-reviewed, replicated hundreds of times.

Rules:
  - Rank stocks by trailing 12-month return, excluding the most recent month
  - Buy top performers (top quintile/decile)
  - The "skip last month" avoids short-term reversal effect
  - Rebalance monthly

Published results:
  - ~1% per month excess return (12% annualized) over 1965-1989
  - Confirmed across many countries, asset classes, and time periods

Use in our system:
  - As a universe FILTER: only trade stocks with strong momentum
  - Rank the universe, select top N for RSI(2) and Turtle to scan
  - Monthly rebalance of the "eligible" list
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class MomentumRank:
    ticker: str
    return_12m: float       # 12-month return (%)
    return_1m: float        # most recent month return (%)
    momentum_score: float   # 12-1 month return (%)
    rank: int               # 1 = best momentum
    percentile: float       # 0-100, higher = stronger


def compute_momentum_ranks(
    tickers: list[str],
    period: str = "14mo",
) -> list[MomentumRank]:
    """
    Rank stocks by 12-1 month momentum.

    Downloads price data, computes trailing returns, ranks by
    12-month return minus most recent 1-month return.

    Args:
        tickers: List of ticker symbols
        period: Data period (need at least 13 months)

    Returns:
        List of MomentumRank sorted by momentum_score descending
    """
    try:
        data = yf.download(tickers, period=period, progress=False, threads=True)
    except Exception:
        return []

    if data.empty:
        return []

    # Extract close prices
    if isinstance(data.columns, pd.MultiIndex):
        close = data["Close"]
    else:
        close = data

    if isinstance(close, pd.Series):
        close = close.to_frame()

    results = []
    for ticker in tickers:
        if ticker not in close.columns:
            continue

        prices = close[ticker].dropna()
        if len(prices) < 252:  # need ~12 months of daily data
            continue

        current = float(prices.iloc[-1])

        # 12-month return (252 trading days ago)
        price_12m = float(prices.iloc[-252]) if len(prices) >= 252 else float(prices.iloc[0])
        ret_12m = (current / price_12m - 1) * 100

        # 1-month return (21 trading days ago)
        price_1m = float(prices.iloc[-21]) if len(prices) >= 21 else float(prices.iloc[0])
        ret_1m = (current / price_1m - 1) * 100

        # Momentum score = 12-month return minus last month (the "12-1" factor)
        momentum = ret_12m - ret_1m

        results.append(MomentumRank(
            ticker=ticker,
            return_12m=round(ret_12m, 1),
            return_1m=round(ret_1m, 1),
            momentum_score=round(momentum, 1),
            rank=0,
            percentile=0,
        ))

    # Rank by momentum score
    results.sort(key=lambda x: x.momentum_score, reverse=True)
    n = len(results)
    for i, r in enumerate(results):
        r.rank = i + 1
        r.percentile = round((1 - i / max(n - 1, 1)) * 100, 1)

    return results


def get_top_momentum(
    tickers: list[str],
    top_n: int = 10,
    min_percentile: float = 60,
) -> list[str]:
    """
    Get top momentum tickers for use as a universe filter.

    Args:
        tickers: Full universe to rank
        top_n: Maximum number of tickers to return
        min_percentile: Minimum momentum percentile to include

    Returns:
        List of ticker symbols with strongest momentum
    """
    ranks = compute_momentum_ranks(tickers)
    filtered = [r for r in ranks if r.percentile >= min_percentile]
    return [r.ticker for r in filtered[:top_n]]


def format_momentum_table(ranks: list[MomentumRank]) -> str:
    """Pretty-print momentum rankings."""
    lines = [
        f"{'Rank':>4}  {'Ticker':8s}  {'12M Ret':>8}  {'1M Ret':>7}  {'Mom Score':>10}  {'Pctile':>7}",
        "-" * 55,
    ]
    for r in ranks:
        lines.append(
            f"{r.rank:4d}  {r.ticker:8s}  {r.return_12m:+7.1f}%  {r.return_1m:+6.1f}%  {r.momentum_score:+9.1f}%  {r.percentile:6.0f}"
        )
    return "\n".join(lines)
