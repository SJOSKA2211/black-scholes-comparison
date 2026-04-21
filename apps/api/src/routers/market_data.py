from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user
from src.database import repository

router = APIRouter()


@router.get("/market-data/{source}")
async def get_market_data(
    source: str,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user: dict = Depends(get_current_user),
):
    """Returns market data for SPY or NSE."""
    data = await repository.get_market_data(source, from_date, to_date)
    return {"items": data, "total": len(data)}
