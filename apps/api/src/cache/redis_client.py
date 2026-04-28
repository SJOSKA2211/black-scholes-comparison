from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)

_redis_client: aioredis.Redis[Any] | None = None


def get_redis() -> aioredis.Redis[Any] | None:
    """Return a cached async Redis client or None if disabled."""
    global _redis_client
    settings = get_settings()

    if _redis_client is None:
        try:
            if settings.redis_cluster_enabled:
                from redis.asyncio.cluster import RedisCluster
                _redis_client = RedisCluster.from_url(
                    settings.redis_url,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                )
                logger.info("redis_cluster_client_created", step="init")
            else:
                _redis_client = aioredis.from_url(
                    settings.redis_url,
                    password=settings.redis_password,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                logger.info("redis_client_created", url=settings.redis_url.split("@")[-1], step="init")
        except Exception as e:
            logger.error("redis_client_init_failed", error=str(e), url=settings.redis_url.split("@")[-1])
            raise
    return _redis_client


def reset_redis() -> None:
    """Reset the global Redis client (used for tests)."""
    global _redis_client
    _redis_client = None
