"""Cache-aside decorator for FastAPI route handlers."""

from __future__ import annotations

import functools
import json
from collections.abc import Callable
from typing import Any

import structlog

from src.cache.redis_client import get_redis

logger = structlog.get_logger(__name__)


def cache_response(key_prefix: str, ttl_seconds: int = 300) -> Callable[..., Any]:
    """
    Decorator: check Redis for cached JSON response; compute and cache on miss.
    Cache key: f"{key_prefix}:{hash(str(sorted(kwargs.items())))}"
    TTL default: 300 seconds (5 minutes).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> object:
            redis = get_redis()
            import hashlib

            # Create a deterministic cache key from sorted kwargs
            key_parts = str(sorted(kwargs.items())).encode()
            cache_key = f"{key_prefix}:{hashlib.sha256(key_parts).hexdigest()}"

            try:
                cached = await redis.get(cache_key)
                if cached is not None:
                    logger.debug("cache_hit", key=cache_key, step="cache")
                    return json.loads(cached)
            except Exception as error:
                logger.warning("cache_lookup_failed", error=str(error), step="cache")

            result = await func(*args, **kwargs)

            try:
                # Handle Pydantic models (Section 4.1)
                from pydantic import BaseModel
                if isinstance(result, BaseModel):
                    dumped = result.model_dump()
                else:
                    dumped = result
                await redis.setex(cache_key, ttl_seconds, json.dumps(dumped, default=str))
                logger.debug("cache_miss_stored", key=cache_key, step="cache")
            except Exception as error:
                logger.warning("cache_store_failed", error=str(error), step="cache")

            return result

        return wrapper

    return decorator
