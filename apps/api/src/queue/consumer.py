"""Background worker process — consumes tasks from RabbitMQ queues."""
from __future__ import annotations
import json
from datetime import date
from typing import Any
import aio_pika
from src.queue.rabbitmq_client import get_rabbitmq_connection
from src.metrics import RABBITMQ_TASKS_CONSUMED
import structlog

logger = structlog.get_logger(__name__)

async def handle_scrape_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Process a scrape task."""
    async with message.process():
        try:
            payload: dict[str, Any] = json.loads(message.body)
            market = str(payload["market"])
            trade_date = date.fromisoformat(str(payload["date"]))
            logger.info("scrape_task_received", market=market, date=trade_date.isoformat(), step="queue")
            
            # TODO: Implement pipeline.run(trade_date)
            
            RABBITMQ_TASKS_CONSUMED.labels(queue="bs.scrape", status="success").inc()
        except Exception as error:
            logger.error("scrape_task_failed", error=str(error), step="queue")
            RABBITMQ_TASKS_CONSUMED.labels(queue="bs.scrape", status="error").inc()
            raise

async def handle_experiment_task(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    """Process an experiment task."""
    async with message.process():
        try:
            payload: dict[str, Any] = json.loads(message.body)
            logger.info("experiment_task_received", payload=payload, step="queue")
            
            # TODO: Implement experiment runner
            
            RABBITMQ_TASKS_CONSUMED.labels(queue="bs.experiment", status="success").inc()
        except Exception as error:
            logger.error("experiment_task_failed", error=str(error), step="queue")
            RABBITMQ_TASKS_CONSUMED.labels(queue="bs.experiment", status="error").inc()
            raise

async def start_consumers() -> None:
    """Start consuming from both queues — called from main.py on startup."""
    connection = await get_rabbitmq_connection()
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    # Declare exchanges and queues to ensure they exist
    exchange = await channel.declare_exchange("bs.tasks", aio_pika.ExchangeType.DIRECT, durable=True)
    
    scrape_queue = await channel.declare_queue("bs.scrape", durable=True)
    await scrape_queue.bind(exchange, routing_key="scrape")
    
    experiment_queue = await channel.declare_queue("bs.experiment", durable=True)
    await experiment_queue.bind(exchange, routing_key="experiment")

    await scrape_queue.consume(handle_scrape_task)
    await experiment_queue.consume(handle_experiment_task)
    logger.info("consumers_started", step="init")
