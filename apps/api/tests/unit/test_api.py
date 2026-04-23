from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.main import app
from src.methods.base import PriceResult

client = TestClient(app)


async def mock_get_current_user() -> dict[str, str]:
    return {"id": "user-123", "email": "test@example.com"}


@pytest.fixture(autouse=True)
def override_auth() -> Generator[None, None]:
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture(autouse=True)
def mock_redis_global() -> Generator[MagicMock, None, None]:
    with patch("src.cache.decorators.get_redis") as mock:
        mock_r = MagicMock()
        mock_r.get = AsyncMock(return_value=None)
        mock_r.setex = AsyncMock(return_value=None)
        mock.return_value = mock_r
        yield mock_r


@pytest.mark.unit
class TestAPI:
    def test_pricing_endpoint_full(self) -> None:
        mock_res = PriceResult(method_type="standard_mc", computed_price=10.5, exec_seconds=0.05)
        with patch("src.routers.pricing.get_method_instance") as mock_factory:
            mock_factory.return_value = MagicMock(price=MagicMock(return_value=mock_res))
            # Success path
            payload = {
                "underlying_price": 100,
                "strike_price": 100,
                "maturity_years": 1,
                "volatility": 0.2,
                "risk_free_rate": 0.05,
                "option_type": "call",
            }
            response = client.post(
                "/api/v1/pricing/calculate?method_type=standard_mc", json=payload
            )
            assert response.status_code == 200

            mock_factory.return_value.price.side_effect = Exception("Fail")
            response = client.post(
                "/api/v1/pricing/calculate?method_type=standard_mc", json=payload
            )
            assert response.status_code == 500

            # Comparison path
            mock_factory.return_value.price.side_effect = None
            mock_factory.return_value.price.return_value = mock_res
            response = client.post(
                "/api/v1/pricing/compare?methods=standard_mc&methods=binomial_crr_richardson",
                json=payload,
            )
            assert response.status_code == 200

    def test_get_methods(self) -> None:
        response = client.get("/api/v1/pricing/methods")
        assert response.status_code == 200
        assert len(response.json()) > 0

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    @patch("src.routers.health.get_rabbitmq_connection")
    def test_health_check_fail_branches(
        self, mock_rmq: Any, mock_supa: Any, mock_minio: Any, mock_redis: Any
    ) -> None:
        # All fail
        mock_supa.side_effect = Exception("Fail")
        mock_redis.side_effect = Exception("Fail")
        mock_rmq.side_effect = Exception("Fail")
        mock_minio.side_effect = Exception("Fail")
        response = client.get("/health")
        assert response.json()["status"] == "error"

        # All success
        mock_supa.side_effect = None
        mock_redis.side_effect = None
        mock_rmq.side_effect = None
        mock_minio.side_effect = None

        mock_redis_obj = MagicMock()
        mock_redis_obj.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_redis_obj

        mock_rmq_obj = MagicMock()
        mock_rmq_obj.is_closed = False
        mock_rmq.return_value = mock_rmq_obj

        response = client.get("/health")
        assert response.json()["status"] == "ok"

        # RabbitMQ is_closed = True branch
        mock_rmq_obj.is_closed = True
        response = client.get("/health")
        assert response.json()["services"]["rabbitmq"] == "unknown"

    @patch("src.routers.market_data.get_market_data")
    def test_market_data_fail(self, mock_get_data: Any) -> None:
        mock_get_data.side_effect = Exception("Fail")
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 500

        mock_get_data.side_effect = None
        mock_get_data.return_value = []
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 200

    @patch("src.routers.notifications.get_notifications", new_callable=AsyncMock)
    @patch("src.routers.notifications.mark_notification_read", new_callable=AsyncMock)
    @patch("src.routers.notifications.mark_all_notifications_read", new_callable=AsyncMock)
    def test_notifications_branches(
        self, mock_all_read: Any, mock_read: Any, mock_get: Any
    ) -> None:
        mock_get.return_value = []
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200

        mock_read.return_value = None
        response = client.patch("/api/v1/notifications/123/read")
        assert response.status_code == 200

        mock_all_read.return_value = None
        response = client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200

    @patch("src.routers.scrapers.publish_scrape_task", new_callable=AsyncMock)
    @patch("src.routers.scrapers.get_scrape_runs", new_callable=AsyncMock)
    def test_scrapers_branches(self, mock_runs: Any, mock_pub: Any) -> None:
        mock_pub.return_value = None
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 200

        response = client.post("/api/v1/scrapers/trigger")
        assert response.status_code == 422

        mock_runs.return_value = []
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 200

    @patch("src.routers.experiments.publish_experiment_task", new_callable=AsyncMock)
    @patch("src.routers.experiments.get_experiments", new_callable=AsyncMock)
    @patch("src.routers.experiments.get_experiments_by_method", new_callable=AsyncMock)
    @patch("src.routers.experiments.get_experiment_by_id", new_callable=AsyncMock)
    def test_experiments_branches(
        self, mock_by_id: Any, mock_get_by_method: Any, mock_get: Any, mock_pub: Any
    ) -> None:
        mock_pub.return_value = None
        response = client.post(
            "/api/v1/experiments/run",
            json={
                "params": {
                    "underlying_price": 100,
                    "strike_price": 100,
                    "maturity_years": 1,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                }
            },
        )
        assert response.status_code == 200

        mock_get.return_value = {"items": []}
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 200

    @patch("src.routers.downloads.get_market_data", new_callable=AsyncMock)
    @patch("src.routers.downloads.get_experiments", new_callable=AsyncMock)
    @patch("src.routers.downloads.upload_export")
    def test_download_branches(
        self, mock_upload: Any, mock_get_exp: Any, mock_get_market: Any
    ) -> None:
        mock_get_market.return_value = [{"a": 1}]
        mock_get_exp.return_value = {"items": [{"b": 2}]}
        mock_upload.return_value = "http://minio/file.csv"

        response = client.get("/api/v1/download/experiments?format=csv")
        assert response.status_code == 200

        response = client.get("/api/v1/download/market_data?format=xlsx")
        assert response.status_code == 200

    def test_websocket_invalid_channel(self) -> None:
        from fastapi import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/v1/ws/invalid_channel"):
                pass
