"""RabbitMQ async client — connection pool with aio-pika."""

from __future__ import annotations

import aio_pika
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)

# Global connection instance
_connection: aio_pika.abc.AbstractConnection | None = None


async def get_rabbitmq_connection() -> aio_pika.abc.AbstractConnection:
    """
    Create and return a robust async connection to RabbitMQ.
    Implements Section 8.2 of the Production Final mandate.
    """
    global _connection
    
    if _connection is None or _connection.is_closed:
        settings = get_settings()
        try:
            _connection = await aio_pika.connect_robust(
                settings.rabbitmq_url,
                timeout=5,
                reconnect_interval=10,
            )
            logger.info("rabbitmq_connected", url=settings.rabbitmq_url.split("@")[-1], step="init")
        except Exception as error:
            logger.error("rabbitmq_connection_failed", error=str(error), step="init")
            # We raise here but start_consumers() catches it
            raise

    return _connection


def reset_rabbitmq() -> None:
    """Reset the global RabbitMQ connection (used for tests)."""
    global _connection
    _connection = None


async def close_rabbitmq_connection() -> None:
    """Close the global RabbitMQ connection during shutdown."""
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        logger.info("rabbitmq_connection_closed", step="shutdown")
