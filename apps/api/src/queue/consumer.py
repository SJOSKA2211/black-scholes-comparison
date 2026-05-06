"""Background worker process — consumes tasks from RabbitMQ queues."""

from __future__ import annotations

import json
from datetime import date

import aio_pika
import structlog

from src.data.pipeline import get_pipeline
from src.queue.rabbitmq_client import get_rabbitmq_connection

logger = structlog.get_logger(__name__)


async def handle_scrape_task(message: aio_pika.IncomingMessage) -> None:
    """Process a market data scrape task."""
    async with message.process():
        payload = json.loads(message.body)
        market = payload["market"]
        trade_date = date.fromisoformat(payload["date"])
        logger.info("scrape_task_received", market=market, step="queue", rows=0)
        pipeline = get_pipeline(market)
        await pipeline.run(trade_date)


async def handle_experiment_task(message: aio_pika.IncomingMessage) -> None:
    """Process an experiment grid run task."""
    async with message.process():
        payload = json.loads(message.body)
        logger.info("experiment_task_received", step="queue", rows=0)
        # TODO: Implement run_experiments() once analysis module is ready
        # This is a placeholder call as per the mandate's logic in Section 8.4
        from src.scripts.run_experiments import run_experiments

        await run_experiments(payload)


async def start_consumers() -> None:
    """Start consuming from both queues — called from main.py on startup."""
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    # 1. Declare exchanges
    exchange = await channel.declare_exchange("bs.tasks", type=aio_pika.ExchangeType.DIRECT, durable=True)

    # 2. Declare queues
    scrape_queue = await channel.declare_queue("bs.scrape", durable=True)
    experiment_queue = await channel.declare_queue("bs.experiment", durable=True)

    # 3. Bind queues
    await scrape_queue.bind(exchange, routing_key="scrape")
    await experiment_queue.bind(exchange, routing_key="experiment")

    # 4. Start consuming
    await scrape_queue.consume(handle_scrape_task)
    await experiment_queue.consume(handle_experiment_task)
    logger.info("consumers_started", step="init", rows=0)
