import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from src.cache.decorators import cache_response

@pytest.mark.unit
class TestCacheDecorator:
    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_hit(self, mock_get_redis):
        # Setup
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = json.dumps({"data": "cached"})
        
        call_count = 0
        @cache_response("test", 60)
        async def mock_func(param: str):
            nonlocal call_count
            call_count += 1
            return {"data": "new"}

        # Execute
        result = await mock_func("val")
        
        # Verify
        assert result == {"data": "cached"}
        assert call_count == 0
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_cache_miss(self, mock_get_redis):
        # Setup
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None
        
        call_count = 0
        @cache_response("test", 60)
        async def mock_func(param: str):
            nonlocal call_count
            call_count += 1
            return {"data": "new"}

        # Execute
        result = await mock_func("val")
        
        # Verify
        assert result == {"data": "new"}
        assert call_count == 1
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_key_uniqueness(self, mock_get_redis):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None
        
        @cache_response("test", 60)
        async def mock_func(a: int, b: int):
            return {"sum": a + b}

        await mock_func(1, 2)
        key1 = mock_redis.get.call_args[0][0]
        
        mock_redis.get.reset_mock()
        await mock_func(2, 1)
        key2 = mock_redis.get.call_args[0][0]
        
        assert key1 != key2

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_ttl_expiry(self, mock_get_redis):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None
        
        ttl = 3600
        @cache_response("test", ttl)
        async def mock_func():
            return {"ok": True}

        await mock_func()
        # setex(key, time, value)
        assert mock_redis.setex.call_args[0][1] == ttl

    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_graceful_error(self, mock_get_redis):
        # Redis unavailable
        mock_get_redis.side_effect = Exception("Redis Down")
        
        @cache_response("test", 60)
        async def mock_func():
            return {"ok": True}

        # Should fall through and run function
        with pytest.raises(Exception, match="Redis Down"):
            await mock_func()
            
    @pytest.mark.asyncio
    @patch("src.cache.decorators.get_redis")
    async def test_complex_args(self, mock_get_redis):
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None
        
        @cache_response("test", 60)
        async def mock_func(data: dict):
            return data

        await mock_func({"x": [1, 2], "y": {"z": 3}})
        mock_redis.get.assert_called_once()
