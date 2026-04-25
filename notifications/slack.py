"""
Slack notification service.

Sends trading alerts via Slack webhook.
Setup: Create a Slack app, add an Incoming Webhook, set SLACK_WEBHOOK_URL env var.

Messages sent:
  - Trade signals (new entry opportunities)
  - Orders placed / skipped
  - Positions closed
  - Regime changes
  - Daily summaries
  - Errors / warnings
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# Regime emoji/color mapping
REGIME_EMOJI = {
    "risk_on": ":large_green_circle:",
    "bullish": ":large_blue_circle:",
    "cautious": ":large_orange_circle:",
    "risk_off": ":red_circle:",
}

REGIME_COLOR = {
    "risk_on": "#22c55e",
    "bullish": "#3b82f6",
    "cautious": "#f59e0b",
    "risk_off": "#ef4444",
}


def _send(blocks: list[dict], text: str = "") -> bool:
    """Send a Slack message. Returns True on success."""
    if not WEBHOOK_URL:
        logger.info(f"[SLACK DRY RUN] {text}")
        return True

    payload = {"text": text, "blocks": blocks}

    try:
        resp = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error(f"Slack webhook failed: {resp.status_code} {resp.text}")
            return False
        return True
    except Exception as e:
        logger.error(f"Slack send error: {e}")
        return False


def _section(text: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": text}}


def _divider() -> dict:
    return {"type": "divider"}


def _header(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text}}


# -------------------------------------------------------------------
# Notification types
# -------------------------------------------------------------------

def notify_regime(regime: str, score: float, allowed_strategies: list[str]) -> bool:
    """Send regime status notification."""
    emoji = REGIME_EMOJI.get(regime, ":grey_question:")
    strategies = ", ".join(allowed_strategies) if allowed_strategies else "None (cash)"

    blocks = [
        _header(f"{emoji} Market Regime: {regime.upper().replace('_', '-')}"),
        _section(
            f"*Score:* {score:+.3f}\n"
            f"*Allowed Strategies:* {strategies}"
        ),
    ]

    return _send(blocks, f"Regime: {regime} ({score:+.3f})")


def notify_signal(
    ticker: str,
    strategy: str,
    action: str,
    entry_price: float,
    stop_price: float,
    target_price: float | None = None,
    reason: str = "",
) -> bool:
    """Send trade signal notification."""
    emoji = ":chart_with_upwards_trend:" if action == "buy" else ":chart_with_downwards_trend:"
    target_str = f"${target_price:.2f}" if target_price else "trailing"
    risk_pct = abs(entry_price - stop_price) / entry_price * 100

    blocks = [
        _header(f"{emoji} Signal: {action.upper()} {ticker}"),
        _section(
            f"*Strategy:* {strategy}\n"
            f"*Entry:* ${entry_price:.2f}\n"
            f"*Stop:* ${stop_price:.2f} ({risk_pct:.1f}% risk)\n"
            f"*Target:* {target_str}\n"
            f"*Reason:* {reason}"
        ),
    ]

    return _send(blocks, f"Signal: {action} {ticker} @ ${entry_price:.2f} ({strategy})")


def notify_order(
    ticker: str,
    side: str,
    qty: int,
    order_type: str,
    status: str,
    stop_loss: float | None = None,
    take_profit: float | None = None,
) -> bool:
    """Send order execution notification."""
    emoji = ":white_check_mark:" if status == "filled" else ":hourglass:" if status in ("accepted", "pending_new") else ":x:"

    details = f"*{side.upper()}* {qty} {ticker} ({order_type})"
    if stop_loss:
        details += f"\nStop: ${stop_loss:.2f}"
    if take_profit:
        details += f"\nTarget: ${take_profit:.2f}"

    blocks = [
        _section(f"{emoji} *Order {status.upper()}*\n{details}"),
    ]

    return _send(blocks, f"Order: {side} {qty} {ticker} — {status}")


def notify_position_closed(
    ticker: str,
    pnl: float,
    pnl_pct: float,
    reason: str = "",
) -> bool:
    """Send position closed notification."""
    emoji = ":moneybag:" if pnl > 0 else ":money_with_wings:"
    color = "green" if pnl > 0 else "red"

    blocks = [
        _section(
            f"{emoji} *Position Closed: {ticker}*\n"
            f"*P&L:* ${pnl:+,.0f} ({pnl_pct:+.1%})\n"
            f"*Reason:* {reason}"
        ),
    ]

    return _send(blocks, f"Closed {ticker}: ${pnl:+,.0f} ({pnl_pct:+.1%})")


def notify_scan_summary(
    regime: str,
    regime_score: float,
    signals_count: int,
    orders_placed: int,
    orders_skipped: int,
    positions_closed: int,
    equity: float,
    portfolio_heat: str,
) -> bool:
    """Send scan summary notification."""
    emoji = REGIME_EMOJI.get(regime, "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    blocks = [
        _header(f":robot_face: Trading Scan — {timestamp}"),
        _section(
            f"{emoji} *Regime:* {regime.upper().replace('_', '-')} ({regime_score:+.3f})\n"
            f"*Signals:* {signals_count}\n"
            f"*Orders Placed:* {orders_placed}\n"
            f"*Orders Skipped:* {orders_skipped}\n"
            f"*Positions Closed:* {positions_closed}"
        ),
        _divider(),
        _section(
            f"*Equity:* ${equity:,.0f}\n"
            f"*Portfolio Heat:* {portfolio_heat}"
        ),
    ]

    return _send(blocks, f"Scan complete: {signals_count} signals, {orders_placed} orders")


def notify_daily_summary(
    date: str,
    regime: str,
    equity: float,
    daily_pnl: float,
    open_positions: int,
    trades_today: int,
    wins: int,
    losses: int,
) -> bool:
    """Send end-of-day summary."""
    pnl_emoji = ":arrow_up:" if daily_pnl > 0 else ":arrow_down:" if daily_pnl < 0 else ":left_right_arrow:"
    regime_emoji = REGIME_EMOJI.get(regime, "")

    blocks = [
        _header(f":calendar: Daily Summary — {date}"),
        _section(
            f"{regime_emoji} *Regime:* {regime.upper().replace('_', '-')}\n"
            f"{pnl_emoji} *Daily P&L:* ${daily_pnl:+,.0f}\n"
            f"*Equity:* ${equity:,.0f}\n"
            f"*Open Positions:* {open_positions}\n"
            f"*Trades Today:* {trades_today} ({wins}W / {losses}L)"
        ),
    ]

    return _send(blocks, f"Daily summary: ${daily_pnl:+,.0f} P&L, {equity:,.0f} equity")


def notify_error(message: str, details: str = "") -> bool:
    """Send error notification."""
    blocks = [
        _section(f":rotating_light: *Error*\n{message}"),
    ]
    if details:
        blocks.append(_section(f"```{details}```"))

    return _send(blocks, f"Error: {message}")
