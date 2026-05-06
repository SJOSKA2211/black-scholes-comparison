"""Unit tests for the cache decorator."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.cache.decorators import cache_response


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_decorator_hit():
    """Test cache hit scenario."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps({"result": "cached_data"})

    with patch("src.cache.decorators.get_redis", return_value=mock_redis):

        @cache_response("test", ttl_seconds=100)
        async def mock_func(param: str):
            return {"result": "new_data"}

        result = await mock_func(param="test")
        assert result == {"result": "cached_data"}
        mock_redis.get.assert_called_once()
        # mock_func body should not be executed


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_decorator_miss():
    """Test cache miss scenario."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("src.cache.decorators.get_redis", return_value=mock_redis):

        @cache_response("test", ttl_seconds=100)
        async def mock_func(param: str):
            return {"result": "new_data"}

        result = await mock_func(param="test")
        assert result == {"result": "new_data"}
        mock_redis.get.assert_called_once()
        mock_redis.setex.assert_called_once()
