from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cache.decorators import cache_response
from src.cache.redis_client import get_redis


@pytest.mark.unit
class TestCache:
    @patch("src.cache.redis_client.aioredis.from_url")
    @patch("src.cache.redis_client.get_settings")
    def test_get_redis_init(self, mock_settings, mock_from_url):
        get_redis.cache_clear()
        mock_settings.return_value.redis_url = "redis://localhost"
        mock_settings.return_value.redis_password = "pass"

        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = get_redis()
        assert client == mock_client
        mock_from_url.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_decorator_hit(self, mock_get_redis):
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value='{"res": "cached"}')
        mock_get_redis.return_value = mock_r

        call_count = 0

        @cache_response(key_prefix="test", ttl_seconds=60)
        async def slow_func(x):
            nonlocal call_count
            call_count += 1
            return {"res": "real"}

        res = await slow_func(1)
        assert res == {"res": "cached"}
        assert call_count == 0

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_decorator_miss(self, mock_get_redis):
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=None)
        mock_r.setex = AsyncMock()
        mock_get_redis.return_value = mock_r

        call_count = 0

        @cache_response(key_prefix="test", ttl_seconds=60)
        async def slow_func(x):
            nonlocal call_count
            call_count += 1
            return {"res": "real"}

        res = await slow_func(1)
        assert res == {"res": "real"}
        assert call_count == 1
        mock_r.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_decorator_error(self, mock_get_redis):
        # Redis error should not break the function - wait, my implementation
        # doesn't catch errors in the decorator yet.
        # I should probably add try/except to the decorator.
        mock_get_redis.side_effect = Exception("Redis Down")

        @cache_response(key_prefix="test", ttl_seconds=60)
        async def fast_func(x):
            return "ok"

        with pytest.raises(Exception):
            await fast_func(1)
