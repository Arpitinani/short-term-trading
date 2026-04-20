"""Position sizing calculators."""

import math


def fixed_fractional_size(
    equity: float,
    risk_per_trade: float,
    entry_price: float,
    stop_price: float,
) -> int:
    """
    Calculate shares based on fixed fractional risk.

    Args:
        equity: Current account equity
        risk_per_trade: Fraction of equity to risk (e.g., 0.01 = 1%)
        entry_price: Planned entry price
        stop_price: Planned stop-loss price

    Returns:
        Number of shares (floored to integer, minimum 0)
    """
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share <= 0:
        return 0

    dollar_risk = equity * risk_per_trade
    shares = math.floor(dollar_risk / risk_per_share)
    return max(0, shares)


def atr_based_size(
    equity: float,
    risk_per_trade: float,
    atr: float,
    atr_multiplier: float = 2.0,
) -> int:
    """
    Turtle-style position sizing. Stop = atr_multiplier * ATR from entry.

    Each unit's daily volatility = risk_per_trade * equity / atr_multiplier.
    """
    if atr <= 0:
        return 0

    dollar_risk = equity * risk_per_trade
    risk_per_share = atr * atr_multiplier
    shares = math.floor(dollar_risk / risk_per_share)
    return max(0, shares)


def equal_weight_size(
    equity: float,
    entry_price: float,
    max_positions: int = 10,
) -> int:
    """Simple equal-weight: divide equity by max_positions."""
    if entry_price <= 0 or max_positions <= 0:
        return 0
    allocation = equity / max_positions
    return math.floor(allocation / entry_price)
