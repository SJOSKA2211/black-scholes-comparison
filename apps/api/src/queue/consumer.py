"""Background worker process — consumes tasks from RabbitMQ queues."""

from __future__ import annotations

import json

import aio_pika
import structlog

from src.data.pipeline import DataPipeline
from src.queue.rabbitmq_client import get_rabbitmq_connection

logger = structlog.get_logger(__name__)


async def handle_scrape_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Handle incoming market data scraping tasks."""
    async with message.process():
        payload = json.loads(message.body)
        run_id = payload.get("run_id", "unknown")
        market = payload.get("market", "unknown")

        logger.info("scrape_task_received", market=market, run_id=run_id, step="queue")

        # Instantiate pipeline for this run
        pipeline = DataPipeline(run_id=run_id)

        # If payload contains rows, process them
        if "rows" in payload:
            await pipeline.process_rows(payload["rows"])
        else:
            logger.warning("scrape_task_empty", run_id=run_id)


async def handle_experiment_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Handle incoming numerical experiment tasks."""
    async with message.process():
        payload = json.loads(message.body)
        logger.info("experiment_task_received", payload=payload, step="queue")
        # TODO: Implement experiment runner integration: await run_experiments(payload)


async def start_consumers() -> None:
    """Start consuming from both queues — called from main.py on startup."""
    try:
        connection = await get_rabbitmq_connection()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declare queues to ensure they exist
        scrape_queue = await channel.declare_queue("bs.scrape", durable=True)
        experiment_queue = await channel.declare_queue("bs.experiment", durable=True)

        await scrape_queue.consume(handle_scrape_task)
        await experiment_queue.consume(handle_experiment_task)

        logger.info("consumers_started", step="init")
    except Exception as e:
        logger.error("consumer_startup_failed", error=str(e), step="init")
