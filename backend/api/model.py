"""
Model API — retrain, status, metrics endpoints.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.api.auth import get_current_user
from backend.database.models import UserOut
from backend.database.mongo import model_metrics_col, portfolios_col
from backend.services import ml_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/retrain")
async def retrain_model(
    portfolio_id: str,
    user: UserOut = Depends(get_current_user),
):
    """
    POST /model/retrain?portfolio_id=...

    Manually trigger model retraining for a portfolio's stock set.
    Returns immediately — training runs in background.
    Poll GET /model/status to check progress.
    """
    doc = await portfolios_col().find_one(
        {"_id": __import__("bson").ObjectId(portfolio_id), "user_id": user.id}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    await ml_service.retrain(doc["stocks"])
    return {
        "message": "Model retraining started",
        "stocks":  doc["stocks"],
        "status":  "training",
    }


@router.get("/status")
async def model_status(user: UserOut = Depends(get_current_user)):
    """Return current ML model training status."""
    return await ml_service.get_status()


@router.get("/metrics")
async def model_metrics(
    portfolio_id: str,
    limit: int = 10,
    user: UserOut = Depends(get_current_user),
):
    """Return the last N model metric records for a portfolio."""
    cursor = model_metrics_col().find(
        {"portfolio_id": portfolio_id},
        sort=[("date", -1)],
        limit=limit,
    )
    docs = await cursor.to_list(length=limit)
    for d in docs:
        d["id"] = str(d.pop("_id"))
    return docs
