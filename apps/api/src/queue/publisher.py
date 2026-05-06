"""Publish scrape and experiment tasks to RabbitMQ."""

from __future__ import annotations

import json
from datetime import date

import aio_pika
import structlog

from src.queue.rabbitmq_client import get_rabbitmq_connection

logger = structlog.get_logger(__name__)


async def publish_scrape_task(market: str, trade_date: date) -> None:
    """Publish a scrape job to the bs.scrape queue."""
    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        exchange = await channel.get_exchange("bs.tasks")
        body = json.dumps({"market": market, "date": trade_date.isoformat()}).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="scrape",
        )
    logger.info("task_published", market=market, date=trade_date.isoformat(), step="queue", rows=0)


async def publish_experiment_task(params: dict) -> None:
    """Publish an experiment grid run to the bs.experiment queue."""
    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        exchange = await channel.get_exchange("bs.tasks")
        body = json.dumps(params).encode()
        await exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="experiment",
        )
    logger.info("experiment_task_published", step="queue", rows=0)
