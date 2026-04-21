from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.auth.dependencies import get_current_user
import uuid

router = APIRouter()

class ScrapeTrigger(BaseModel):
    market: str
    date: Optional[str] = None

@router.post("/scrapers/trigger")
async def trigger_scraper(
    trigger: ScrapeTrigger,
    current_user: dict = Depends(get_current_user)
):
    """Triggers an asynchronous scrape job."""
    # Check for admin role (placeholder)
    job_id = str(uuid.uuid4())
    return {"job_id": job_id, "status": "queued"}

@router.get("/scrapers/runs")
async def get_scrape_runs(
    market: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Returns recent scrape runs."""
    return []
