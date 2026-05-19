"""
MongoDB connection management using Motor (async driver).
"""

import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Initialize Motor client and select database."""
    global _client, _db
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB", "portfolio_ai")
    _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10_000)
    _db = _client[db_name]

    # Verify connection
    await _client.admin.command("ping")
    logger.info("MongoDB connected → db=%s", db_name)

    # Create indexes
    await _create_indexes()


async def close_db() -> None:
    """Close Motor client."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Return the active database (dependency-injection friendly)."""
    if _db is None:
        raise RuntimeError("Database not initialized — call connect_db() first")
    return _db


# ---------------------------------------------------------------------------
# Collection accessors
# ---------------------------------------------------------------------------

def users_col():
    return get_db()["users"]


def portfolios_col():
    return get_db()["portfolios"]


def transactions_col():
    return get_db()["transactions"]


def weights_history_col():
    return get_db()["weights_history"]


def model_metrics_col():
    return get_db()["model_metrics"]


def rebalance_history_col():
    return get_db()["rebalance_history"]


# ---------------------------------------------------------------------------
# Index creation
# ---------------------------------------------------------------------------

async def _create_indexes() -> None:
    db = get_db()

    await db["users"].create_index("email", unique=True)
    await db["portfolios"].create_index("user_id")
    await db["weights_history"].create_index([("portfolio_id", 1), ("date", -1)])
    await db["model_metrics"].create_index([("portfolio_id", 1), ("date", -1)])
    await db["rebalance_history"].create_index([("portfolio_id", 1), ("date", -1)])
    await db["transactions"].create_index([("portfolio_id", 1), ("date", -1)])

    logger.info("MongoDB indexes ensured")
