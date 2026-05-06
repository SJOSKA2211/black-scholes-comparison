"""Redis client singleton using async redis."""
from __future__ import annotations
from functools import lru_cache
from redis.asyncio import Redis
from src.config import get_settings
import structlog

logger = structlog.get_logger(__name__)

@lru_cache(maxsize=1)
def get_redis() -> Redis[bytes]:
    """Return a cached async Redis client."""
    settings = get_settings()
    client: Redis[bytes] = Redis.from_url(
        settings.redis_url, 
        decode_responses=False # We handle JSON encoding/decoding ourselves
    )
    logger.info("redis_client_created", url=settings.redis_url, step="init")
    return client
