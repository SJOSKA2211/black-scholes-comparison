"""Router for managing numerical experiments and grid runs."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_experiments, get_experiments_by_method
from src.queue.publisher import publish_experiment_task

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/run")
async def run_experiment(
    params: dict[str, Any], current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
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
        raise HTTPException(status_code=500, detail="Failed to submit experiment") from e


@router.get("/results")
async def get_results(
    method_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
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
        raise HTTPException(status_code=500, detail="Failed to fetch results") from e
