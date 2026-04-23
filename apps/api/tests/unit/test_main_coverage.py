"""Unit tests for additional main.py coverage."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import lifespan, app
from fastapi import FastAPI

@pytest.mark.unit
class TestMainCoverage:
    @patch("src.main.get_settings")
    @patch("src.main.start_consumers")
    @patch("src.cache.redis_client.get_redis")
    @patch("src.storage.minio_client.get_minio")
    async def test_lifespan_exception(self, mock_minio, mock_redis, mock_consumers, mock_settings) -> None:
        """Test exception handling in lifespan startup."""
        mock_consumers.side_effect = Exception("Queue error")
        
        # Test the lifespan context manager
        async with lifespan(app):
            pass
            
        mock_consumers.assert_called_once()
        # Should not raise exception (caught in try/except)

    async def test_root_endpoint(self) -> None:
        """Test the root endpoint for coverage."""
        from fastapi.testclient import TestClient
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert "Black-Scholes Research API" in response.json()["message"]
