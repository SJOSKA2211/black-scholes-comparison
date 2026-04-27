"""Integration tests for Redis cache client and cache-aside decorator.
Strictly zero-mock: uses real Redis instance.
"""

import json
import pytest
from src.cache.decorators import cache_response
from src.cache.redis_client import get_redis, reset_redis
from src.cache.compressed_cache import reset_binary_redis

@pytest.mark.integration
class TestRedisCacheIntegration:
    @pytest.fixture(autouse=True)
    async def setup_cache(self):
        """Reset Redis singletons and flush data before each test."""
        reset_redis()
        reset_binary_redis()
        
        # Flush real Redis data
        redis = get_redis()
        if redis:
            await redis.flushdb()
        
        yield

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

    @pytest.mark.asyncio
    async def test_compressed_cache_flow(self):
        """Test the compressed cache utility."""
        from src.cache.compressed_cache import get_compressed, set_compressed, get_binary_redis
        
        key = "compressed_test_key"
        val = {"large_data": "A" * 2000} # > 2KB
        
        # 1. Set compressed
        await set_compressed(key, val, expire=10)
        
        # 2. Verify raw data is compressed (and not plain JSON)
        binary_redis = get_binary_redis()
        raw_binary = await binary_redis.get(key)
        assert raw_binary is not None
        assert len(raw_binary) < 2000 # Should be significantly smaller
        
        # Verify it's not valid JSON
        try:
            json.loads(raw_binary.decode())
            pytest.fail("Raw binary data should not be valid JSON")
        except:
            pass
            
        # 3. Get compressed
        retrieved = await get_compressed(key)
        assert retrieved == val
        
        # Cleanup
        await binary_redis.delete(key)
