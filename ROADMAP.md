# Trading System Roadmap

## Phase 1: Foundation & First Strategy (Days 1-4)

### Day 1-2: Core Concepts + Environment Setup
- [ ] Set up Python environment with key libraries
- [ ] Write data download scripts (yfinance)
- [ ] Plot candlestick charts with EMAs and volume
- [ ] Create Alpaca paper trading account

### Day 3-4: First Backtest — EMA Crossover
- [ ] Backtest 9/21 EMA crossover on SPY using VectorBT
- [ ] Track: win rate, profit factor, max drawdown, Sharpe ratio
- [ ] Add 200 SMA regime filter and compare results
- [ ] Parameter sensitivity analysis (learn about overfitting)

## Phase 2: Breakout Strategy + Screening (Days 5-7)

### Day 5-6: Minervini Trend Template Screener
- [ ] Build screener for Minervini's 8-criteria Trend Template
- [ ] Scan S&P 500 and generate daily watchlist

### Day 7: Breakout Backtest
- [ ] Backtest breakout strategy (20-day high break on volume)
- [ ] Set up TradingView charts for visual pattern recognition

## Phase 3: Risk Management (Days 8-9)
- [ ] Position sizing module (fixed fractional, 1% risk per trade)
- [ ] Risk manager (max portfolio heat, max daily loss)
- [ ] Re-run backtests with proper position sizing

## Phase 4: Execution Infrastructure (Days 10-13)
- [ ] Alpaca API integration (orders, positions, account info)
- [ ] Bracket orders (entry + stop loss + take profit)
- [ ] End-to-end workflow: screen → alert → execute → manage
- [ ] Begin paper trading

## Phase 5: Automation & Live Trading (Week 3+)
- [ ] Automated screening runs (evening scan, morning check)
- [ ] TradingView webhook → Python server → Alpaca execution
- [ ] Automated trade management (trailing stops, partial profits)
- [ ] Transition from paper to live trading with small size
- [ ] Claude Code autonomous trading based on validated criteria

---

## Key Strategies to Implement & Backtest

### 1. Minervini VCP Breakout (Swing, Primary)
- Screen: Trend Template (8 criteria)
- Entry: Breakout from Volatility Contraction Pattern on 1.5x+ volume
- Stop: Below pattern low (typically 3-7%)
- Target: 15-20% partial, trail rest with 10/21 EMA
- Hold: 2-20 days

### 2. EMA Pullback in Uptrend (Swing)
- Filter: Stock above rising 50 SMA, ADX > 25
- Entry: Pullback to 10 or 21 EMA, bounce confirmed
- Stop: Below the EMA or recent swing low
- Target: Prior high or 2:1 R-multiple

### 3. Opening Range Breakout (Day Trade)
- Filter: Stock gapping with relative volume > 2x
- Entry: Break of first 15-min high/low
- Stop: Opposite end of opening range
- Target: 2:1 or close at EOD

### 4. Gap and Go (Day Trade)
- Scan: Stocks gapping 5%+ premarket on 2x+ volume with catalyst
- Entry: Break of first pullback after open
- Stop: Below pullback low or VWAP
- Target: Whole-dollar resistance levels

### 5. RSI(2) Mean Reversion (Swing)
- Filter: Stock above 200 SMA
- Entry: RSI(2) drops below 10
- Exit: RSI(2) rises above 70
- Position size: 1% risk

---

## Risk Rules (Non-Negotiable)
- Max 1% account risk per trade
- Max 5-6% total portfolio heat (sum of all open risks)
- Max 3% daily loss — stop trading for the day
- Never average down on a losing position
- Always have a stop loss defined BEFORE entry
- Cut losses at max 7-8%, no exceptions
