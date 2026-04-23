"""Unit tests for additional main.py coverage."""

from unittest.mock import AsyncMock, patch

import pytest

from src.main import app, lifespan


@pytest.mark.unit
class TestMainCoverage:
    @patch("src.main.get_settings")
    @patch("src.main.start_consumers", new_callable=AsyncMock)
    @patch("src.cache.redis_client.get_redis")
    @patch("src.storage.minio_client.get_minio")
    async def test_lifespan_timeout(
        self, mock_minio, mock_redis, mock_consumers, mock_settings
    ) -> None:
        """Test timeout handling in lifespan startup."""

        mock_consumers.side_effect = TimeoutError()

        async with lifespan(app):
            pass

        mock_consumers.assert_called_once()

    @patch("src.main.get_settings")
    @patch("src.main.start_consumers", new_callable=AsyncMock)
    @patch("src.cache.redis_client.get_redis")
    @patch("src.storage.minio_client.get_minio")
    async def test_lifespan_exception(
        self, mock_minio, mock_redis, mock_consumers, mock_settings
    ) -> None:
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
