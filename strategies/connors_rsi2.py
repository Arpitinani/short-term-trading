"""
Connors RSI(2) Mean Reversion Strategy.

Source: "Short-Term Trading Strategies That Work" (Connors & Alvarez, 2008)

Rules:
  - Filter: Close > SMA(200)
  - Entry:  RSI(2) < entry_threshold (default 5)
  - Exit:   RSI(2) > exit_threshold (default 65)

Published results (S&P 500, 1995-2007):
  - RSI(2) < 5: ~84% win rate, ~1.3% avg gain/trade
  - Avg holding period: 3-6 days
"""

import pandas as pd

from strategies.base import Strategy, StrategyConfig
from core.indicators import calculate_rsi, calculate_sma


class ConnorsRSI2(Strategy):
    """Connors RSI(2) mean reversion strategy."""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.rsi_period = config.params.get("rsi_period", 2)
        self.sma_period = config.params.get("sma_period", 200)
        self.entry_threshold = config.params.get("entry_threshold", 5)
        self.exit_threshold = config.params.get("exit_threshold", 65)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["Close"]

        df["rsi2"] = calculate_rsi(close, period=self.rsi_period)
        df["sma200"] = calculate_sma(close, period=self.sma_period)

        df["signal"] = 0

        # Entry: RSI(2) < threshold AND above 200 SMA
        entry_mask = (df["rsi2"] < self.entry_threshold) & (close > df["sma200"])

        # Exit: RSI(2) > exit threshold
        exit_mask = df["rsi2"] > self.exit_threshold

        # Convert to stateful signals (can't enter if already in position)
        in_position = False
        signals = []

        for i in range(len(df)):
            if not in_position and entry_mask.iloc[i]:
                signals.append(1)
                in_position = True
            elif in_position and exit_mask.iloc[i]:
                signals.append(-1)
                in_position = False
            else:
                signals.append(0)

        df["signal"] = signals
        return df
