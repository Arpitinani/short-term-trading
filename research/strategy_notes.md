# Strategy Research Notes

## Verification Standard

Only strategies with **independently verified** returns are in Tier 1.
Self-reported screenshots, unaudited claims, and "trust me" track records go to Tier 3.

| Trader | Claimed Returns | Verified? | Source |
|--------|----------------|-----------|--------|
| Mark Minervini | 220% avg annual, 2x USIC winner | **YES** | US Investing Championship (third-party audited) |
| Dan Zanger | 29,233% in <2 years | **YES** | Fortune magazine verification |
| David Ryan | 161%, 160%, 46% (3 consecutive USIC wins) | **YES** | US Investing Championship (audited) |
| Larry Williams | 11,376% in 12 months | **YES** | Robbins World Cup (third-party audited) |
| Richard Dennis / Turtles | $100M+ over 4.5 years | **YES** | Multiple Turtle confirmations; Jerry Parker's CTA audited ~20-25% annual for decades |
| Larry Connors | N/A (researcher, not trader) | **YES** | Extensive published backtests with methodology |
| Momentum factor | ~12% annual excess | **YES** | Jegadeesh & Titman 1993, hundreds of replications |
| Post-earnings drift | ~2-4% per quarter excess | **YES** | Bernard & Thomas 1989, robust across periods |
| Ross Cameron | 300%+ years | **PARTIAL** | Self-reported "audited" by own accountant |
| Kristjan Kullamägi | $5K → $80M+ | **NO** | Twitter screenshots only |
| Ed Seykota | $5K → $15M+ over 12 years | **NO** | Self-reported in Market Wizards interview |
| Andrew Aziz | Profitable day trader | **NO** | No verified P&L published |

---

## Tier 1 Strategies: Fully Mechanical + Verified

### 1. Connors RSI(2) Mean Reversion

**Source:** "Short-Term Trading Strategies That Work" (2008, Connors & Alvarez)

**Exact Rules:**
- Filter: Price ABOVE 200-day SMA
- Entry: Buy at close when RSI(2) < 5
- Exit: Sell at close when RSI(2) > 65
- No stop loss in published version

**Published Results (S&P 500 stocks, 1995-2007):**

| Entry Threshold | Win Rate | Avg Gain/Trade |
|-----------------|----------|----------------|
| RSI(2) < 2 | ~88% | ~1.7% |
| RSI(2) < 5 | ~84-85% | ~1.3% |
| RSI(2) < 10 | ~79-80% | ~0.9% |

- Average holding period: 3-6 days
- Tested on all S&P 500 stocks with no stop loss

**Variations:**
- Cumulative RSI: Sum of last 2 RSI(2) readings < 35
- Double 7: Buy at 7-day low close (above 200 SMA), sell at 7-day high close
- ConnorsRSI: (RSI(Close,3) + RSI(Streak,2) + PercentRank(ROC(1),100)) / 3

**Known Weaknesses:**
- No stop loss = individual trades can draw down 20-30% before reverting
- In 2008, RSI(2) buy signals in financials produced catastrophic losses
- 200 SMA filter doesn't protect in fast crashes (stock above 200 SMA one day, -20% the next)
- The edge may have decayed post-publication (2008-2009)
- "Buying the dip" psychologically very hard during scary selloffs

**What to Backtest:**
- Original rules vs rules with stop losses (Connors says stops hurt — verify this)
- RSI(2) < 5 vs < 10 entry thresholds
- Exit at 65 vs 70 vs 90
- On SPY/QQQ ETFs vs individual stocks
- Performance per market regime (does it fail in trending markets?)

---

### 2. Turtle Trading System 2 (55-Day Breakout)

**Source:** Curtis Faith "Way of the Turtle" (2007), free PDF "The Original Turtle Trading Rules"

**Exact Rules:**
- Entry: Buy when price > 55-day highest high. Short when price < 55-day lowest low.
- Exit: Close long when price < 20-day lowest low. Close short when price > 20-day highest high.
- No filter — every breakout is taken.

**Position Sizing (ATR-based):**
```
N = ATR(20)  (20-day exponential moving average of True Range)
Unit = floor(0.01 × Account_Equity / N)
```
Each unit's daily volatility = 1% of account equity.

**Stop Loss:** 2N from entry price
- Long stop = Entry - 2N
- Short stop = Entry + 2N
- Risking exactly 2% of account per unit

**Pyramiding:**
- Max 4 units per instrument
- Add 1 unit every 0.5N price movement from prior entry
- All stops move to 2N from newest entry

**Correlation Limits:**
- Max 4 units in one market
- Max 6 units in closely correlated markets
- Max 10 units in single direction
- Max 12 units total

**Verified Returns:**
- Turtle program: $100M+ in ~4.5 years (1983-1988)
- Jerry Parker (Chesapeake Capital): ~20-25% annual compound for decades (audited CTA)

**Known Weaknesses:**
- Win rate: ~35-40% (most trades lose money)
- Drawdowns of 30-50% are normal and expected
- Gets whipsawed badly in range-bound/choppy markets
- Breakout entries have significant slippage
- Long losing streaks (10+ consecutive losers) are common
- Psychologically brutal — low win rate + frequent stops + skipping winners

**Adaptation for Stocks:**
- System 2 (55-day) works better than System 1 (20-day) on stocks — filters more noise
- Use on ETFs (SPY, QQQ, sector ETFs) rather than individual stocks
- Wider stops (3N instead of 2N) due to overnight gap risk in stocks
- Cap individual positions at 5-10% of equity
- Consider: long-only (skip shorts) due to long-term upward bias in equities

---

### 3. Academic Momentum Factor (12-1 Month)

**Source:** Jegadeesh & Titman 1993, replicated hundreds of times across markets

**Exact Rules:**
- Rank all stocks by their 12-month return, excluding the most recent month
- Buy top decile (or quintile), short bottom decile
- Hold 3-12 months, rebalance monthly
- The "skip last month" is critical — it avoids short-term reversal

**Published Results:**
- ~1% per month excess return (12% annualized) over 1965-1989
- Confirmed in out-of-sample periods across many countries
- Works in equities, currencies, commodities, bonds

**Use In Our System:** Stock selection/ranking overlay
- Use momentum ranking to decide WHICH stocks get the RSI(2) or Turtle treatment
- Long-only variant: buy top 20% by 12-1 month momentum, equal weight, rebalance monthly

**Known Weaknesses:**
- Momentum crashes — sharp, sudden reversals (March 2009: -40% in a single month)
- Weaker post-2000 performance (possibly more crowded)
- Long-short version requires shorting; long-only variant is safer

---

### 4. Post-Earnings Announcement Drift (PEAD)

**Source:** Bernard & Thomas 1989, one of the most robust anomalies in finance

**Exact Rules:**
- Buy stocks with positive earnings surprise > 1 standard deviation above consensus
- Short stocks with negative earnings surprise > 1 standard deviation below
- Hold for 60 trading days (~3 months)

**Published Results:**
- ~2-4% per quarter excess return
- Confirmed across many time periods and markets
- The drift has diminished somewhat post-2000 but remains statistically significant

**Requirements:**
- Earnings estimates data (consensus EPS) — this is a data cost
- Quick execution post-announcement

---

## Tier 1.5: Verified Traders, Partially Codeable

### Mark Minervini — SEPA / VCP

**Trend Template (ALL must be true — 100% codeable as a screener):**
1. Price > 150-day MA AND 200-day MA
2. 150-day MA > 200-day MA
3. 200-day MA trending up for 1+ months (ideally 4-5)
4. 50-day MA > 150-day AND 200-day
5. Price > 50-day MA
6. Price ≥ 25% above 52-week low (ideally 100%+)
7. Price within 25% of 52-week high
8. Relative Strength ranking 70+ (ideally 90+)

**VCP Entry (requires visual judgment — ~70% codeable):**
- Progressively tighter consolidations (25% → 15% → 8% → 3%)
- Volume dries up at pivot point
- Buy breakout above pivot on 1.5x+ average volume

**Risk:** Max loss 7-8%, often tighter 3-5%. Risks 1-1.25% portfolio per trade. 3:1 R minimum.

### David Ryan — Refined CAN SLIM (3x USIC winner, audited)
- More concentrated than O'Neil (4-8 positions, 20-30% per position)
- Faster stops (5-7% vs O'Neil's 7-8%)
- Same fundamental filters (EPS 25%+, RS 85+, industry leader)
- Entry: Cup-and-handle or flat base breakout on 50%+ volume
- Exit: 20-25% profit target, or hold 8 weeks if up 20% in first 3 weeks

### Larry Williams — Volatility Breakout + COT
- **WARNING:** His 11,376% return used 20-40% risk per trade — suicidal sizing
- Williams %R: Buy when %R < -80 crosses back above -80 (in uptrend context)
- Volatility breakout: Buy at Open + (k × Yesterday's Range), k = 0.5-1.0
- COT Index as directional filter (Commercials net position percentile)
- **Best use:** COT as a macro filter (futures only), volatility breakout concept as an entry modifier

---

## Tier 2: Unverified or Discretionary

### Linda Raschke
- "Holy Grail": ADX > 30, buy first pullback to 20 EMA
- "Turtle Soup": Fade false breakouts of 20-day highs/lows
- 3/10/16 MACD oscillator
- Featured in Market Wizards but specific returns not audited

### Kristjan Kullamägi
- Episodic pivots, VCP breakouts, momentum
- Self-reported $5K → $80M+ — screenshots only, not verified
- Methods heavily influenced by Minervini (who IS verified)

### Ross Cameron
- Gap and Go on small-caps
- Self-reported "audited" by own accountant
- Good educational content, but returns not independently verified

---

## Critical Concept: Mean Reversion + Trend Following = Complementary

When trend following loses money (choppy markets), mean reversion makes money.
When mean reversion loses money (crashes, strong trends), trend following makes money.

Running both together produces:
- Lower drawdowns than either alone
- Higher Sharpe ratio (uncorrelated strategies combine as Sharpe × √N)
- More consistent equity curve

This is why Strategy 1 (Connors RSI2) + Strategy 2 (Turtle) is the right starting pair.

---

## Key Books for Reference

1. "Short-Term Trading Strategies That Work" — Connors & Alvarez (RSI2 systems)
2. "Way of the Turtle" — Curtis Faith (Turtle system complete rules)
3. "Trade Like a Stock Market Wizard" — Mark Minervini (VCP, Trend Template)
4. "How to Make Money in Stocks" — William O'Neil (CAN SLIM)
5. "Trading in the Zone" — Mark Douglas (trading psychology)
6. "Advances in Financial Machine Learning" — Marcos López de Prado (walk-forward, CPCV)
7. "Long-Term Secrets to Short-Term Trading" — Larry Williams (volatility breakout, COT)
