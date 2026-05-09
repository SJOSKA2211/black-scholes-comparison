"""Script to run grid experiments."""

from __future__ import annotations

from typing import Any

import structlog

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParameters, OptionType
from src.queue.publisher import publish_experiment_task

logger = structlog.get_logger(__name__)


async def run_experiments(payload: dict[str, Any]) -> None:
    """Run experiments based on the payload (actual execution)."""
    logger.info("experiments_execution_started", payload=payload)

    # Example: Run analytical pricing for a range of strikes
    strikes = payload.get("params", {}).get("strikes", [100.0, 110.0, 120.0])
    for strike in strikes:
        params = OptionParameters(
            underlying_price=100.0,
            strike_price=strike,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type=OptionType.CALL,
        )
        engine = BlackScholesAnalytical()
        price = engine.price(params)
        logger.info("experiment_step_completed", strike=strike, price=price)

    logger.info("experiments_execution_finished")


async def main() -> None:
    """CLI entry point for running a default experiment set via RabbitMQ."""
    default_payload = {"type": "grid_search", "params": {"strikes": [100.0, 110.0, 120.0]}}
    await publish_experiment_task(default_payload)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
