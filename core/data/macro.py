"""
Raw macro data fetching. Extracted from investing dashboard.

Provides factual market data — VIX, yields, DXY, breadth, Fear & Greed, etc.
NO scoring or regime classification here — that's in core/regime/detector.py.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .market_data import fetch_close_cached, get_price_history

# ---------------------------------------------------------------------------
# Ticker map
# ---------------------------------------------------------------------------
MACRO_TICKERS = {
    "vix": "^VIX",
    "vix3m": "^VIX3M",
    "spx": "^GSPC",
    "tnx": "^TNX",       # 10Y yield (%)
    "irx": "^IRX",       # 13-week T-bill (%)
    "dxy": "DX-Y.NYB",   # Dollar index
    "gold": "GC=F",
    "copper": "HG=F",
}

# Cache path — configurable via environment or defaults to project data/
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BREADTH_CACHE = _PROJECT_ROOT / "data" / "breadth_cache.csv"


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_macro_data(
    period: str = "1y",
    ttl: int = 300,
) -> dict[str, pd.Series]:
    """Fetch price history for all macro tickers. Returns {name: close_series}."""
    data = {}
    for name, ticker in MACRO_TICKERS.items():
        try:
            close = fetch_close_cached(ticker, period=period, ttl_seconds=ttl)
            if close is not None and len(close) > 0:
                data[name] = close
        except Exception:
            continue
    return data


def fetch_spx_atr(period: str = "1y", ttl: int = 300, window: int = 20) -> float | None:
    """Compute S&P 500 ATR(window) from OHLC data."""
    df = get_price_history("^GSPC", period=period, ttl_seconds=ttl)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated()]
    if not all(c in df.columns for c in ["High", "Low", "Close"]):
        return None
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low, (high - prev_close).abs(), (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr = tr.rolling(window).mean().iloc[-1]
    return float(atr) if pd.notna(atr) else None


# ---------------------------------------------------------------------------
# Fear & Greed
# ---------------------------------------------------------------------------

def get_fear_greed() -> dict:
    """Fetch CNN Fear & Greed Index. Returns dict with score (0-100), rating, deltas."""
    empty = {
        "score": None, "rating": None, "previous_close": None,
        "previous_1_week": None, "previous_1_month": None, "previous_1_year": None,
    }
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        resp = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://edition.cnn.com/markets/fear-and-greed",
            },
            timeout=10,
        )
        resp.raise_for_status()
        fg = resp.json().get("fear_and_greed", {})
        return {
            "score": round(fg["score"], 1) if fg.get("score") else None,
            "rating": fg.get("rating"),
            "previous_close": round(fg["previous_close"], 1) if fg.get("previous_close") else None,
            "previous_1_week": round(fg["previous_1_week"], 1) if fg.get("previous_1_week") else None,
            "previous_1_month": round(fg["previous_1_month"], 1) if fg.get("previous_1_month") else None,
            "previous_1_year": round(fg["previous_1_year"], 1) if fg.get("previous_1_year") else None,
        }
    except Exception:
        return empty


# ---------------------------------------------------------------------------
# S&P 500 Breadth
# ---------------------------------------------------------------------------

def _get_sp500_tickers() -> list[str]:
    """Fetch S&P 500 constituent tickers from Wikipedia."""
    import io
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
        df = tables[0]
        tickers = df["Symbol"].str.strip().tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception:
        return []


def compute_sp500_breadth() -> pd.Series | None:
    """Compute daily % of S&P 500 stocks above their 200-day SMA. Cached to disk (12h TTL)."""
    cached = _load_breadth_cache()
    if cached is not None:
        return cached
    breadth = _compute_breadth_fresh()
    if breadth is not None:
        _save_breadth_cache(breadth)
    return breadth


def _load_breadth_cache() -> pd.Series | None:
    try:
        if not _BREADTH_CACHE.exists():
            return None
        age = dt.datetime.now().timestamp() - _BREADTH_CACHE.stat().st_mtime
        if age > 12 * 3600:
            return None
        df = pd.read_csv(_BREADTH_CACHE, index_col=0, parse_dates=True)
        s = df.iloc[:, 0]
        return s if not s.empty else None
    except Exception:
        return None


def _save_breadth_cache(breadth: pd.Series) -> None:
    try:
        _BREADTH_CACHE.parent.mkdir(parents=True, exist_ok=True)
        breadth.to_csv(_BREADTH_CACHE, header=["breadth"])
    except Exception:
        pass


def _compute_breadth_fresh() -> pd.Series | None:
    import yfinance as yf
    tickers = _get_sp500_tickers()
    if not tickers:
        return None
    try:
        raw = yf.download(tickers, period="1y", progress=False, threads=True)
    except Exception:
        return None
    if raw.empty:
        return None
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            return None
        close = raw["Close"]
    else:
        close = raw
    if isinstance(close, pd.Series):
        close = close.to_frame()
    sma200 = close.rolling(window=200, min_periods=200).mean()
    above = close > sma200
    valid = sma200.notna().sum(axis=1)
    above_count = above.sum(axis=1)
    breadth = (above_count / valid * 100).round(2)
    breadth = breadth[valid >= 100]
    return breadth if not breadth.empty else None


# ---------------------------------------------------------------------------
# Compute raw indicators (NO scoring — just facts)
# ---------------------------------------------------------------------------

def _safe_last(series: pd.Series) -> float | None:
    if series is None or len(series) == 0:
        return None
    v = float(series.iloc[-1])
    return v if np.isfinite(v) else None


def _safe_prev(series: pd.Series, offset: int = 1) -> float | None:
    if series is None or len(series) <= offset:
        return None
    v = float(series.iloc[-(offset + 1)])
    return v if np.isfinite(v) else None


def _pct_change(series: pd.Series, days: int) -> float | None:
    if series is None or len(series) <= days:
        return None
    now = float(series.iloc[-1])
    then = float(series.iloc[-(days + 1)])
    if then == 0:
        return None
    return round((now / then - 1) * 100, 2)


def compute_indicators(data: dict[str, pd.Series]) -> dict:
    """Compute all macro indicators from raw price data. Returns factual values, no scoring."""
    ind = {}

    # VIX
    if "vix" in data:
        vix = data["vix"]
        vix_val = _safe_last(vix)
        if vix_val is not None and vix_val > 100:
            vix_val = None  # corrupt yfinance data
        ind["vix"] = vix_val
        ind["vix_sma20"] = round(float(vix.tail(20).mean()), 2) if len(vix) >= 20 else None

    # VIX Term Structure
    if "vix" in data and "vix3m" in data:
        vix_val = _safe_last(data["vix"])
        vix3m_val = _safe_last(data["vix3m"])
        ind["vix3m"] = vix3m_val
        if vix_val and vix3m_val and vix3m_val > 0:
            ind["vix_term_ratio"] = round(vix_val / vix3m_val, 3)

    # Yield curve (10Y - 3M)
    if "tnx" in data and "irx" in data:
        tnx_val = _safe_last(data["tnx"])
        irx_val = _safe_last(data["irx"])
        if tnx_val is not None and irx_val is not None:
            ind["yield_curve"] = round(tnx_val - irx_val, 2)

    # DXY
    if "dxy" in data:
        dxy = data["dxy"]
        ind["dxy"] = _safe_last(dxy)
        ind["dxy_sma50"] = round(float(dxy.tail(50).mean()), 2) if len(dxy) >= 50 else None

    # Copper/Gold ratio
    if "copper" in data and "gold" in data:
        cu = _safe_last(data["copper"])
        au = _safe_last(data["gold"])
        if cu and au and au > 0:
            ind["copper_gold"] = round(cu / au * 1000, 2)
            cu_prev = _safe_prev(data["copper"], 22)
            au_prev = _safe_prev(data["gold"], 22)
            if cu_prev and au_prev and au_prev > 0:
                ind["copper_gold_trend"] = 1 if (cu / au) > (cu_prev / au_prev) else -1

    # Breadth
    if "breadth" in data:
        br = data["breadth"]
        ind["breadth"] = _safe_last(br)

    # SPX trend
    if "spx" in data:
        spx = data["spx"]
        ind["spx"] = _safe_last(spx)
        if len(spx) >= 200:
            sma200 = float(spx.tail(200).mean())
            sma50 = float(spx.tail(50).mean())
            ind["spx_sma200"] = round(sma200, 2)
            ind["spx_sma50"] = round(sma50, 2)
            ind["spx_above_200"] = float(spx.iloc[-1]) > sma200
            ind["spx_above_50"] = float(spx.iloc[-1]) > sma50
            ind["spx_golden_cross"] = sma50 > sma200

    # SPX ATR
    spx_atr = fetch_spx_atr()
    if spx_atr is not None:
        ind["spx_atr"] = round(spx_atr, 2)

    return ind
