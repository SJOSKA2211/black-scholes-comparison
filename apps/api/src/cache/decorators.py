"""Cache-aside decorator for FastAPI route handlers."""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from typing import Any

import structlog

from src.cache.redis_client import get_redis

logger = structlog.get_logger(__name__)


def cache_response(key_prefix: str, ttl_seconds: int = 300) -> Callable:
    """
    Decorator: check Redis for cached JSON response; compute and cache on miss.
    Cache key: f"{key_prefix}:{hash(str(sorted(kwargs.items())))}"
    TTL default: 300 seconds (5 minutes).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            redis = get_redis()
            # Construct a stable cache key based on sorted keyword arguments
            items = sorted(kwargs.items())
            cache_key = f"{key_prefix}:{hash(str(items))}"

            try:
                cached = await redis.get(cache_key)
                if cached is not None:
                    logger.debug("cache_hit", key=cache_key, step="cache")
                    return json.loads(cached)
            except Exception as e:
                logger.warning("cache_lookup_failed", error=str(e), key=cache_key)

            result = await func(*args, **kwargs)

            try:
                await redis.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
                logger.debug("cache_miss_stored", key=cache_key, step="cache")
            except Exception as e:
                logger.warning("cache_store_failed", error=str(e), key=cache_key)

            return result

        return wrapper

    return decorator
