"""Router for managing market data scrapers."""

from __future__ import annotations

import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_scrape_runs
from src.queue.publisher import publish_scrape_task

router = APIRouter(prefix="/scrapers", tags=["Scrapers"])
logger = structlog.get_logger(__name__)


@router.post("/trigger")
async def trigger_scraper(
    market: str = Query(..., pattern="^(spy|nse)$"),
    trade_date: datetime.date | None = Query(None),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Manually triggers a scraper run via the message queue."""
    if trade_date is None:
        trade_date = datetime.date.today()

    try:
        await publish_scrape_task(market, trade_date)
        logger.info(
            "scraper_triggered",
            market=market,
            date=trade_date.isoformat(),
            user_id=current_user["id"],
            step="router",
        )
        return {"message": f"Scraper for {market} triggered", "status": "queued"}
    except Exception as error:
        logger.error("scraper_trigger_failed", error=str(error), market=market, step="router")
        raise HTTPException(status_code=500, detail="Failed to trigger scraper") from error


@router.get("/runs")
async def get_runs(
    limit: int = Query(20, ge=1, le=100), current_user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """Retrieves the history of scraper runs."""
    try:
        runs = await get_scrape_runs(limit=limit)
        return runs
    except Exception as error:
        logger.error("scraper_runs_fetch_failed", error=str(error), step="router")
        raise HTTPException(status_code=500, detail="Failed to fetch scraper runs") from error
