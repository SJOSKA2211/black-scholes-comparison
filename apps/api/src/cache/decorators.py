"""Cache-aside decorator for FastAPI route handlers."""
from __future__ import annotations
import json
import functools
from typing import Callable, Any
from src.cache.redis_client import get_redis
import structlog
 
logger = structlog.get_logger(__name__)
 
def cache_response(key_prefix: str, ttl_seconds: int = 300) -> Callable:
    """
    Decorator: check Redis for cached JSON response; compute and cache on miss.
    Cache key: f"{key_prefix}:{hash(str(sorted(kwargs.items())))}"
    TTL default: 300 seconds (5 minutes).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            redis = get_redis()
            cache_key = f"{key_prefix}:{hash(str(sorted(kwargs.items())))}"
            cached = await redis.get(cache_key)
            if cached is not None:
                logger.debug("cache_hit", key=cache_key, step="cache")
                return json.loads(cached)
            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl_seconds, json.dumps(result, default=str))
            logger.debug("cache_miss_stored", key=cache_key, step="cache")
            return result
        return wrapper
    return decorator
