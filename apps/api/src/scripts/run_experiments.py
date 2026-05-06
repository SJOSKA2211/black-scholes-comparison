"""Script to run grid experiments."""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


async def run_experiments(payload: dict[str, Any]) -> None:
    """Run experiments based on the payload."""
    logger.info("experiments_started", payload=payload)
    # Add to queue for processing
    from src.queue.publisher import publish_experiment_task
    await publish_experiment_task(payload)

async def main() -> None:
    """CLI entry point for running a default experiment set."""
    default_payload = {"type": "grid_search", "params": {"steps": [100, 200, 500]}}
    await run_experiments(default_payload)
