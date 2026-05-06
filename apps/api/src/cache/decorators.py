"""Cache-aside decorator for FastAPI endpoints."""
from __future__ import annotations
import json
import functools
from typing import Any, Callable, TypeVar, cast
from src.cache.redis_client import get_redis
from src.metrics import REDIS_CACHE_HITS, REDIS_CACHE_MISSES
import structlog

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

def cache_response(key_prefix: str, ttl_seconds: int = 300) -> Callable[[F], F]:
    """Decorator to cache function results in Redis."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            redis = get_redis()
            # Generate cache key from prefix and arguments
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            try:
                cached_data = await redis.get(cache_key)
                if cached_data:
                    REDIS_CACHE_HITS.labels(endpoint=key_prefix).inc()
                    return json.loads(cached_data)
            except Exception as error:
                logger.warning("cache_lookup_failed", error=str(error))

            # Cache miss: execute function
            result = await func(*args, **kwargs)
            
            try:
                await redis.setex(cache_key, ttl_seconds, json.dumps(result))
                REDIS_CACHE_MISSES.labels(endpoint=key_prefix).inc()
            except Exception as error:
                logger.warning("cache_storage_failed", error=str(error))
                
            return result
        return cast(F, wrapper)
    return decorator
