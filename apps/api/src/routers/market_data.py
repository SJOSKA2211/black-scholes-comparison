"""API router for market data."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends
from src.auth.dependencies import get_current_user
import structlog

router = APIRouter(prefix="/api/v1/market-data", tags=["market_data"])
logger = structlog.get_logger(__name__)

@router.get("/")
async def get_market_data(
    symbol: str = "SPY",
    current_user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """Fetch market data for a symbol."""
    logger.info("market_data_requested", symbol=symbol, user_id=current_user.get("id"))
    # Placeholder for repository call
    return []
