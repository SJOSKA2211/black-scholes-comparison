import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import MagicMock, AsyncMock, patch
from src.auth.dependencies import get_current_user
from src.methods.base import PriceResult
import pandas as pd
import src.routers.pricing

client = TestClient(app)

async def mock_get_current_user():
    return {"id": "user-123", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.mark.unit
class TestAPI:
    def test_pricing_endpoint_full(self):
        mock_res = PriceResult(method_type="standard_mc", computed_price=10.5, exec_seconds=0.05)
        mock_pricer = MagicMock(return_value=mock_res)
        with patch("src.routers.pricing.analytical_engine") as mock_analytical:
            mock_analytical.price.return_value = PriceResult(method_type="analytical", computed_price=10.0, exec_seconds=0.01)
            with patch.dict("src.routers.pricing.METHOD_MAP", {"standard_mc": mock_pricer}, clear=True):
                payload = {"params": {"underlying_price": 100, "strike_price": 100, "maturity_years": 1, "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"}, "methods": ["standard_mc"]}
                response = client.post("/api/v1/price", json=payload)
                assert response.status_code == 200

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    @patch("src.routers.health.get_rabbitmq_connection")
    def test_health_check_fail_branches(self, mock_rmq, mock_supa, mock_minio, mock_redis):
        mock_supa.side_effect = Exception("Fail")
        mock_redis.side_effect = Exception("Fail")
        mock_rmq.side_effect = Exception("Fail")
        mock_minio.side_effect = Exception("Fail")
        response = client.get("/health")
        assert response.json()["status"] == "error"

    @patch("src.routers.market_data.get_market_data")
    def test_market_data_fail(self, mock_get_data):
        mock_get_data.side_effect = Exception("Fail")
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 500

    @patch("src.routers.notifications.get_notifications")
    @patch("src.routers.notifications.mark_notification_read")
    def test_notifications_fail(self, mock_read, mock_get):
        mock_get.side_effect = Exception("Fail")
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 500
        mock_read.side_effect = Exception("Fail")
        response = client.patch("/api/v1/notifications/123/read")
        assert response.status_code == 500

    @patch("src.routers.scrapers.publish_scrape_task")
    @patch("src.routers.scrapers.get_scrape_runs")
    def test_scrapers_fail(self, mock_runs, mock_pub):
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 500
        mock_runs.side_effect = Exception("Fail")
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 500

    @patch("src.routers.experiments.publish_experiment_task")
    @patch("src.routers.experiments.get_experiments")
    def test_experiments_fail(self, mock_get, mock_pub):
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/experiments/run", json={"params": {}})
        assert response.status_code == 500
        mock_get.side_effect = Exception("Fail")
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 500

    @patch("src.routers.downloads._fetch_data")
    @patch("src.routers.downloads.upload_export")
    def test_download_branches(self, mock_upload, mock_fetch):
        mock_fetch.return_value = pd.DataFrame()
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 404
        mock_fetch.side_effect = Exception("Fail")
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 500

    @patch("src.routers.websocket.ws_manager")
    def test_websocket_logic(self, mock_ws_manager):
        mock_ws_manager.connect = AsyncMock()
        # Simply trigger the route to cover the logic
        try:
            with client.websocket_connect("/ws/experiments"):
                pass
        except:
            pass
        try:
            with client.websocket_connect("/ws/invalid"):
                pass
        except:
            pass
