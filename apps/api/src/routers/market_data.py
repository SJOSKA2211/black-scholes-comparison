"""Router for accessing historical and real-time market data."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.auth.dependencies import get_current_user
from src.database.repository import Repository

router = APIRouter(prefix="/market-data", tags=["Market Data"])
logger = structlog.get_logger(__name__)


@router.get("/")
async def get_market_quotes(
    option_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Retrieves market data quotes for a specific option."""
    repo = Repository()
    try:
        data = await repo.get_market_data(option_id=option_id)
        return data
    except Exception as error:
        logger.error(
            "market_data_fetch_failed", error=str(error), option_id=option_id, step="router"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch market data") from error
