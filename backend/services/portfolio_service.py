"""
Portfolio business logic service.

All database writes live here so API routes stay thin.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId

from backend.database.mongo import (
    portfolios_col,
    rebalance_history_col,
    transactions_col,
    weights_history_col,
)
from backend.database.models import (
    PortfolioCreate,
    PortfolioInDB,
    RebalanceRecord,
    TransactionRecord,
    WeightHistoryEntry,
)
from backend.services import ml_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Portfolio CRUD
# ---------------------------------------------------------------------------

async def create_portfolio(user_id: str, payload: PortfolioCreate) -> Dict:
    """Create portfolio document and trigger initial model training."""
    doc = {
        "user_id":        user_id,
        "name":           payload.name,
        "stocks":         [t.upper().strip() for t in payload.stocks],
        "capital":        payload.capital,
        "status":         "training",
        "model_trained":  False,
        "created_at":     datetime.now(timezone.utc),
        "last_rebalanced": None,
    }
    result = await portfolios_col().insert_one(doc)
    portfolio_id = str(result.inserted_id)
    doc["_id"] = portfolio_id

    # Log transaction
    await _log_transaction(portfolio_id, "create", {"stocks": payload.stocks, "capital": payload.capital})

    # Trigger initial training
    await ml_service.retrain(doc["stocks"])

    return _fmt(doc)


async def get_portfolio(portfolio_id: str, user_id: str) -> Optional[Dict]:
    doc = await portfolios_col().find_one(
        {"_id": ObjectId(portfolio_id), "user_id": user_id}
    )
    return _fmt(doc) if doc else None


async def list_portfolios(user_id: str) -> List[Dict]:
    cursor = portfolios_col().find({"user_id": user_id})
    docs   = await cursor.to_list(length=100)
    return [_fmt(d) for d in docs]


# ---------------------------------------------------------------------------
# Stock management
# ---------------------------------------------------------------------------

async def add_stock(portfolio_id: str, user_id: str, ticker: str) -> Dict:
    """Add a stock to the portfolio and trigger rebalancing."""
    ticker = ticker.upper().strip()
    doc = await _get_portfolio_or_raise(portfolio_id, user_id)

    if ticker in doc["stocks"]:
        raise ValueError(f"{ticker} is already in the portfolio")

    new_stocks = doc["stocks"] + [ticker]

    await portfolios_col().update_one(
        {"_id": ObjectId(portfolio_id)},
        {"$set": {"stocks": new_stocks, "status": "training", "model_trained": False}},
    )
    await _log_transaction(portfolio_id, "add_stock", {"ticker": ticker})

    # Retrain with new stock set
    await ml_service.retrain(new_stocks)

    return {"message": f"{ticker} added. Model retraining started.", "stocks": new_stocks}


async def remove_stock(portfolio_id: str, user_id: str, ticker: str) -> Dict:
    """
    Remove a stock and proportionally redistribute its capital.
    Capital never sits idle — it flows to remaining stocks.
    """
    ticker = ticker.upper().strip()
    doc = await _get_portfolio_or_raise(portfolio_id, user_id)

    if ticker not in doc["stocks"]:
        raise ValueError(f"{ticker} is not in the portfolio")

    remaining = [t for t in doc["stocks"] if t != ticker]
    if not remaining:
        raise ValueError("Cannot remove the last stock from a portfolio")

    await portfolios_col().update_one(
        {"_id": ObjectId(portfolio_id)},
        {"$set": {"stocks": remaining, "status": "training", "model_trained": False}},
    )
    await _log_transaction(portfolio_id, "remove_stock", {
        "ticker":    ticker,
        "remaining": remaining,
        "note":      "Capital redistributed proportionally among remaining stocks",
    })

    # Retrain with reduced stock set
    await ml_service.retrain(remaining)

    return {
        "message":   f"{ticker} removed. Capital redistributed proportionally. Model retraining started.",
        "stocks":    remaining,
    }


# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------

async def get_weights(portfolio_id: str, user_id: str) -> Dict:
    """Return latest portfolio weights + ₹ allocations."""
    doc = await _get_portfolio_or_raise(portfolio_id, user_id)
    stocks  = doc["stocks"]
    capital = doc["capital"]

    allocations, model_trained = await ml_service.get_weights(stocks, capital)

    # Persist snapshot
    weights_dict     = {a["ticker"]: a["weight"]         for a in allocations}
    allocation_dict  = {a["ticker"]: a["allocation_inr"] for a in allocations}

    await weights_history_col().insert_one({
        "portfolio_id": portfolio_id,
        "date":         datetime.now(timezone.utc),
        "weights":      weights_dict,
        "allocations":  allocation_dict,
    })

    if model_trained and not doc["model_trained"]:
        await portfolios_col().update_one(
            {"_id": ObjectId(portfolio_id)},
            {"$set": {"model_trained": True, "status": "active"}},
        )

    return {
        "portfolio_id":  portfolio_id,
        "date":          datetime.now(timezone.utc),
        "capital":       capital,
        "allocations":   allocations,
        "model_trained": model_trained,
        "status":        doc.get("status", "active"),
    }


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

async def get_performance(portfolio_id: str, user_id: str) -> Dict:
    doc = await _get_portfolio_or_raise(portfolio_id, user_id)
    perf = await ml_service.compute_performance(doc["stocks"])
    return {"portfolio_id": portfolio_id, **perf}


# ---------------------------------------------------------------------------
# Rebalance
# ---------------------------------------------------------------------------

async def rebalance(portfolio_id: str, user_id: str) -> Dict:
    """
    Force a rebalance cycle:
    1. Trigger model retrain
    2. Fetch new weights
    3. Compute turnover vs last weights
    4. Apply transaction cost
    5. Persist record
    """
    doc = await _get_portfolio_or_raise(portfolio_id, user_id)
    stocks  = doc["stocks"]
    capital = doc["capital"]

    # Get old weights from latest history
    old_entry = await weights_history_col().find_one(
        {"portfolio_id": portfolio_id},
        sort=[("date", -1)],
    )
    old_weights = old_entry["weights"] if old_entry else {t: 1 / len(stocks) for t in stocks}

    # Retrain and get new weights
    await ml_service.retrain(stocks)
    allocations, model_trained = await ml_service.get_weights(stocks, capital)
    new_weights = {a["ticker"]: a["weight"] for a in allocations}

    # Turnover
    all_tickers = set(old_weights) | set(new_weights)
    turnover = sum(
        abs(new_weights.get(t, 0.0) - old_weights.get(t, 0.0))
        for t in all_tickers
    )
    cost_inr = turnover * float(os.getenv("COST_RATE", "0.001")) * capital

    # Persist
    now = datetime.now(timezone.utc)
    await rebalance_history_col().insert_one({
        "portfolio_id":      portfolio_id,
        "date":              now,
        "old_weights":       old_weights,
        "new_weights":       new_weights,
        "turnover":          turnover,
        "transaction_cost":  cost_inr / capital,
    })
    await portfolios_col().update_one(
        {"_id": ObjectId(portfolio_id)},
        {"$set": {"last_rebalanced": now, "model_trained": model_trained}},
    )
    await _log_transaction(portfolio_id, "rebalance", {
        "turnover": turnover, "cost_inr": cost_inr,
    })

    return {
        "message":             "Rebalance complete",
        "date":                now,
        "allocations":         allocations,
        "turnover":            round(turnover, 6),
        "transaction_cost_inr": round(cost_inr, 2),
    }


# ---------------------------------------------------------------------------
# Update capital
# ---------------------------------------------------------------------------

async def update_capital(portfolio_id: str, user_id: str, capital: float) -> Dict:
    await _get_portfolio_or_raise(portfolio_id, user_id)
    await portfolios_col().update_one(
        {"_id": ObjectId(portfolio_id)},
        {"$set": {"capital": capital}},
    )
    return {"message": "Capital updated", "capital": capital}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_portfolio_or_raise(portfolio_id: str, user_id: str) -> Dict:
    doc = await portfolios_col().find_one(
        {"_id": ObjectId(portfolio_id), "user_id": user_id}
    )
    if not doc:
        raise ValueError(f"Portfolio {portfolio_id} not found")
    return doc


async def _log_transaction(portfolio_id: str, tx_type: str, details: Dict) -> None:
    await transactions_col().insert_one({
        "portfolio_id": portfolio_id,
        "date":         datetime.now(timezone.utc),
        "type":         tx_type,
        "details":      details,
    })


def _fmt(doc: Optional[Dict]) -> Optional[Dict]:
    """Convert MongoDB doc to JSON-serializable dict."""
    if not doc:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


import os
