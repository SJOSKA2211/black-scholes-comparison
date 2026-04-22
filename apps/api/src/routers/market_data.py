"""Router for accessing historical and real-time market data."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_market_data

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/")
async def get_market_quotes(
    source: str = Query("synthetic", pattern="^(synthetic|spy|nse)$"),
    trade_date: Optional[datetime.date] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Retrieves market data quotes based on source and date."""
    try:
        data = await get_market_data(source=source, trade_date=trade_date, limit=limit)
        return data
    except Exception as e:
        logger.error("market_data_fetch_failed", error=str(e), source=source, step="router")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")
