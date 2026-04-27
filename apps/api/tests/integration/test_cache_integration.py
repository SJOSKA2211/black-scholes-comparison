"""Integration tests for Redis cache client and cache-aside decorator.
Strictly zero-mock: uses real Redis instance.
"""

import json
import pytest
from src.cache.decorators import cache_response
from src.cache.redis_client import get_redis

@pytest.mark.integration
class TestRedisCacheIntegration:
    @pytest.mark.asyncio
    async def test_cache_hit_and_miss(self):
        """Test real cache hit/miss flow with decorator."""
        redis = get_redis()
        if redis is None:
            pytest.fail("Redis client could not be initialized")
            
        call_count = 0

        @cache_response(key_prefix="integration_test", ttl_seconds=10)
        async def sample_func(x: int):
            nonlocal call_count
            call_count += 1
            return {"value": x * 2}

        # 1. First call (Miss)
        res1 = await sample_func(10)
        assert res1 == {"value": 20}
        assert call_count == 1

        # 2. Second call (Hit)
        res2 = await sample_func(10)
        assert res2 == {"value": 20}
        assert call_count == 1  # Still 1 because it hit the cache

        # 3. Different params (Miss)
        res3 = await sample_func(20)
        assert res3 == {"value": 40}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_cache_direct_access(self):
        """Test direct Redis access via client."""
        redis = get_redis()
        key = "direct_test_key"
        val = {"status": "ok"}
        
        await redis.set(key, json.dumps(val), ex=10)
        cached = await redis.get(key)
        assert json.loads(cached) == val
        
        await redis.delete(key)
        assert await redis.get(key) is None
