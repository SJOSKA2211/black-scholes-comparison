"""Router for managing numerical experiments and grid runs."""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.auth.dependencies import get_current_user
from src.database.repository import Repository
from src.queue.publisher import publish_experiment_task

router = APIRouter(prefix="/experiments", tags=["Experiments"])
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
    except Exception as error:
        logger.error("experiment_submission_failed", error=str(error), step="router")
        raise HTTPException(status_code=500, detail="Failed to submit experiment") from error


@router.get("/results")
async def get_results(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Retrieves experiment results from the database."""
    repo = Repository()
    try:
        results = await repo.get_experiments(user_id=current_user["id"])
        return results
    except Exception as error:
        logger.error("results_fetch_failed", error=str(error), step="router")
        raise HTTPException(status_code=500, detail="Failed to fetch results") from error


@router.get("/results/{experiment_id}")
async def get_result_detail(
    experiment_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    """Retrieves specific experiment results by ID."""
    repo = Repository()
    try:
        result = await repo.get_experiment_by_id(experiment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Experiment result not found")
        return result
    except HTTPException:
        raise
    except Exception as error:
        logger.error(
            "experiment_detail_fetch_failed", error=str(error), id=experiment_id, step="router"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch experiment detail") from error
