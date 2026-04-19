# Short-Term Trading System

A systematic approach to short-term stock trading — from research and backtesting to automated execution.

## Goal

Build a Python-based trading system that:
1. Screens for high-probability trade setups
2. Backtests strategies with proper risk management
3. Paper trades via Alpaca to validate
4. Eventually executes live trades automatically via Alpaca API

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Data (daily) | yfinance | Free, easy, good for development |
| Data (intraday) | Polygon.io | Reliable, excellent API |
| Backtesting (fast) | VectorBT | Rapid exploration, parameter sweeps |
| Backtesting (realistic) | Backtrader | Event-driven, proper execution modeling |
| Indicators | pandas-ta | 130+ indicators, pure Python |
| Screening | Custom Python | Full control, automatable |
| Charting | TradingView + mplfinance | Visual + programmatic |
| Alerts | TradingView webhooks | Proven, low-latency |
| Execution | Alpaca API | Clean API, free paper trading, then live |

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the detailed 2-week plan.

## Project Structure

```
short-term-trading/
├── research/           # Strategy research notes and references
├── data/               # Downloaded market data (gitignored)
├── strategies/         # Strategy implementations
├── backtests/          # Backtest scripts and results
├── screener/           # Stock screening tools
├── execution/          # Alpaca integration, order management
├── risk/               # Position sizing and risk management
├── utils/              # Shared utilities
└── notebooks/          # Jupyter notebooks for exploration
```
