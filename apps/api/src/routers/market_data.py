"""Router for accessing historical and real-time market data."""

import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_market_data

router = APIRouter(prefix="/market-data", tags=["Market Data"])
logger = structlog.get_logger(__name__)


@router.get("/")
async def get_market_quotes(
    source: str = Query("synthetic", pattern="^(synthetic|spy|nse)$"),
    trade_date: datetime.date | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Retrieves market data quotes based on source and date."""
    try:
        data = await get_market_data(source=source, trade_date=trade_date, limit=limit)
        return data
    except Exception as error:
        logger.error("market_data_fetch_failed", error=str(error), source=source, step="router")
        raise HTTPException(status_code=500, detail="Failed to fetch market data") from error
