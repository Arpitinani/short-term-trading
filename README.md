# Short-Term Trading System

A systematic approach to short-term stock trading — research, backtesting, and automated execution.

## Goal

Build a trading system that:
1. Screens for high-probability setups using verified, backtested strategies
2. Validates strategies through walk-forward optimization and Monte Carlo simulation
3. Detects market regime to select appropriate strategies
4. Paper trades via Alpaca to validate real-world execution
5. Executes live trades autonomously via Alpaca API (Claude Code)

## Architecture

```
Next.js Dashboard (TradingView lightweight-charts)
        │ REST API
FastAPI Backend (Python)
  ├── Backtest Engine (VectorBT + walk-forward + Monte Carlo)
  ├── Strategy Engine (config-driven, multi-strategy)
  ├── Screener (Minervini Trend Template + custom)
  ├── Regime Detector (weighted macro signals, backtested)
  ├── Risk Manager (ATR-based sizing, portfolio heat, daily loss limits)
  ├── Execution (Alpaca paper → live → IBKR later)
  └── Notifications (Slack)
        │
Shared Data Layer
  ├── Raw macro data: reused from investing dashboard (VIX, yields, breadth, F&G)
  ├── Indicator calculations: reused (RSI, MACD, ADX, ATR, BB, OBV)
  ├── Market data: Alpaca free tier + yfinance
  └── Regime scoring: rebuilt from scratch, backtested (NOT reused)
```

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Frontend | Next.js + TradingView lightweight-charts | Professional trading charts, same stack as investing dashboard |
| Backend | FastAPI (Python) | Fast async API, auto-generated docs |
| Data (daily) | yfinance | Free, good for backtesting |
| Data (intraday) | Alpaca free tier → Polygon.io | Free to start, reliable paid upgrade |
| Backtesting | VectorBT | Vectorized, 100-1000x faster than event-driven |
| Indicators | pandas-ta + reused from investing dashboard | RSI, MACD, ATR, ADX, BB, OBV, Stochastic |
| Regime data | Reused from investing dashboard (raw signals only) | VIX, yields, DXY, breadth, F&G, inflation |
| Broker (phase 1) | Alpaca | Clean API, free paper trading |
| Broker (phase 2) | Interactive Brokers | Options, shorting, global markets |
| Notifications | Slack webhooks | Simple, reliable |

## Strategy Priority

| # | Strategy | Type | Verified | Regime |
|---|----------|------|----------|--------|
| 1 | Connors RSI(2) | Mean reversion | Published backtests (84% win rate) | Choppy/bull |
| 2 | Turtle System 2 (55-day) | Trend following | Audited CTA records (decades) | Trending |
| 3 | Academic Momentum (12-1) | Factor ranking | Peer-reviewed (1993+) | Bull |
| 4 | Minervini Trend Template | Screening tool | 2x USIC winner (audited) | Bull |

Strategies 1+2 are complementary — when one loses, the other typically wins.

## Validation Pipeline

Every strategy must pass ALL stages before live trading:
1. Hypothesis (why does this edge exist?)
2. Development (60% of data, parameter sensitivity)
3. Walk-forward validation (20% of data, WFE > 0.5)
4. Monte Carlo (10K sims, P(ruin) < 5%)
5. Holdout test (final 20%, ONE shot — fail = reject)
6. Portfolio integration (correlation < 0.3 with existing strategies)
7. Paper trading (1-3 months, fills vs backtest)
8. Live trading (start at 25-50% size, scale up)

## Project Structure

```
short-term-trading/
├── research/              # Strategy research and system design notes
├── core/                  # Shared Python core
│   ├── data/              # Data fetching (Alpaca, yfinance, macro signals)
│   ├── indicators/        # Technical indicators (reused + new)
│   ├── regime/            # Market regime detection (rebuilt, backtested)
│   └── risk/              # Position sizing, portfolio heat, daily limits
├── strategies/            # Strategy implementations (config-driven)
├── backtest/              # Backtesting engine (walk-forward, Monte Carlo)
├── screener/              # Stock screening (Trend Template, momentum rank)
├── execution/             # Alpaca/IBKR integration, order management
├── api/                   # FastAPI backend
├── dashboard/             # Next.js frontend
├── notifications/         # Slack/email alerts
└── notebooks/             # Jupyter notebooks for exploration
```

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the phased build plan.
See [research/strategy_notes.md](research/strategy_notes.md) for detailed strategy research.
See [research/system_design.md](research/system_design.md) for system design (walk-forward, Monte Carlo, regime, correlation).
