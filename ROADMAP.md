# Trading System Roadmap

## Architecture Overview

```
Trading Dashboard (Next.js + lightweight-charts)
        │ REST API
Trading Backend (FastAPI + Python)
  ├── Backtest Engine (VectorBT + walk-forward + Monte Carlo)
  ├── Strategy Engine (config-driven, multi-strategy)
  ├── Screener (Minervini Trend Template + custom)
  ├── Regime Detector (weighted macro signals — rebuilt, backtested)
  ├── Risk Manager (position sizing, portfolio heat, daily loss limit)
  ├── Execution (Alpaca paper → live, IBKR later)
  └── Notifications (Slack → email/SMS later)
        │
Shared Data Layer
  ├── Raw data fetching: reused from ~/investing (macro.py, market_data.py, indicators.py)
  ├── Indicator calculations: reused from ~/investing (RSI, MACD, ADX, ATR, BB, OBV)
  ├── Market data: Alpaca free tier + yfinance (daily backtesting)
  └── Regime signals: raw VIX, yields, DXY, breadth, F&G, inflation (reused)
                       scoring/weights/thresholds (rebuilt & backtested)
```

## Key Decisions

- **Data:** Alpaca free tier (intraday) + yfinance (daily backtesting). Polygon.io when going live.
- **Broker:** Alpaca (paper → live). IBKR when scaling up or needing options/shorting.
- **UI:** Next.js + TradingView lightweight-charts (not Streamlit).
- **Backtesting:** VectorBT (fast exploration) → custom walk-forward engine.
- **Regime:** Reuse raw macro data from investing dashboard. Rebuild scoring with weighted model + backtest validation.
- **Derived scores:** Nothing from investing dashboard used blindly. All scoring rebuilt and backtested.

---

## Phase 1: Core Infrastructure (Days 1-4)

### Day 1-2: Environment + Data Pipeline
- [ ] Python environment with all dependencies
- [ ] Data pipeline: download OHLCV from Alpaca/yfinance
- [ ] Extract reusable modules from ~/investing (raw data fetching, indicators, caching)
- [ ] Candlestick chart generation with EMAs + volume (mplfinance)
- [ ] Create Alpaca paper trading account

### Day 3-4: Backtesting Framework + First Strategy
- [ ] Walk-forward optimization engine (rolling window, 3yr train / 6mo test)
- [ ] Parameter sensitivity analysis tool
- [ ] Monte Carlo simulation (trade resampling, 10K sims)
- [ ] First backtest: Connors RSI(2) on SPY (fully mechanical, verified strategy)
  - Entry: RSI(2) < 5, stock above 200 SMA
  - Exit: RSI(2) > 65
  - Validate against Connors' published results (~84% win rate)

## Phase 2: Second Strategy + Regime (Days 5-8)

### Day 5-6: Turtle Trend Following
- [ ] Implement Turtle System 2 (55-day breakout, 20-day exit)
- [ ] ATR-based position sizing (1% equity volatility per unit)
- [ ] 2N stop loss
- [ ] Backtest on SPY/QQQ and sector ETFs
- [ ] Walk-forward validation
- [ ] Compare: RSI(2) + Turtle combined vs each alone (correlation analysis)

### Day 7-8: Regime Detection (Rebuilt)
- [ ] Extract raw macro signals from ~/investing (VIX, yields, DXY, breadth, F&G, Cu/Au)
- [ ] Build weighted regime model (not equal-weight +1/0/-1)
  - Backtest different weights to find what actually predicts forward returns
  - Walk-forward validate the regime model itself
  - Add Hurst exponent (trending vs mean-reverting detection)
- [ ] Regime-to-strategy mapping:
  - Bull trending → Turtle + momentum
  - Choppy → Connors RSI(2) mean reversion
  - Bear/crisis → cash or minimal exposure
- [ ] Validate: do strategies perform better WITH regime filter than without?

## Phase 3: Screening + Risk Management (Days 9-11)

### Day 9: Minervini Trend Template Screener
- [ ] Implement all 8 Trend Template criteria
- [ ] Scan S&P 500 + Russell 1000 for qualifying stocks
- [ ] Rank by relative strength
- [ ] Generate daily watchlist

### Day 10-11: Risk Management Module
- [ ] Position sizing: fixed fractional (1% risk per trade)
- [ ] ATR-based stop calculation
- [ ] Portfolio heat tracking (max 5-6% total open risk)
- [ ] Daily loss limit (3% → stop trading)
- [ ] Fractional Kelly criterion for sizing optimization
- [ ] Re-run all backtests with risk management applied

## Phase 4: Execution + API (Days 12-15)

### Day 12-13: FastAPI Backend
- [ ] API endpoints: strategies, backtests, screener, positions, regime
- [ ] Alpaca integration (orders, positions, account)
- [ ] Bracket orders (entry + stop + target)
- [ ] Paper trading mode

### Day 14-15: Next.js Dashboard
- [ ] TradingView lightweight-charts integration
- [ ] Pages: Dashboard (positions/P&L), Screener, Backtest Results, Trade History
- [ ] Regime indicator display
- [ ] Real-time position updates

## Phase 5: Notifications + Paper Trading (Days 16-18)
- [ ] Slack webhook notifications (signal fired, trade placed, stop hit)
- [ ] End-to-end workflow: scan → signal → size → execute → manage
- [ ] Begin paper trading with validated strategies
- [ ] Track paper results vs backtest expectations

## Phase 6: Automation + Live (Week 4+)
- [ ] Claude Code autonomous trading loop
- [ ] Automated evening scan + morning execution
- [ ] Strategy decay monitoring (rolling Sharpe, regime shifts)
- [ ] Transition to live trading (small size, 25-50% of target)
- [ ] Scale up over 2-3 months if performance matches
- [ ] IBKR integration when ready for options/shorting

---

## Strategy Priority (Verified & Codeable First)

### Tier 1: Fully Mechanical + Verified (Build First)

**1. Connors RSI(2) Mean Reversion**
- Source: Published backtests by Larry Connors (84% win rate on S&P 500 stocks)
- Entry: RSI(2) < 5, stock above 200 SMA
- Exit: RSI(2) > 65
- No stop loss in original (we'll test adding one)
- Hold: 3-6 days avg
- Best regime: Choppy, range-bound markets
- Weakness: No crash protection, individual trades can draw down 20-30%

**2. Turtle System 2 (55-Day Breakout)**
- Source: Curtis Faith "Way of the Turtle", audited CTA records (Jerry Parker ~20-25% annual for decades)
- Entry: Price > 55-day high
- Exit: Price < 20-day low
- Stop: 2 × ATR(20) from entry
- Position size: 1% of equity / ATR(20) = 1 unit
- Pyramiding: Up to 4 units, add every 0.5 ATR
- Best regime: Strong trending markets
- Weakness: 35-40% win rate, 30-50% drawdowns, whipsaw in choppy markets

**3. Academic Momentum (12-1 Month)**
- Source: Jegadeesh & Titman 1993, peer-reviewed, replicated hundreds of times
- Rule: Buy top decile by 12-month return (skip most recent month), hold 3-12 months
- Use as: Stock selection/ranking overlay for other strategies
- Best regime: Bull markets

### Tier 2: Semi-Mechanical + Verified (Build Second)

**4. Minervini Trend Template (Screening Tool)**
- Source: 2x US Investing Championship (audited)
- 8 criteria for stock qualification
- Use as: Universe filter — only trade stocks passing the template
- Entry timing for VCP breakouts requires visual confirmation initially

**5. Post-Earnings Announcement Drift**
- Source: Bernard & Thomas 1989, one of the most robust academic anomalies
- Rule: Buy positive earnings surprises (>1 std dev), hold 60 trading days
- Requires earnings estimates data
- Best regime: Any

**6. Connors Double 7**
- Source: Published backtests by Connors
- Entry: 7-day low close, stock above 200 SMA
- Exit: 7-day high close
- Simple, low-frequency complement to RSI(2)

### Tier 3: Discretionary / Unverified (Evaluate Later)

- VCP breakout entries (pattern recognition needed)
- Gap and Go (Ross Cameron — partially verified)
- Opening Range Breakout (Crabel — academic backing)
- Williams volatility breakout (one audited year, extreme sizing)
- Sector rotation strategies

---

## Validation Pipeline (Every Strategy Must Pass ALL Stages)

```
Stage 1: HYPOTHESIS
  └── Why does this edge exist? Who's on the other side?

Stage 2: DEVELOPMENT (60% of data)
  ├── Code the strategy
  ├── Parameter sensitivity (test ±20% around optimal — must show plateau, not spike)
  └── 100+ trades minimum for statistical significance

Stage 3: WALK-FORWARD VALIDATION (20% of data)
  ├── Rolling 3yr train / 6mo test windows
  ├── Walk-forward efficiency > 0.5 (OOS Sharpe / IS Sharpe)
  └── Stable parameters across windows

Stage 4: MONTE CARLO (on walk-forward results)
  ├── 10,000 trade resampling simulations
  ├── 95th percentile drawdown must be tolerable
  └── Probability of ruin < 5%

Stage 5: HOLDOUT TEST (final 20% of data — ONE shot)
  ├── Run with parameters from validation (NO re-optimization)
  ├── Positive Sharpe + drawdown within Monte Carlo CI
  └── FAIL = reject strategy entirely, no going back

Stage 6: PORTFOLIO INTEGRATION
  ├── Return + drawdown correlation with existing strategies
  ├── Drawdown correlation < 0.3 with any existing strategy
  └── Risk parity capital allocation

Stage 7: PAPER TRADING (1-3 months minimum)
  ├── Actual fills vs backtest assumptions
  └── Strategy-to-backtest correlation > 0.85

Stage 8: LIVE TRADING
  ├── Start at 25-50% of target position size
  ├── Scale up over 2-3 months
  └── Kill switch: rolling 3-month Sharpe < 0 for 2 consecutive months
```

---

## Risk Rules (Non-Negotiable)

- Max 1% account risk per trade
- Max 5-6% total portfolio heat (sum of all open position risks)
- Max 3% daily loss — stop trading for the day
- Never average down on a losing position
- Always have stop loss defined BEFORE entry
- Cut losses at max 7-8%, no exceptions
- Regime filter: reduce exposure in Cautious, go to cash in Risk-Off
- No strategy goes live without passing all 8 validation stages

## Regime-Dependent Position Sizing

| Regime | Max Portfolio Heat | Max Position Size | Strategy Allowed |
|--------|-------------------|-------------------|------------------|
| Risk-On | 6% | 1.5% per trade | All strategies |
| Leaning Bullish | 5% | 1% per trade | All strategies |
| Cautious | 3% | 0.75% per trade | Mean reversion only |
| Risk-Off | 1% | 0.5% per trade | Cash preferred, defensive only |
