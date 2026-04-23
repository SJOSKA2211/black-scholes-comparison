"""Redis client singleton — cache, session store, and pub/sub for WebSockets."""

from __future__ import annotations

from functools import lru_cache

import redis.asyncio as aioredis
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_redis() -> aioredis.Redis[str]:
    """Return a cached async Redis client."""
    settings = get_settings()
    client = aioredis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    logger.info("redis_client_created", url=settings.redis_url, step="init")
    return client
