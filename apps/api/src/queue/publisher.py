"""Publish scrape and experiment tasks to RabbitMQ."""
from __future__ import annotations
import json
from datetime import date
from typing import Any
import aio_pika
from src.queue.rabbitmq_client import get_rabbitmq_connection
from src.metrics import RABBITMQ_TASKS_PUBLISHED
import structlog

logger = structlog.get_logger(__name__)

async def publish_scrape_task(market: str, trade_date: date) -> None:
    """Publish a scrape job to the bs.scrape queue."""
    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange("bs.tasks", aio_pika.ExchangeType.DIRECT, durable=True)
        
        # Ensure queue exists and is bound
        queue = await channel.declare_queue("bs.scrape", durable=True)
        await queue.bind(exchange, routing_key="scrape")
        
        body = json.dumps({"market": market, "date": trade_date.isoformat()}).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="scrape",
        )
        RABBITMQ_TASKS_PUBLISHED.labels(queue="bs.scrape").inc()
        
    logger.info("task_published", market=market, date=trade_date.isoformat(), step="queue")

async def publish_experiment_task(params: dict[str, Any]) -> None:
    """Publish an experiment grid run to the bs.experiment queue."""
    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange("bs.tasks", aio_pika.ExchangeType.DIRECT, durable=True)
        
        # Ensure queue exists and is bound
        queue = await channel.declare_queue("bs.experiment", durable=True)
        await queue.bind(exchange, routing_key="experiment")
        
        body = json.dumps(params).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="experiment",
        )
        RABBITMQ_TASKS_PUBLISHED.labels(queue="bs.experiment").inc()
        
    logger.info("experiment_task_published", step="queue")
