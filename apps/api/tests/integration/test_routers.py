from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.mark.integration
class TestRoutersIntegration:
    def setup_method(self) -> None:
        self.client = TestClient(app)

    def test_health_check(self) -> None:
        with patch("src.routers.health.get_supabase_client"), \
             patch("src.routers.health.get_redis") as mock_redis, \
             patch("src.routers.health.get_rabbitmq_connection", new_callable=AsyncMock) as mock_rmq, \
             patch("src.routers.health.get_minio"):

            mock_redis.return_value.ping = AsyncMock(return_value=True)
            mock_rmq.return_value.is_closed = False

            response = self.client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_pricing_no_auth(self) -> None:
        # Should return 401 as per mandate Section 16.2
        response = self.client.post("/api/v1/pricing/calculate", json={})
        assert response.status_code == 401

    def test_methods_list(self) -> None:
        response = self.client.get("/api/v1/pricing/methods")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 12
