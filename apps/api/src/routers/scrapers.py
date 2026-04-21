from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.database import repository
from src.scrapers.nse_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper

router = APIRouter()


class ScrapeTrigger(BaseModel):
    market: str
    date: Optional[str] = None


async def run_scraper_task(market: str, run_id: str):
    if market == "spy":
        scraper = SPYScraper(run_id)
    else:
        scraper = NSEScraper(run_id)
    await scraper.run()


@router.post("/scrapers/trigger")
async def trigger_scraper(
    trigger: ScrapeTrigger,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Triggers an asynchronous scrape job."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Only administrators can trigger scrapers"
        )
    run_id = await repository.create_scrape_run(
        trigger.market, triggered_by=current_user["id"]
    )
    background_tasks.add_task(run_scraper_task, trigger.market, run_id)
    return {"job_id": run_id, "status": "queued"}


@router.get("/scrapers/runs")
async def get_scrape_runs(
    market: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """Returns recent scrape runs."""
    return await repository.get_scrape_runs(limit=limit)
