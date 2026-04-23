"""Background worker process — consumes tasks from RabbitMQ queues."""

from __future__ import annotations

import json
from datetime import date

import structlog
from aio_pika.abc import AbstractIncomingMessage

from src.data.pipeline import DataPipeline
from src.task_queues.rabbitmq_client import get_rabbitmq_connection

logger = structlog.get_logger(__name__)


async def handle_scrape_task(message: AbstractIncomingMessage) -> None:
    """Process a market data scrape task."""
    async with message.process():
        payload = json.loads(message.body)
        market = payload["market"]
        trade_date = date.fromisoformat(payload["date"])

        logger.info(
            "scrape_task_received", market=market, date=trade_date.isoformat(), step="queue"
        )

        # Create pipeline instance and run
        # Note: Pipeline ID is generated here for tracking
        import uuid

        run_id = str(uuid.uuid4())
        pipeline = DataPipeline(run_id=run_id, market=market)

        try:
            await pipeline.run(trade_date)
            logger.info("scrape_task_success", market=market, run_id=run_id, step="queue")
        except Exception as error:
            logger.error("scrape_task_failed", market=market, error=str(error), step="queue")
            # In production, we might want to dead-letter or retry here
            raise


async def handle_experiment_task(message: AbstractIncomingMessage) -> None:
    """Process an experiment grid run task."""
    from scripts.run_experiments import run_experiments

    async with message.process():
        payload = json.loads(message.body)
        logger.info("experiment_task_received", payload=payload, step="queue")

        try:
            await run_experiments(payload)
            logger.info("experiment_task_success", step="queue")
        except Exception as error:
            logger.error("experiment_task_failed", error=str(error), step="queue")
            # Log failure but process() handles ack/nack depending on robustness needs
            raise


async def start_consumers() -> None:
    """
    Start consuming from both queues — called from main.py lifespan.
    Adheres to Section 8.4 of the Production Final mandate.
    """
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()

        # Prefetch 1 ensures fair dispatch (Section 8.4)
        await channel.set_qos(prefetch_count=1)

        # Ensure queues exist
        scrape_queue = await channel.declare_queue("bs.scrape", durable=True)
        experiment_queue = await channel.declare_queue("bs.experiment", durable=True)

        # Start consuming
        await scrape_queue.consume(handle_scrape_task)
        await experiment_queue.consume(handle_experiment_task)

        logger.info("consumers_active", queues=["bs.scrape", "bs.experiment"], step="init")
    except Exception as error:
        logger.error("consumers_start_failed", error=str(error), step="init")
        # Do not raise here to allow API to start even if RabbitMQ is transiently down
        # Robustness handled by connect_robust in rabbitmq_client.py
