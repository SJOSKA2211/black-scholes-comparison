"""Integration tests for live infrastructure."""

import asyncio

import pytest

from src.cache.redis_client import get_redis
from src.queue.rabbitmq_client import get_rabbitmq_connection
from src.storage.minio_client import get_minio


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_reachability() -> None:
    """Test Redis connection and basic operation."""
    redis = get_redis()
    await redis.set("test_key", "test_value")
    val = await redis.get("test_key")
    assert val == "test_value"
    await redis.delete("test_key")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rabbitmq_reachability() -> None:
    """Test RabbitMQ connection and exchange creation."""
    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        exchange = await channel.declare_exchange("test.exchange", type="topic")
        assert exchange is not None
        await exchange.delete()


@pytest.mark.integration
def test_minio_reachability() -> None:
    """Test MinIO reachability and bucket listing."""
    client = get_minio()
    buckets = client.list_buckets()
    assert isinstance(buckets, list)
