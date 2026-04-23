"""Market data fetching with parquet caching. Adapted from investing dashboard."""

import pandas as pd
import yfinance as yf
from pathlib import Path

from .cache import read_parquet_if_fresh, write_parquet, cache_path_prices


# Project root: short-term-trading/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def fetch_close(symbol: str, period: str = "6mo") -> pd.Series:
    """Fetch close prices directly from yfinance (no caching)."""
    df = yf.download(symbol, period=period, progress=False)
    close_obj = df["Close"]
    close = close_obj.iloc[:, 0] if isinstance(close_obj, pd.DataFrame) else close_obj
    return close.dropna()


def pct_change_over_days(series: pd.Series, days: int) -> float:
    if len(series) <= days:
        return float("nan")
    return (series.iloc[-1] / series.iloc[-(days + 1)] - 1) * 100


def get_price_history(
    ticker: str,
    period: str = "6mo",
    ttl_seconds: int = 24 * 60 * 60,
    project_root: Path | None = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV history with parquet caching.
    Returns empty DataFrame on failure (never raises).
    """
    if project_root is None:
        project_root = _PROJECT_ROOT

    cache_file = cache_path_prices(project_root, ticker, period)

    cached = read_parquet_if_fresh(cache_file, ttl_seconds=ttl_seconds)
    if cached is not None:
        cdf = cached.df
        if isinstance(cdf.columns, pd.MultiIndex):
            cdf.columns = cdf.columns.get_level_values(0)
            cdf = cdf.loc[:, ~cdf.columns.duplicated()]
        return cdf

    try:
        df = yf.download(ticker, period=period, progress=False)
        if df is None:
            df = pd.DataFrame()
    except Exception:
        df = pd.DataFrame()

    # yfinance may return MultiIndex columns — flatten
    if not df.empty and isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        df = df.loc[:, ~df.columns.duplicated()]

    if not df.empty:
        write_parquet(cache_file, df)

    return df


def fetch_close_cached(
    symbol: str,
    period: str = "6mo",
    ttl_seconds: int = 24 * 60 * 60,
) -> pd.Series:
    """Fetch close prices with caching."""
    df = get_price_history(symbol, period=period, ttl_seconds=ttl_seconds)
    if df is None or df.empty or "Close" not in df.columns:
        return pd.Series(dtype=float)

    close_obj = df["Close"]
    close = close_obj.iloc[:, 0] if isinstance(close_obj, pd.DataFrame) else close_obj
    return close.dropna()
