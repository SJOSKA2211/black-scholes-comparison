"""RabbitMQ async client — connection pool with aio-pika."""

from __future__ import annotations

import aio_pika
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)

_connection: aio_pika.abc.AbstractConnection | None = None


async def get_rabbitmq_connection() -> aio_pika.abc.AbstractConnection:
    """Create and return an aio-pika async connection (singleton)."""
    global _connection
    if _connection is None or _connection.is_closed:
        settings = get_settings()
        _connection = await aio_pika.connect_robust(
            settings.rabbitmq_url,
            timeout=10,
            reconnect_interval=5,
        )
        logger.info("rabbitmq_connected", step="init")
    return _connection


async def close_rabbitmq_connection() -> None:
    """Close the global RabbitMQ connection."""
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        _connection = None
        logger.info("rabbitmq_disconnected", step="teardown")
