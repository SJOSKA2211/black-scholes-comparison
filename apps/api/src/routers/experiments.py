"""Router for managing numerical experiments and grid runs."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.auth.dependencies import get_current_user
from src.database.repository import get_experiments, get_experiments_by_method
from src.queue.publisher import publish_experiment_task
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.post("/run")
async def run_experiment(
    params: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Submits an experiment task to the message queue.
    The payload includes pricing parameters and methods to test.
    """
    try:
        # Add user context to params
        params["user_id"] = current_user["id"]
        await publish_experiment_task(params)
        logger.info("experiment_submitted", user_id=current_user["id"], step="router")
        return {"message": "Experiment submitted successfully", "status": "queued"}
    except Exception as e:
        logger.error("experiment_submission_failed", error=str(e), step="router")
        raise HTTPException(status_code=500, detail="Failed to submit experiment")

@router.get("/results")
async def get_results(
    method_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Retrieves experiment results from the database."""
    try:
        if method_type:
            results = await get_experiments_by_method(method_type)
        else:
            # use get_experiments
            results_dict = await get_experiments(page_size=limit)
            results = results_dict.get("data", [])
        return results
    except Exception as e:
        logger.error("results_fetch_failed", error=str(e), step="router")
        raise HTTPException(status_code=500, detail="Failed to fetch results")
