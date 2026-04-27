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
    Decorator: check Redis for cached compressed JSON response; compute and cache on miss.
    Uses src.cache.compressed_cache for binary-safe zlib compression.
    Cache key: f"{key_prefix}:{hash(str(sorted(kwargs.items())))}"
    TTL default: 300 seconds (5 minutes).
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: object, **kwargs: object) -> object:
            from src.cache.compressed_cache import get_compressed, set_compressed
            import hashlib

            # Create a deterministic cache key from args and sorted kwargs
            key_parts = f"{args}:{sorted(kwargs.items())}".encode()
            cache_key = f"{key_prefix}:{hashlib.sha256(key_parts).hexdigest()}"

            try:
                cached = await get_compressed(cache_key)
                if cached is not None:
                    logger.debug("cache_hit", key=cache_key, step="cache")
                    return cached
            except Exception as error:
                logger.warning("cache_lookup_failed", error=str(error), step="cache")

            result = await func(*args, **kwargs)

            try:
                # Handle Pydantic models (Section 4.1)
                from pydantic import BaseModel

                dumped = result.model_dump() if isinstance(result, BaseModel) else result
                await set_compressed(cache_key, dumped, expire=ttl_seconds)
                logger.debug("cache_miss_stored", key=cache_key, step="cache")
            except Exception as error:
                logger.warning("cache_store_failed", error=str(error), step="cache")

            return result

        return wrapper

    return decorator
