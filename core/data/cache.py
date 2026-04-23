"""TTL-based parquet caching for market data."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class CacheResult:
    df: pd.DataFrame
    hit: bool
    age_seconds: Optional[int]


def _now_ts() -> int:
    return int(time.time())


def _file_age_seconds(path: Path) -> Optional[int]:
    try:
        return _now_ts() - int(path.stat().st_mtime)
    except Exception:
        return None


def read_parquet_if_fresh(path: Path, ttl_seconds: int) -> Optional[CacheResult]:
    """Return CacheResult if file exists and is newer than TTL; otherwise None."""
    if not path.exists():
        return None

    age = _file_age_seconds(path)
    if age is None or age > ttl_seconds:
        return None

    try:
        df = pd.read_parquet(path)
        return CacheResult(df=df, hit=True, age_seconds=age)
    except Exception:
        return None


def write_parquet(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=True)


def cache_path_prices(project_root: Path, ticker: str, period: str) -> Path:
    safe_ticker = ticker.replace("^", "IDX_").replace("/", "_")
    safe_period = period.replace(" ", "")
    return project_root / "data" / "cache" / "prices" / f"{safe_ticker}__{safe_period}.parquet"
