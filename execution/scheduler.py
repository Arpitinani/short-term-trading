"""
Scan scheduler — automates trading scans on a schedule.

Modes:
  1. API-triggered: POST /scan from the dashboard or Claude Code
  2. CLI: python -m execution.scheduler --once (single scan)
  3. Scheduled: python -m execution.scheduler --interval 3600 (hourly)

The scheduler handles:
  - Morning scan (pre-market or at open)
  - Evening scan (after close, prepare for next day)
  - Periodic exit checks during market hours
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

from execution.orchestrator import Orchestrator
from notifications import slack

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_scan(
    broker_mode: str = "dry_run",
    notify: bool = True,
) -> None:
    """Run a single trading scan."""
    logger.info("Starting trading scan...")

    try:
        orch = Orchestrator(broker_mode=broker_mode, notify=notify)
        result = orch.run_scan()

        logger.info(f"Scan complete: {len(result.signals)} signals, "
                    f"{len(result.orders_placed)} orders, "
                    f"{len(result.positions_closed)} closed")
        logger.info(result.summary)

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        if notify:
            slack.notify_error("Trading scan failed", str(e))


def run_scheduled(
    interval_seconds: int = 3600,
    broker_mode: str = "dry_run",
    notify: bool = True,
) -> None:
    """Run scans on a recurring schedule."""
    logger.info(f"Starting scheduler: scan every {interval_seconds}s ({interval_seconds/60:.0f} min)")

    while True:
        now = datetime.now()
        hour = now.hour

        # Only scan during market hours (9:30 AM - 4:00 PM ET)
        # Simplified: assume we're in ET timezone
        if 9 <= hour <= 16:
            run_scan(broker_mode=broker_mode, notify=notify)
        else:
            logger.info(f"Outside market hours ({hour}:00), skipping scan")

        logger.info(f"Next scan in {interval_seconds}s")
        time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="Trading scan scheduler")
    parser.add_argument("--once", action="store_true", help="Run a single scan and exit")
    parser.add_argument("--interval", type=int, default=3600, help="Scan interval in seconds (default: 3600)")
    parser.add_argument("--broker", default="dry_run", choices=["dry_run", "paper", "live"], help="Broker mode")
    parser.add_argument("--no-notify", action="store_true", help="Disable Slack notifications")

    args = parser.parse_args()

    if args.once:
        run_scan(broker_mode=args.broker, notify=not args.no_notify)
    else:
        run_scheduled(
            interval_seconds=args.interval,
            broker_mode=args.broker,
            notify=not args.no_notify,
        )


if __name__ == "__main__":
    main()
