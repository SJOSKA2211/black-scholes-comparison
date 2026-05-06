"""Compressed Redis cache utility — stores serialized objects as compressed binary."""

from __future__ import annotations
import json
from functools import lru_cache
from typing import Any
import redis.asyncio as aioredis
from src.config import get_settings
from src.utils.compression import compress_data, decompress_data
import structlog

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_binary_redis() -> aioredis.Redis:
    """Return a cached async Redis client configured for binary data."""
    settings = get_settings()
    # Note: decode_responses=False for binary data
    client = aioredis.from_url(
        settings.redis_url,
        password=settings.redis_password,
        encoding="utf-8",
        decode_responses=False,
        socket_connect_timeout=5,
    )
    return client


def reset_binary_redis() -> None:
    """Reset the binary Redis client singleton."""
    get_binary_redis.cache_clear()


async def set_compressed(key: str, value: Any, expire: int = 3600) -> None:
    """Serialize, compress, and store an object in Redis."""
    redis = get_binary_redis()
    serialized = json.dumps(value).encode("utf-8")
    compressed = compress_data(serialized)
    await redis.setex(key, expire, compressed)
    logger.debug("compressed_cache_set", key=key, original_size=len(serialized), compressed_size=len(compressed))


async def get_compressed(key: str) -> Any | None:
    """Retrieve, decompress, and deserialize an object from Redis."""
    redis = get_binary_redis()
    compressed = await redis.get(key)
    if compressed is None:
        return None
    
    decompressed = decompress_data(compressed)
    return json.loads(decompressed.decode("utf-8"))
