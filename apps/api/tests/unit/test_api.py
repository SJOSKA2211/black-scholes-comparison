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
                # Success path
                payload = {"params": {"underlying_price": 100, "strike_price": 100, "maturity_years": 1, "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"}, "methods": ["standard_mc"]}
                response = client.post("/api/v1/price", json=payload)
                assert response.status_code == 200
                
                # isNaN branch
                mock_res.computed_price = float("nan")
                response = client.post("/api/v1/price", json=payload)
                assert response.status_code == 200
                
                # Unknown method branch (it will be skipped if not in METHOD_MAP, or return what's there)
                # But request.methods is validated by Pydantic against MethodType
                # So we test skipping logic in the loop
                with patch.dict("src.routers.pricing.METHOD_MAP", {"standard_mc": mock_pricer}, clear=True):
                     payload["methods"] = ["analytical"] # Should skip analytical if not in METHOD_MAP
                     response = client.post("/api/v1/price", json=payload)
                     assert response.status_code == 200
                
                # Exception branch
                mock_pricer.side_effect = Exception("Fail")
                payload["methods"] = ["standard_mc"]
                response = client.post("/api/v1/price", json=payload)
                assert response.status_code == 500

    def test_get_methods(self):
        response = client.get("/api/v1/methods")
        assert response.status_code == 200
        assert len(response.json()) > 0

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    @patch("src.routers.health.get_rabbitmq_connection")
    def test_health_check_fail_branches(self, mock_rmq, mock_supa, mock_minio, mock_redis):
        # All fail
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
    @patch("src.routers.notifications.mark_all_notifications_read")
    def test_notifications_branches(self, mock_all_read, mock_read, mock_get):
        # Get fail
        mock_get.side_effect = Exception("Fail")
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 500
        
        # Mark read fail
        mock_read.side_effect = Exception("Fail")
        response = client.patch("/api/v1/notifications/123/read")
        assert response.status_code == 500
        
        # Mark all read fail
        mock_all_read.side_effect = Exception("Fail")
        response = client.post("/api/v1/notifications/read-all")
        assert response.status_code == 500

    @patch("src.routers.scrapers.publish_scrape_task")
    @patch("src.routers.scrapers.get_scrape_runs")
    def test_scrapers_branches(self, mock_runs, mock_pub):
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 500
        mock_runs.side_effect = Exception("Fail")
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 500

    @patch("src.routers.experiments.publish_experiment_task")
    @patch("src.routers.experiments.get_experiments")
    @patch("src.routers.experiments.get_experiment_by_id")
    def test_experiments_branches(self, mock_by_id, mock_get, mock_pub):
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/experiments/run", json={"params": {"underlying_price": 100, "strike_price": 100, "maturity_years": 1, "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"}})
        assert response.status_code == 500
        mock_get.side_effect = Exception("Fail")
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 500
        mock_by_id.return_value = None
        response = client.get("/api/v1/experiments/results/123")
        assert response.status_code == 404

    @patch("src.routers.downloads._fetch_data")
    @patch("src.routers.downloads.upload_export")
    def test_download_branches(self, mock_upload, mock_fetch):
        # Empty data
        mock_fetch.return_value = pd.DataFrame()
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 404
        
        # Fetch fail
        mock_fetch.side_effect = Exception("Fail")
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 500

    @patch("src.routers.websocket.ws_manager")
    @patch("src.routers.websocket.verify_ws_token")
    def test_websocket_branches(self, mock_verify, mock_ws_manager):
        mock_verify.return_value = {"id": "user-123"}
        mock_ws_manager.connect = AsyncMock()
        mock_ws_manager.disconnect = AsyncMock()
        
        # Valid
        with client.websocket_connect("/ws/experiments?token=valid"):
             pass
        
        # Invalid channel
        try:
            with client.websocket_connect("/ws/invalid?token=valid"):
                 pass
        except:
            pass
        
        # Auth fail
        mock_verify.return_value = None
        try:
            with client.websocket_connect("/ws/experiments?token=invalid"):
                 pass
        except:
            pass
