"""
FastAPI backend for the trading system.

Exposes all core functionality via REST endpoints:
- Regime detection
- Stock screening
- Strategy backtesting
- Trade execution
- Position management

Run: uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Short-Term Trading System",
    description="Systematic trading API — regime detection, screening, backtesting, execution",
    version="0.1.0",
)

# Allow Next.js frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Lazy-loaded singletons (avoid slow imports at startup)
# -------------------------------------------------------------------
_orchestrator = None
_regime_detector = None


def _get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from execution.orchestrator import Orchestrator
        # Use paper mode if Alpaca keys are configured, otherwise dry_run
        broker_mode = "paper" if os.environ.get("ALPACA_API_KEY") else "dry_run"
        _orchestrator = Orchestrator(broker_mode=broker_mode)
    return _orchestrator


def _get_regime_detector():
    global _regime_detector
    if _regime_detector is None:
        from core.regime.detector import RegimeDetector
        _regime_detector = RegimeDetector()
    return _regime_detector


# -------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------

class RegimeResponse(BaseModel):
    regime: str
    score: float
    max_position_pct: float
    max_heat_pct: float
    allowed_strategies: list[str]
    signals: dict[str, float]
    timestamp: str


class ScanResult(BaseModel):
    timestamp: str
    regime: str
    regime_score: float
    signals_count: int
    orders_placed: int
    orders_skipped: int
    positions_closed: int
    summary: str


class ScreenerResult(BaseModel):
    ticker: str
    passes: bool
    criteria_met: int
    price: float
    rs_rank: float | None
    pct_above_52w_low: float
    pct_below_52w_high: float


class BacktestRequest(BaseModel):
    strategy: str = "connors_rsi2"
    ticker: str = "SPY"
    period: str = "max"
    params: dict = {}


class BacktestResponse(BaseModel):
    strategy: str
    ticker: str
    metrics: dict
    trade_count: int


class TradeRequest(BaseModel):
    ticker: str
    qty: int
    side: str = "buy"
    order_type: str = "market"
    stop_loss: float | None = None
    take_profit: float | None = None


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "name": "Short-Term Trading System",
        "version": "0.1.0",
        "status": "running",
        "endpoints": [
            "/regime", "/scan", "/screener", "/backtest",
            "/positions", "/account", "/trade",
        ],
    }


@app.get("/regime", response_model=RegimeResponse)
async def get_regime():
    """Get current market regime."""
    from core.data.market_data import fetch_close_cached
    from core.data.macro import get_fear_greed

    detector = _get_regime_detector()

    spx = fetch_close_cached("^GSPC", period="1y")
    vix = fetch_close_cached("^VIX", period="1y")
    tnx = fetch_close_cached("^TNX", period="1y")
    irx = fetch_close_cached("^IRX", period="1y")
    fg = get_fear_greed()

    data = {"spx": spx, "vix": vix, "tnx": tnx, "irx": irx}
    if fg.get("score") is not None:
        data["fear_greed_score"] = fg["score"]

    state = detector.detect(data)

    return RegimeResponse(
        regime=state.regime.value,
        score=state.score,
        max_position_pct=state.max_position_pct,
        max_heat_pct=state.max_heat_pct,
        allowed_strategies=state.allowed_strategies,
        signals=state.signals,
        timestamp=datetime.now().isoformat(),
    )


@app.get("/ohlcv")
async def get_ohlcv(
    ticker: str = Query(default="SPY"),
    period: str = Query(default="1y"),
):
    """Get OHLCV data for charting."""
    from core.data.market_data import get_price_history
    from core.indicators import calculate_rsi, calculate_sma

    df = get_price_history(ticker, period)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")

    close = df["Close"]
    ema9 = close.ewm(span=9, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    sma200 = close.rolling(200).mean()

    records = []
    for i in range(len(df)):
        idx = df.index[i]
        time_val = int(idx.timestamp()) if hasattr(idx, 'timestamp') else 0
        records.append({
            "time": time_val,
            "open": round(float(df["Open"].iloc[i]), 2),
            "high": round(float(df["High"].iloc[i]), 2),
            "low": round(float(df["Low"].iloc[i]), 2),
            "close": round(float(df["Close"].iloc[i]), 2),
            "volume": int(df["Volume"].iloc[i]) if "Volume" in df.columns else 0,
            "ema9": round(float(ema9.iloc[i]), 2) if not pd.isna(ema9.iloc[i]) else None,
            "ema21": round(float(ema21.iloc[i]), 2) if not pd.isna(ema21.iloc[i]) else None,
            "sma200": round(float(sma200.iloc[i]), 2) if not pd.isna(sma200.iloc[i]) else None,
        })

    return {"ticker": ticker, "period": period, "data": records}


@app.get("/signals")
async def get_signals():
    """Scan universe for current trading signals (no execution)."""
    orch = _get_orchestrator()
    signals = orch.scan_signals_only()

    return [
        {
            "ticker": s.ticker,
            "strategy": s.strategy,
            "action": s.action,
            "entry_price": round(s.entry_price, 2),
            "stop_price": round(s.stop_price, 2),
            "target_price": round(s.target_price, 2) if s.target_price else None,
            "risk_pct": round(abs(s.entry_price - s.stop_price) / s.entry_price * 100, 1),
            "reward_risk": round(abs(s.target_price - s.entry_price) / abs(s.entry_price - s.stop_price), 1) if s.target_price else None,
            "reason": s.reason,
        }
        for s in signals
    ]


@app.get("/scan", response_model=ScanResult)
async def run_scan():
    """Run full trading scan: regime → signals → risk check → execute (dry run)."""
    orch = _get_orchestrator()
    result = orch.run_scan()

    return ScanResult(
        timestamp=result.timestamp,
        regime=result.regime.regime.value,
        regime_score=result.regime.score,
        signals_count=len(result.signals),
        orders_placed=len(result.orders_placed),
        orders_skipped=len(result.orders_skipped),
        positions_closed=len(result.positions_closed),
        summary=result.summary,
    )


@app.get("/screener", response_model=list[ScreenerResult])
async def run_screener(
    min_criteria: int = Query(default=7, ge=1, le=8, description="Minimum criteria to pass (1-8)"),
    universe: str = Query(default="top20", description="'top20' or 'sp500'"),
):
    """Run Minervini Trend Template screener."""
    from screener.trend_template import scan_universe

    if universe == "sp500":
        from screener.trend_template import get_sp500_tickers
        tickers = get_sp500_tickers()
    else:
        tickers = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "UNH",
            "XOM", "LLY", "AVGO", "COST", "HD", "PG", "MRK", "ABBV", "CRM", "NFLX",
        ]

    results = scan_universe(tickers, period="2y", min_criteria=min_criteria)

    if results.empty:
        return []

    return [
        ScreenerResult(
            ticker=row["ticker"],
            passes=row["passes"],
            criteria_met=row["criteria_met"],
            price=row["price"],
            rs_rank=row.get("rs_rank"),
            pct_above_52w_low=row["pct_above_52w_low"],
            pct_below_52w_high=row["pct_below_52w_high"],
        )
        for _, row in results.iterrows()
    ]


@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest_endpoint(request: BacktestRequest):
    """Run a backtest for a strategy."""
    from core.data.market_data import get_price_history
    from strategies.base import StrategyConfig
    from backtest.engine import run_backtest

    df = get_price_history(request.ticker, request.period)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {request.ticker}")

    config = StrategyConfig(
        name=request.strategy,
        params=request.params or {},
    )

    if request.strategy == "connors_rsi2":
        from strategies.connors_rsi2 import ConnorsRSI2
        if not config.params:
            config = config.with_params(rsi_period=2, sma_period=200, entry_threshold=5, exit_threshold=65)
        strategy = ConnorsRSI2(config)
    elif request.strategy == "turtle_system2":
        from strategies.turtle_system2 import TurtleSystem2
        if not config.params:
            config = config.with_params(entry_period=55, exit_period=20, atr_period=20, atr_stop_mult=2.0, long_only=True)
        strategy = TurtleSystem2(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown strategy: {request.strategy}")

    result = run_backtest(strategy, df)

    return BacktestResponse(
        strategy=request.strategy,
        ticker=request.ticker,
        metrics=result.metrics,
        trade_count=result.metrics["total_trades"],
    )


@app.get("/positions")
async def get_positions():
    """Get current open positions."""
    orch = _get_orchestrator()
    positions = orch.broker.get_positions()
    return [
        {
            "ticker": p.ticker,
            "qty": p.qty,
            "side": p.side,
            "entry_price": p.entry_price,
            "current_price": p.current_price,
            "unrealized_pnl": p.unrealized_pnl,
            "unrealized_pnl_pct": p.unrealized_pnl_pct,
        }
        for p in positions
    ]


@app.get("/account")
async def get_account():
    """Get account info."""
    orch = _get_orchestrator()
    acct = orch.broker.get_account()
    return {
        "equity": acct.equity,
        "cash": acct.cash,
        "buying_power": acct.buying_power,
        "portfolio_value": acct.portfolio_value,
        "is_paper": acct.is_paper,
    }


@app.get("/status")
async def get_status():
    """Get full system status."""
    orch = _get_orchestrator()
    return {
        "broker": orch.broker.status_summary(),
        "risk": orch.risk_manager.status(),
        "timestamp": datetime.now().isoformat(),
    }
