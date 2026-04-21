"""RabbitMQ async client — connection pool with aio-pika."""
from __future__ import annotations
import aio_pika
from src.config import get_settings
import structlog
 
logger = structlog.get_logger(__name__)
 
async def get_rabbitmq_connection() -> aio_pika.abc.AbstractConnection:
    """Create and return an aio-pika async connection."""
    settings = get_settings()
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url,
        timeout=10,
        reconnect_interval=5,
    )
    logger.info("rabbitmq_connected", step="init")
    return connection
