"""Compressed Redis cache utility."""

import json
from typing import Any, Optional

import redis.asyncio as aioredis

from src.config import get_settings
from src.utils.compression import compress_data, decompress_data

_binary_redis_client: Optional[aioredis.Redis] = None


def get_binary_redis() -> aioredis.Redis:
    """Return a Redis client that handles binary data (no auto-decoding)."""
    global _binary_redis_client
    if _binary_redis_client is None:
        settings = get_settings()
        _binary_redis_client = aioredis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=False,  # Crucial for binary/compressed data
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _binary_redis_client


def reset_binary_redis() -> None:
    """Reset the global binary Redis client (used for tests)."""
    global _binary_redis_client
    _binary_redis_client = None


async def set_compressed(key: str, value: object, expire: int = 3600) -> None:
    """Serialize, compress, and store a value in Redis."""
    redis = get_binary_redis()

    # Serialize to JSON then compress
    json_data = json.dumps(value)
    compressed = compress_data(json_data, method="zlib")

    await redis.set(key, compressed, ex=expire)


async def get_compressed(key: str) -> Any | None:  # noqa: ANN401
    """Retrieve, decompress, and deserialize a value from Redis."""
    redis = get_binary_redis()

    compressed = await redis.get(key)
    if compressed is None:
        return None

    json_data = decompress_data(compressed, as_str=True, method="zlib")
    return json.loads(json_data)
