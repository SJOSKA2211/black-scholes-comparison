"""Unit tests for Redis cache client and cache-aside decorator.
Tests cover: initialization, cache hit, cache miss, TTL, error handling, Pydantic models.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cache.decorators import cache_response
from src.cache.redis_client import get_redis, reset_redis


@pytest.mark.unit
class TestRedisClient:
    @patch("src.cache.redis_client.aioredis.from_url")
    @patch("src.cache.redis_client.get_settings")
    def test_get_redis_init(self, mock_settings, mock_from_url):
        reset_redis()
        mock_settings.return_value.redis_url = "redis://localhost"
        mock_settings.return_value.redis_password = "pass"

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = get_redis()
        assert client == mock_client
        mock_from_url.assert_called_once()
        reset_redis()  # Clear it so other tests get real redis


@pytest.mark.unit
class TestCacheDecorator:
    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_hit(self, mock_get_redis):
        mock_r = AsyncMock()
        mock_r.get.return_value = json.dumps({"res": "cached"})
        mock_get_redis.return_value = mock_r

        call_count = 0

        @cache_response(key_prefix="test")
        async def mock_func(x):
            nonlocal call_count
            call_count += 1
            return {"res": "real"}

        res = await mock_func(1)
        assert res == {"res": "cached"}
        assert call_count == 0

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_miss(self, mock_get_redis):
        mock_r = AsyncMock()
        mock_r.get.return_value = None
        mock_get_redis.return_value = mock_r

        call_count = 0

        @cache_response(key_prefix="test")
        async def mock_func(x):
            nonlocal call_count
            call_count += 1
            return {"res": "real"}

        res = await mock_func(1)
        assert res == {"res": "real"}
        assert call_count == 1
        mock_r.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_error_graceful(self, mock_get_redis):
        # 1. Lookup failure
        mock_r = AsyncMock()
        mock_r.get.side_effect = Exception("Redis Get Error")
        mock_get_redis.return_value = mock_r

        @cache_response(key_prefix="test")
        async def fast_func(x):
            return {"res": "real"}

        res = await fast_func(1)
        assert res == {"res": "real"}  # Should fall through to real function

        # 2. Store failure
        mock_r.get.side_effect = None
        mock_r.get.return_value = None
        mock_r.setex.side_effect = Exception("Redis Set Error")

        res = await fast_func(1)
        assert res == {"res": "real"}  # Should still return real result

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_pydantic(self, mock_get_redis):
        mock_r = AsyncMock()
        mock_r.get.return_value = None
        mock_get_redis.return_value = mock_r

        from pydantic import BaseModel

        class MockModel(BaseModel):
            val: str

        @cache_response(key_prefix="test")
        async def model_func():
            return MockModel(val="ok")

        res = await model_func()
        assert res.val == "ok"
        mock_r.setex.assert_called_once()
        # Verify it was dumped
        args, kwargs = mock_r.setex.call_args
        assert '{"val": "ok"}' in args[2]
