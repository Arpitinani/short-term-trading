"""Transaction cost model for backtesting."""

from dataclasses import dataclass


@dataclass
class CostModel:
    spread_bps: float = 5.0      # bid-ask half-spread in basis points
    slippage_bps: float = 3.0    # execution slippage in basis points
    commission_per_share: float = 0.0  # per-share commission (Alpaca = $0)

    @property
    def one_way_bps(self) -> float:
        return self.spread_bps + self.slippage_bps

    @property
    def round_trip_bps(self) -> float:
        return 2 * self.one_way_bps

    def entry_cost(self, price: float, shares: int) -> float:
        """Dollar cost of entering a position."""
        return price * (self.one_way_bps / 10_000) * shares + self.commission_per_share * shares

    def exit_cost(self, price: float, shares: int) -> float:
        """Dollar cost of exiting a position."""
        return price * (self.one_way_bps / 10_000) * shares + self.commission_per_share * shares

    def adjusted_entry_price(self, price: float, direction: int = 1) -> float:
        """Price after spread+slippage. direction: 1=buy (worse=higher), -1=short (worse=lower)."""
        return price * (1 + direction * self.one_way_bps / 10_000)

    def adjusted_exit_price(self, price: float, direction: int = 1) -> float:
        """Price after spread+slippage on exit. direction: 1=was long (sell=lower), -1=was short (cover=higher)."""
        return price * (1 - direction * self.one_way_bps / 10_000)

    def break_even_annual(self, trades_per_year: int) -> float:
        """Minimum annual return needed to cover costs."""
        return self.round_trip_bps / 10_000 * trades_per_year
