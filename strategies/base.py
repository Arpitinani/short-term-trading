"""Base strategy class and configuration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml


@dataclass
class StrategyConfig:
    name: str
    params: dict = field(default_factory=dict)
    universe: list[str] = field(default_factory=lambda: ["SPY"])
    data_period: str = "max"
    cost_bps: float = 15.0
    risk_per_trade: float = 0.01

    @classmethod
    def from_yaml(cls, path: str | Path) -> StrategyConfig:
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            name=data["name"],
            params=data.get("params", {}),
            universe=data.get("universe", ["SPY"]),
            data_period=data.get("data_period", "max"),
            cost_bps=data.get("cost_bps", 15.0),
            risk_per_trade=data.get("risk_per_trade", 0.01),
        )

    def with_params(self, **overrides) -> StrategyConfig:
        """Return a new config with updated params."""
        new_params = {**self.params, **overrides}
        return StrategyConfig(
            name=self.name,
            params=new_params,
            universe=self.universe,
            data_period=self.data_period,
            cost_bps=self.cost_bps,
            risk_per_trade=self.risk_per_trade,
        )


class Strategy(ABC):
    """Base class for all trading strategies."""

    def __init__(self, config: StrategyConfig):
        self.config = config

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a 'signal' column to the OHLCV DataFrame.

        Signal values:
            1  = enter long
           -1  = exit long (close position)
            0  = hold (no action)

        Must not look ahead — only use data up to and including current bar.
        Returns the DataFrame with additional columns (indicators + signal).
        """
        ...
