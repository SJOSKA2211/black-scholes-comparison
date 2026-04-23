from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_auth() -> Generator[MagicMock, None, None]:
    with patch("src.auth.dependencies.get_supabase_client") as mock:
        mock_supabase = MagicMock()
        mock.return_value = mock_supabase

        mock_user = MagicMock()
        mock_user.id = "test-user"
        mock_user.email = "test@example.com"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)

        # Mock Profile Role
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )
        yield mock_supabase


@pytest.mark.unit
class TestAllRouters:
    def test_market_data_router(self, mock_auth: Any) -> None:
        with patch("src.routers.market_data.get_market_data") as mock_get:
            mock_get.return_value = [{"id": "1", "price": 100.0}]
            response = client.get(
                "/api/v1/market-data/?source=spy", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            assert response.json()[0]["price"] == 100.0

    def test_scrapers_router_trigger(self, mock_auth: Any) -> None:
        with patch("src.routers.scrapers.publish_scrape_task") as mock_pub:
            response = client.post(
                "/api/v1/scrapers/trigger?market=spy", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            mock_pub.assert_called_once()

    def test_scrapers_router_runs(self, mock_auth: Any) -> None:
        with patch("src.routers.scrapers.get_scrape_runs") as mock_get:
            mock_get.return_value = [{"id": "run-1"}]
            response = client.get(
                "/api/v1/scrapers/runs", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            assert response.json()[0]["id"] == "run-1"

    def test_experiments_router_run(self, mock_auth: Any) -> None:
        with patch("src.routers.experiments.publish_experiment_task") as mock_pub:
            response = client.post(
                "/api/v1/experiments/run",
                json={"test": "data"},
                headers={"Authorization": "Bearer token"},
            )
            assert response.status_code == 200
            mock_pub.assert_called_once()

    def test_experiments_router_results(self, mock_auth: Any) -> None:
        with patch("src.routers.experiments.get_experiments") as mock_get:
            mock_get.return_value = {"items": [{"id": "exp-1"}]}
            response = client.get(
                "/api/v1/experiments/results", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            assert response.json()[0]["id"] == "exp-1"

    def test_notifications_router(self, mock_auth: Any) -> None:
        with patch("src.routers.notifications.get_notifications") as mock_get:
            mock_get.return_value = [{"id": "notif-1"}]
            response = client.get(
                "/api/v1/notifications/", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200

        with patch("src.routers.notifications.mark_notification_read") as mock_patch:
            response = client.patch(
                "/api/v1/notifications/notif-1/read", headers={"Authorization": "Bearer token"}
            )
            assert response.status_code == 200
            mock_patch.assert_called_once()

    def test_downloads_router(self, mock_auth: Any) -> None:
        with patch("src.routers.downloads.get_experiments") as mock_get_exp:
            with patch("src.routers.downloads.upload_export") as mock_upload:
                mock_get_exp.return_value = {"items": [{"id": "1", "val": 100}]}
                mock_upload.return_value = "http://minio/file.csv"
                response = client.get(
                    "/api/v1/download/experiments?format=csv",
                    headers={"Authorization": "Bearer token"},
                )
                assert response.status_code == 200
                assert "url" in response.json()
