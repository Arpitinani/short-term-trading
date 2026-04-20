# System Design: Robustness & Risk Components

## 1. Walk-Forward Optimization

**What:** Split historical data into rolling train/test windows. Optimize on train, validate on test, slide forward. Concatenate all out-of-sample results for true performance estimate.

**Our approach:** Rolling windows
- Train: 3 years (756 trading days)
- Test: 6 months (126 trading days)
- Step: 6 months (non-overlapping OOS periods)
- Minimum 30 trades per test window for statistical significance

**Key metric:** Walk-Forward Efficiency = OOS Sharpe / IS Sharpe
- \> 0.5 = robust strategy
- < 0.3 = likely overfit

**Why not k-fold cross-validation?** It shuffles data randomly, destroying temporal ordering. A fold from 2023 could train on 2024 data — pure look-ahead bias.

---

## 2. Market Regime Detection

**Raw signals (from investing dashboard — factual data):**
- VIX level and VIX term structure (VIX/VIX3M)
- Fear & Greed Index (CNN)
- Yield curve (10Y - 3M spread)
- Dollar Index (DXY) vs 50-day SMA
- Copper/Gold ratio (risk appetite)
- S&P 500 breadth (% above 200-day SMA)
- SPX vs 50/200 SMA
- Golden/Death Cross confirmation
- Fed rate expectations (CME ZQ)
- Inflation (CPI, Core PCE via FRED)

**What we rebuild (NOT reusing from investing dashboard):**
- Scoring weights for each indicator
- Threshold levels for bullish/bearish classification
- Regime aggregation logic
- All weights and thresholds must be validated through backtesting

**New additions:**
- Hurst exponent (trending vs mean-reverting detection)
- Weighted scoring instead of equal-weight +1/0/-1

**Regime-to-strategy mapping:**

| Regime | Strategies | Position Sizing |
|--------|-----------|-----------------|
| Bull trending | Turtle + momentum + Trend Template screen | Full size (1% per trade, 6% heat) |
| Leaning bullish | All strategies | Normal (1% per trade, 5% heat) |
| Choppy | Mean reversion (RSI2, Double 7) only | Reduced (0.75% per trade, 3% heat) |
| Bear/crisis | Cash preferred, defensive only | Minimal (0.5% per trade, 1% heat) |

**Implementation approach:** Start as a filter (don't trade in bad regimes). Upgrade to switch (different strategy per regime) once we have multiple validated strategies.

---

## 3. Monte Carlo Simulation

**What we simulate:** Shuffle the order of trade P&Ls from backtest, replay 10,000 times. This shows the range of possible equity curves from the same trades in different sequences.

**Why:** Historical backtest gives ONE equity curve. The future won't replay in the same order. A backtest might show 15% max drawdown, but Monte Carlo might reveal the 95th percentile drawdown is 35% — meaning you got lucky with trade ordering.

**Method:** Trade resampling (primary) + block bootstrap of daily returns (secondary)

**Key outputs:**
- Median max drawdown
- 95th percentile max drawdown (this is your "realistic worst case")
- Probability of ruin (hitting -50% drawdown)
- Confidence intervals on total return

**Decision criteria:**
- 95th percentile drawdown must be < 2× your acceptable max drawdown
- Probability of ruin < 5%
- Median return must be meaningfully positive after costs

---

## 4. Strategy Correlation Analysis

**Why:** Two uncorrelated strategies with Sharpe 0.5 each beat one strategy with Sharpe 0.8 in risk-adjusted terms. Portfolio Sharpe scales as individual Sharpe × √N (for uncorrelated strategies).

**What to measure:**
- Return correlation (Pearson + Spearman)
- **Drawdown correlation** (more important — do they blow up together?)
- Tail correlation (correlation during worst days only)
- Rolling correlation (does it change over time/regimes?)

**Criteria for adding a strategy to the portfolio:**
- Return correlation < 0.5 with any existing strategy
- Drawdown correlation < 0.3
- Positive diversification ratio (> 1.3)

**Capital allocation:** Risk parity (inverse volatility weighting)
- Volatile strategy gets less capital
- Stable strategy gets more capital
- Simple, robust, doesn't require estimating expected returns

---

## 5. Additional Robustness Checks

### Parameter Sensitivity
- Test ±20% around optimal parameter values
- At least 60% of nearby values must be profitable
- Must show a "plateau" (smooth performance surface), not a "spike"
- Spike = overfit to noise. Plateau = real signal.

### Transaction Costs
- Model: spread (5 bps) + slippage (2-3 bps) = ~7-8 bps one way, ~15 bps round trip
- Break-even calculation: at 250 trades/year, need ~3.75% annual return just to cover costs
- All backtests must include realistic costs

### Survivorship Bias
- S&P 500 of 2015 ≠ S&P 500 of 2025 — failed companies were removed
- For initial backtesting: acknowledge the bias, note it in results
- For production: consider Norgate Data (~$300/year) for survivorship-bias-free data

### Out-of-Sample Discipline
- 60% development / 20% validation / 20% holdout
- Holdout is touched ONCE for final go/no-go
- If holdout fails, strategy is REJECTED — no going back to re-optimize

---

## Validation Pipeline Summary

```
Idea
  → "Why does this edge exist? Who's on the other side?"
  → If no answer, STOP

Development (60% of data)
  → Code strategy
  → Parameter sensitivity — must show plateau
  → 100+ trades minimum
  → If fragile, STOP

Walk-Forward Validation (20% of data)
  → Rolling 3yr/6mo windows
  → WFE > 0.5
  → Stable parameters across windows
  → If overfit, STOP

Monte Carlo (on WFO results)
  → 10,000 sims
  → 95th pctile drawdown tolerable
  → P(ruin) < 5%
  → If fragile, STOP

Holdout Test (final 20% — ONE shot)
  → Parameters from validation (NO re-optimization)
  → Positive Sharpe + DD within Monte Carlo CI
  → FAIL = reject entirely

Portfolio Integration
  → Correlation analysis with existing strategies
  → Risk parity allocation
  → Combined Monte Carlo

Paper Trading (1-3 months)
  → Compare fills vs backtest
  → Strategy correlation > 0.85 with backtest

Live Trading
  → Start at 25-50% size
  → Scale up over 2-3 months
  → Kill switch: rolling 3-month Sharpe < 0 for 2 consecutive months
```
