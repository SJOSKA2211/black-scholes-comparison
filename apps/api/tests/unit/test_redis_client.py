"""Unit tests for the Redis client."""
from unittest.mock import patch, MagicMock
import pytest
from src.cache.redis_client import get_redis

@pytest.mark.unit
def test_get_redis():
    """Test that get_redis creates and returns a Redis client."""
    # Clear the lru_cache for testing
    get_redis.cache_clear()
    
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        
        client = get_redis()
        
        assert client == mock_client
        mock_from_url.assert_called_once()
        
        # Test lru_cache: second call should not call from_url again
        client2 = get_redis()
        assert client2 == mock_client
        mock_from_url.assert_called_once()
