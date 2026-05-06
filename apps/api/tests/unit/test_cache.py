"""Unit tests for the cache layer."""

import asyncio
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch

from src.cache.decorators import cache_response
from src.cache.redis_client import get_redis


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_hit_miss() -> None:
    """Test cache hit and miss cycles."""
    call_count = 0

    @cache_response("test_hit", ttl_seconds=10)
    async def mock_endpoint(val: int) -> dict[str, int]:
        nonlocal call_count
        call_count += 1
        return {"value": val}

    # 1. First call (miss)
    res1 = await mock_endpoint(val=10)
    assert res1 == {"value": 10}
    assert call_count == 1

    # 2. Second call (hit)
    res2 = await mock_endpoint(val=10)
    assert res2 == {"value": 10}
    assert call_count == 1

    # 3. Different params (miss)
    res3 = await mock_endpoint(val=20)
    assert res3 == {"value": 20}
    assert call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_expiration() -> None:
    """Test that cache expires correctly."""
    call_count = 0

    @cache_response("test_expire", ttl_seconds=1)
    async def mock_endpoint() -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {"status": "ok"}

    await mock_endpoint()
    assert call_count == 1

    await asyncio.sleep(1.1)

    await mock_endpoint()
    assert call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_fallback_on_error(monkeypatch: MonkeyPatch) -> None:
    """Test that the decorator falls through gracefully if Redis is down."""

    async def mock_get_fail(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        raise ConnectionError("Redis is down")

    redis = get_redis()
    monkeypatch.setattr(redis, "get", mock_get_fail)
    monkeypatch.setattr(redis, "setex", mock_get_fail)

    call_count = 0

    @cache_response("test_fallback", ttl_seconds=10)
    async def mock_endpoint() -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return {"status": "fallback"}

    # Should still work even if Redis fails
    res = await mock_endpoint()
    assert res == {"status": "fallback"}
    assert call_count == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_key_uniqueness() -> None:
    """Test that different kwargs produce different cache keys."""

    @cache_response("test_unique")
    async def mock_endpoint(**kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        return kwargs

    await mock_endpoint(a=1, b=2)
    await mock_endpoint(b=2, a=1)  # Same params, different order

    # If I use a mock that tracks calls:
    call_count = 0

    @cache_response("test_unique_logic")
    async def tracked_endpoint(**kwargs: Any) -> int:  # noqa: ANN401
        nonlocal call_count
        call_count += 1
        return call_count

    await tracked_endpoint(x=1, y=2)
    await tracked_endpoint(y=2, x=1)

    assert call_count == 1  # Should be a hit


@pytest.mark.unit
def test_reset_redis() -> None:
    """Test resetting the redis client singleton."""
    from src.cache.redis_client import get_redis, reset_redis

    get_redis()
    reset_redis()
    pass
