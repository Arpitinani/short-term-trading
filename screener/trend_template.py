"""
Minervini Trend Template Screener.

Source: Mark Minervini, 2x US Investing Championship winner (audited).
From "Trade Like a Stock Market Wizard" (2013).

All 8 criteria must be met for a stock to qualify:
  1. Price > 150-day MA AND 200-day MA
  2. 150-day MA > 200-day MA
  3. 200-day MA trending up for at least 1 month (~22 trading days)
  4. 50-day MA > 150-day MA AND 200-day MA
  5. Price > 50-day MA
  6. Price at least 25% above 52-week low
  7. Price within 25% of 52-week high
  8. Relative Strength ranking >= 70 (percentile vs universe)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class TrendTemplateResult:
    ticker: str
    passes: bool
    criteria_met: int       # out of 8
    criteria_detail: dict   # {criterion_name: bool}
    price: float
    sma50: float
    sma150: float
    sma200: float
    pct_above_52w_low: float
    pct_below_52w_high: float
    rs_rank: float | None   # percentile rank (0-100)


def check_trend_template(
    close: pd.Series,
    high: pd.Series | None = None,
    low: pd.Series | None = None,
    rs_rank: float | None = None,
    min_above_52w_low: float = 0.25,
    max_below_52w_high: float = 0.25,
    min_rs_rank: float = 70,
) -> TrendTemplateResult:
    """
    Check if a stock passes Minervini's Trend Template.

    Args:
        close: Daily close prices (need at least 252 days)
        high: Daily highs (for 52-week range). Falls back to close if None.
        low: Daily lows (for 52-week range). Falls back to close if None.
        rs_rank: Relative strength percentile rank (0-100). If None, criterion 8 is skipped.
    """
    if len(close) < 252:
        return TrendTemplateResult(
            ticker="", passes=False, criteria_met=0, criteria_detail={},
            price=0, sma50=0, sma150=0, sma200=0,
            pct_above_52w_low=0, pct_below_52w_high=0, rs_rank=None,
        )

    price = float(close.iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    sma150 = float(close.rolling(150).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])

    # 200 SMA 22 trading days ago
    sma200_1m_ago = float(close.rolling(200).mean().iloc[-22]) if len(close) >= 222 else sma200

    # 52-week high/low
    if high is not None and len(high) >= 252:
        high_52w = float(high.iloc[-252:].max())
    else:
        high_52w = float(close.iloc[-252:].max())

    if low is not None and len(low) >= 252:
        low_52w = float(low.iloc[-252:].min())
    else:
        low_52w = float(close.iloc[-252:].min())

    pct_above_low = (price / low_52w - 1) if low_52w > 0 else 0
    pct_below_high = (1 - price / high_52w) if high_52w > 0 else 1

    criteria = {}

    # 1. Price > 150-day MA AND 200-day MA
    criteria["price_above_150_200"] = price > sma150 and price > sma200

    # 2. 150-day MA > 200-day MA
    criteria["sma150_above_sma200"] = sma150 > sma200

    # 3. 200-day MA trending up (current > 1 month ago)
    criteria["sma200_rising"] = sma200 > sma200_1m_ago

    # 4. 50-day MA > 150-day MA AND 200-day MA
    criteria["sma50_above_150_200"] = sma50 > sma150 and sma50 > sma200

    # 5. Price > 50-day MA
    criteria["price_above_50"] = price > sma50

    # 6. Price at least 25% above 52-week low
    criteria["above_52w_low"] = pct_above_low >= min_above_52w_low

    # 7. Price within 25% of 52-week high
    criteria["near_52w_high"] = pct_below_high <= max_below_52w_high

    # 8. RS rank >= 70
    if rs_rank is not None:
        criteria["rs_rank"] = rs_rank >= min_rs_rank
    else:
        criteria["rs_rank"] = True  # skip if not provided

    passes = all(criteria.values())
    criteria_met = sum(criteria.values())

    return TrendTemplateResult(
        ticker="",
        passes=passes,
        criteria_met=criteria_met,
        criteria_detail=criteria,
        price=price,
        sma50=round(sma50, 2),
        sma150=round(sma150, 2),
        sma200=round(sma200, 2),
        pct_above_52w_low=round(pct_above_low * 100, 1),
        pct_below_52w_high=round(pct_below_high * 100, 1),
        rs_rank=rs_rank,
    )


def scan_universe(
    tickers: list[str],
    period: str = "2y",
    benchmark: str = "SPY",
    min_criteria: int = 8,
) -> pd.DataFrame:
    """
    Scan a universe of stocks against the Trend Template.

    Args:
        tickers: List of ticker symbols
        period: Data period for yfinance
        benchmark: Benchmark for relative strength calculation
        min_criteria: Minimum criteria to include (8 = strict, 6 = relaxed)

    Returns:
        DataFrame of qualifying stocks, sorted by RS rank descending
    """
    # Download all tickers + benchmark
    all_tickers = list(set(tickers + [benchmark]))

    try:
        data = yf.download(all_tickers, period=period, progress=False, threads=True)
    except Exception:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    # Extract close prices
    if isinstance(data.columns, pd.MultiIndex):
        close_all = data["Close"]
        high_all = data.get("High")
        low_all = data.get("Low")
    else:
        close_all = data[["Close"]]
        high_all = data.get("High")
        low_all = data.get("Low")

    if isinstance(close_all, pd.Series):
        close_all = close_all.to_frame()

    # Compute 12-month relative strength for each stock
    rs_scores = {}
    if benchmark in close_all.columns:
        bench_ret = close_all[benchmark].pct_change(252).iloc[-1] if len(close_all) >= 253 else 0

        for ticker in tickers:
            if ticker in close_all.columns and ticker != benchmark:
                stock_ret = close_all[ticker].pct_change(252).iloc[-1] if len(close_all[ticker].dropna()) >= 253 else None
                if stock_ret is not None and np.isfinite(stock_ret):
                    rs_scores[ticker] = stock_ret

    # Rank RS scores as percentiles
    if rs_scores:
        values = list(rs_scores.values())
        for ticker in rs_scores:
            rank = sum(1 for v in values if v <= rs_scores[ticker]) / len(values) * 100
            rs_scores[ticker] = round(rank, 1)

    # Check each stock
    results = []
    for ticker in tickers:
        if ticker == benchmark or ticker not in close_all.columns:
            continue

        close = close_all[ticker].dropna()
        if len(close) < 252:
            continue

        high = high_all[ticker].dropna() if high_all is not None and ticker in high_all.columns else None
        low = low_all[ticker].dropna() if low_all is not None and ticker in low_all.columns else None
        rs = rs_scores.get(ticker)

        result = check_trend_template(close, high=high, low=low, rs_rank=rs)
        result.ticker = ticker

        if result.criteria_met >= min_criteria:
            results.append({
                "ticker": ticker,
                "passes": result.passes,
                "criteria_met": result.criteria_met,
                "price": round(result.price, 2),
                "sma50": result.sma50,
                "sma150": result.sma150,
                "sma200": result.sma200,
                "pct_above_52w_low": result.pct_above_52w_low,
                "pct_below_52w_high": result.pct_below_52w_high,
                "rs_rank": result.rs_rank,
                **{f"c_{k}": v for k, v in result.criteria_detail.items()},
            })

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("rs_rank", ascending=False, na_position="last")
    return df


def get_sp500_tickers() -> list[str]:
    """Fetch S&P 500 tickers from Wikipedia."""
    import io
    try:
        resp = pd.read_html(
            io.StringIO(
                __import__("requests").get(
                    "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=15,
                ).text
            )
        )
        tickers = resp[0]["Symbol"].str.strip().tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception:
        return []
