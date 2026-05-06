"""Background worker process — consumes tasks from RabbitMQ queues."""

from __future__ import annotations

import json
from datetime import date

import aio_pika
import structlog

from src.data.pipeline import get_pipeline
from src.queue.rabbitmq_client import get_rabbitmq_connection

logger = structlog.get_logger(__name__)


async def handle_scrape_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body)
        market = payload["market"]
        trade_date = date.fromisoformat(payload["date"])
        logger.info("scrape_task_received", market=market, step="queue", rows=0)
        pipeline = get_pipeline(market)
        await pipeline.run(trade_date)


async def handle_experiment_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        logger.info("experiment_task_received", step="queue", rows=0)
        # Calls run_experiments() with payload parameters
        # Note: Implementation for run_experiments will be in src/scripts/run_experiments.py
        # or similar. For now, following the mandate's block.


async def start_consumers() -> None:
    """Start consuming from both queues — called from main.py on startup."""
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    scrape_queue = await channel.get_queue("bs.scrape")
    experiment_queue = await channel.get_queue("bs.experiment")

    await scrape_queue.consume(handle_scrape_task)
    await experiment_queue.consume(handle_experiment_task)
    logger.info("consumers_started", step="init", rows=0)
