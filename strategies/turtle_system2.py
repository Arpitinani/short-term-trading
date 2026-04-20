"""
Turtle Trading System 2 (55-Day Breakout).

Source: Curtis Faith "Way of the Turtle" (2007)

Rules:
  - Entry:  Price > 55-day highest high (long)
            Price < 55-day lowest low (short, optional)
  - Exit:   Price < 20-day lowest low (long exit)
            Price > 20-day highest high (short exit)
  - Stop:   2 x ATR(20) from entry price
  - Position sizing: 1% of equity / ATR(20) = 1 unit

Verified returns:
  - Turtle program: $100M+ over 4.5 years (1983-1988)
  - Jerry Parker (Chesapeake Capital): ~20-25% annual for decades (audited CTA)

Known characteristics:
  - Win rate: ~35-40%
  - Winners are 5-10x losers
  - Drawdowns of 30-50% are normal
"""

import pandas as pd
import numpy as np

from strategies.base import Strategy, StrategyConfig
from core.indicators import calculate_atr


class TurtleSystem2(Strategy):
    """Turtle Trading System 2 — 55-day breakout trend following."""

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.entry_period = config.params.get("entry_period", 55)
        self.exit_period = config.params.get("exit_period", 20)
        self.atr_period = config.params.get("atr_period", 20)
        self.atr_stop_mult = config.params.get("atr_stop_mult", 2.0)
        self.long_only = config.params.get("long_only", True)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        # Donchian channels — shifted by 1 to avoid look-ahead
        # "Price breaks above the PRIOR 55-day high" (not including today)
        df["entry_high"] = high.rolling(self.entry_period).max().shift(1)
        df["exit_low"] = low.rolling(self.exit_period).min().shift(1)
        df["atr"] = calculate_atr(high, low, close, period=self.atr_period)

        # For short side (if enabled)
        if not self.long_only:
            df["entry_low"] = low.rolling(self.entry_period).min().shift(1)
            df["exit_high"] = high.rolling(self.exit_period).max().shift(1)

        df["signal"] = 0

        in_position = False
        position_dir = 0  # 1 = long, -1 = short
        entry_price = 0.0
        stop_price = 0.0
        signals = []

        for i in range(len(df)):
            signal = 0

            if pd.isna(df["entry_high"].iloc[i]) or pd.isna(df["atr"].iloc[i]):
                signals.append(0)
                continue

            price = float(close.iloc[i])
            h = float(high.iloc[i])
            l = float(low.iloc[i])
            atr = float(df["atr"].iloc[i])
            entry_hi = float(df["entry_high"].iloc[i])
            exit_lo = float(df["exit_low"].iloc[i])

            if not in_position:
                # Long entry: price breaks above 55-day high
                if h > entry_hi and atr > 0:
                    signal = 1
                    entry_price = price
                    stop_price = entry_price - self.atr_stop_mult * atr
                    in_position = True
                    position_dir = 1

                # Short entry (if enabled)
                elif not self.long_only:
                    entry_lo = float(df["entry_low"].iloc[i])
                    if l < entry_lo and atr > 0:
                        signal = 1  # engine handles direction via strategy config
                        entry_price = price
                        stop_price = entry_price + self.atr_stop_mult * atr
                        in_position = True
                        position_dir = -1

            elif in_position and position_dir == 1:
                # Long exit: price drops below 20-day low OR hits stop
                if l < exit_lo or price <= stop_price:
                    signal = -1
                    in_position = False
                    position_dir = 0

                # Trail stop up (never move stop down)
                else:
                    new_stop = price - self.atr_stop_mult * atr
                    if new_stop > stop_price:
                        stop_price = new_stop

            elif in_position and position_dir == -1:
                exit_hi = float(df["exit_high"].iloc[i])
                if h > exit_hi or price >= stop_price:
                    signal = -1
                    in_position = False
                    position_dir = 0

            signals.append(signal)

        df["signal"] = signals
        return df
