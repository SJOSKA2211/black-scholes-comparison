import pytest
from fastapi.testclient import TestClient
from src.main import app
from unittest.mock import MagicMock, AsyncMock, patch
from src.auth.dependencies import get_current_user
from src.methods.base import PriceResult
import pandas as pd

client = TestClient(app)

async def mock_get_current_user():
    return {"id": "user-123", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.mark.unit
class TestAPI:
    @patch("src.routers.pricing.analytical_engine")
    @patch("src.routers.pricing.METHOD_MAP")
    def test_pricing_endpoint_full(self, mock_map, mock_analytical):
        mock_analytical.price.return_value = PriceResult(
            method_type="analytical", computed_price=10.0, exec_seconds=0.01
        )
        mock_pricer = MagicMock(return_value=PriceResult(
            method_type="standard_mc", computed_price=10.5, exec_seconds=0.05
        ))
        mock_map.get.side_effect = lambda k, d=None: mock_pricer if k == "standard_mc" else d
        mock_map.__contains__.side_effect = lambda k: k == "standard_mc"
        
        payload = {
            "params": {
                "underlying_price": 100.0,
                "strike_price": 100.0,
                "maturity_years": 1.0,
                "volatility": 0.2,
                "risk_free_rate": 0.05,
                "option_type": "call"
            },
            "methods": ["standard_mc", "unknown"]
        }
        response = client.post("/api/v1/price", json=payload)
        assert response.status_code == 200

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    @patch("src.routers.health.get_rabbitmq_connection")
    def test_health_check_deep(self, mock_rmq, mock_supa, mock_minio, mock_redis):
        mock_redis.return_value.ping = AsyncMock(return_value=True)
        mock_minio.return_value.list_buckets = MagicMock(return_value=[])
        mock_supa.return_value.table.return_value.select.return_value.limit.return_value.execute = MagicMock()
        mock_rmq.return_value = MagicMock(is_closed=False)
        
        response = client.get("/health")
        assert response.status_code == 200

    @patch("src.routers.market_data.get_market_data")
    def test_market_data_endpoint(self, mock_get_data):
        mock_get_data.return_value = []
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 200

    @patch("src.routers.notifications.get_notifications")
    @patch("src.routers.notifications.mark_notification_read")
    def test_notifications_endpoints(self, mock_read, mock_get):
        mock_get.return_value = []
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        
        response = client.patch("/api/v1/notifications/123/read")
        assert response.status_code == 200

    @patch("src.routers.scrapers.publish_scrape_task")
    @patch("src.routers.scrapers.get_scrape_runs")
    def test_scrapers_endpoints(self, mock_runs, mock_pub):
        mock_pub.return_value = AsyncMock()
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 200
        
        mock_runs.return_value = []
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 200

    @patch("src.routers.experiments.publish_experiment_task")
    @patch("src.routers.experiments.get_experiments")
    def test_experiments_endpoints(self, mock_get, mock_pub):
        mock_pub.return_value = AsyncMock()
        response = client.post("/api/v1/experiments/run", json={"params": {}})
        assert response.status_code == 200
        
        mock_get.return_value = {"data": []}
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 200

    @patch("src.routers.downloads._fetch_data")
    @patch("src.routers.downloads.upload_export")
    def test_download_endpoint(self, mock_upload, mock_fetch):
        mock_fetch.return_value = pd.DataFrame([{"id": 1}])
        mock_upload.return_value = "url"
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 200
