"""API router for research experiments."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.database.repository import list_method_results
from src.queue.publisher import publish_experiment_task

router = APIRouter(prefix="/api/v1/experiments", tags=["experiments"])
logger = structlog.get_logger(__name__)


@router.post("/run")
async def run_experiment(
    params: dict[str, Any], current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """Trigger a grid experiment task."""
    logger.info("experiment_run_requested", user_id=current_user.get("id"))

    # Add user context to params
    params["user_id"] = current_user.get("id")
    await publish_experiment_task(params)

    return {"status": "queued", "message": "Experiment task has been published to the queue."}


@router.get("/results")
async def list_results(
    limit: int = 100,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """List recent experiment results."""
    results = await list_method_results(limit=limit)
    return {
        "items": results,
        "total": len(results),
        "has_next": False,  # Simplified pagination
    }
