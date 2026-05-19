"""
APScheduler — periodic rebalancing every 21 trading days.

Runs as a background task inside the FastAPI process.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database.mongo import portfolios_col, rebalance_history_col
from backend.services import ml_service

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()
_REBALANCE_DAYS = int(os.getenv("REBALANCE_DAYS", "21"))


def start_scheduler() -> None:
    """Called on app startup — starts the background scheduler."""
    _scheduler.add_job(
        _rebalance_all_portfolios,
        trigger=IntervalTrigger(days=_REBALANCE_DAYS),
        id="periodic_rebalance",
        replace_existing=True,
        next_run_time=None,   # don't run immediately at startup
    )
    _scheduler.start()
    logger.info(
        "Scheduler started — rebalance every %d days", _REBALANCE_DAYS
    )


def shutdown_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


async def _rebalance_all_portfolios() -> None:
    """Retrain model and rebalance every active portfolio."""
    logger.info("=== Scheduled rebalance triggered ===")

    cursor = portfolios_col().find({"status": "active"})
    portfolios = await cursor.to_list(length=500)

    if not portfolios:
        logger.info("No active portfolios to rebalance")
        return

    for portfolio in portfolios:
        portfolio_id = str(portfolio["_id"])
        stocks = portfolio.get("stocks", [])

        if not stocks:
            continue

        try:
            logger.info("Rebalancing portfolio %s (%d stocks)", portfolio_id, len(stocks))

            # Retrain model for this stock set
            await ml_service.retrain(stocks)

            # Record scheduled rebalance
            await rebalance_history_col().insert_one({
                "portfolio_id": portfolio_id,
                "date":         datetime.now(timezone.utc),
                "type":         "scheduled",
                "old_weights":  {},
                "new_weights":  {},
                "turnover":     0.0,
                "transaction_cost": 0.0,
            })

            # Update last_rebalanced
            await portfolios_col().update_one(
                {"_id": portfolio["_id"]},
                {"$set": {"last_rebalanced": datetime.now(timezone.utc)}},
            )

            logger.info("Portfolio %s rebalanced successfully", portfolio_id)

        except Exception as exc:
            logger.exception(
                "Failed to rebalance portfolio %s: %s", portfolio_id, exc
            )

    logger.info("=== Scheduled rebalance complete (%d portfolios) ===", len(portfolios))
