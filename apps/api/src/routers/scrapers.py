"""API router for scrapers."""

from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.database.repository import list_scrape_runs
from src.queue.publisher import publish_scrape_task

router = APIRouter(prefix="/api/v1/scrapers", tags=["scrapers"])
logger = structlog.get_logger(__name__)


@router.post("/run")
async def run_scraper(
    market: str,
    trade_date: date | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Trigger a scraper task."""
    target_date = trade_date or date.today()
    logger.info(
        "scraper_run_requested",
        market=market,
        date=target_date.isoformat(),
        user_id=current_user.get("id"),
    )

    await publish_scrape_task(market, target_date)

    return {"status": "queued", "market": market, "date": target_date.isoformat()}


@router.get("/runs")
async def list_runs(
    limit: int = 50,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """List recent scrape runs."""
    return await list_scrape_runs(limit=limit)
