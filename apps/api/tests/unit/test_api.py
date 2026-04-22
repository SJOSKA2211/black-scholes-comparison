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
        # In this case, services["rabbitmq"] remains "unknown" but status is "ok"
        # because no exception was raised.
        assert response.json()["services"]["rabbitmq"] == "unknown"

    @patch("src.routers.market_data.get_market_data")
    def test_market_data_fail(self, mock_get_data):
        mock_get_data.side_effect = Exception("Fail")
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 500
        
        mock_get_data.side_effect = None
        mock_get_data.return_value = []
        response = client.get("/api/v1/market-data/")
        assert response.status_code == 200

    @patch("src.routers.notifications.get_notifications")
    @patch("src.routers.notifications.mark_notification_read")
    @patch("src.routers.notifications.mark_all_notifications_read")
    async def test_notifications_branches(self, mock_all_read, mock_read, mock_get):
        # Success paths
        mock_get.return_value = []
        response = client.get("/api/v1/notifications/")
        assert response.status_code == 200
        
        mock_read.return_value = None
        response = client.patch("/api/v1/notifications/123/read")
        assert response.status_code == 200
        
        mock_all_read.return_value = None
        response = client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200

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
    async def test_scrapers_branches(self, mock_runs, mock_pub):
        # Success
        mock_pub.return_value = None
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 200
        
        # Missing market (FastAPI returns 422 for missing required Query params)
        response = client.post("/api/v1/scrapers/trigger")
        assert response.status_code == 422
        
        mock_runs.return_value = []
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 200

        # Fail
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 500
        mock_runs.side_effect = Exception("Fail")
        response = client.get("/api/v1/scrapers/runs")
        assert response.status_code == 500

    @patch("src.routers.experiments.publish_experiment_task")
    @patch("src.routers.experiments.get_experiments")
    @patch("src.routers.experiments.get_experiments_by_method")
    @patch("src.routers.experiments.get_experiment_by_id")
    async def test_experiments_branches(self, mock_by_id, mock_get_by_method, mock_get, mock_pub):
        # Success
        mock_pub.return_value = None
        response = client.post("/api/v1/experiments/run", json={"params": {"underlying_price": 100, "strike_price": 100, "maturity_years": 1, "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"}})
        assert response.status_code == 200
        
        mock_get.return_value = {"data": []}
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 200
        
        mock_get_by_method.return_value = []
        response = client.get("/api/v1/experiments/results?method_type=standard_mc")
        assert response.status_code == 200
        
        mock_by_id.return_value = {"id": "123"}
        response = client.get("/api/v1/experiments/results/123")
        assert response.status_code == 200

        # Fail
        mock_pub.side_effect = Exception("Fail")
        response = client.post("/api/v1/experiments/run", json={"params": {}})
        assert response.status_code == 500
        
        mock_get.side_effect = Exception("Fail")
        response = client.get("/api/v1/experiments/results")
        assert response.status_code == 500
        
        mock_by_id.return_value = None
        response = client.get("/api/v1/experiments/results/123")
        assert response.status_code == 404
        
        mock_by_id.side_effect = Exception("Fail")
        response = client.get("/api/v1/experiments/results/123")
        assert response.status_code == 500

    @patch("src.routers.downloads.get_market_data", new_callable=AsyncMock)
    @patch("src.routers.downloads.get_experiments", new_callable=AsyncMock)
    @patch("src.routers.downloads.upload_export")
    async def test_download_branches(self, mock_upload, mock_get_exp, mock_get_market):
        # Success
        mock_get_market.return_value = [{"a": 1}]
        mock_get_exp.return_value = {"data": [{"b": 2}]}
        mock_upload.return_value = "http://minio/file.csv"
        
        # Experiments resource
        response = client.get("/api/v1/download/experiments?format=csv")
        assert response.status_code == 200
        
        # Market data resource
        response = client.get("/api/v1/download/market_data?format=csv")
        assert response.status_code == 200
        
        # Other formats
        response = client.get("/api/v1/download/market_data?format=json")
        assert response.status_code == 200
        response = client.get("/api/v1/download/market_data?format=xlsx")
        assert response.status_code == 200
        
        # Invalid resource (covers _fetch_data else)
        from src.routers.downloads import _fetch_data
        with pytest.raises(ValueError, match="Unknown resource"):
            await _fetch_data("invalid")
            
        # Invalid format (covers _serialize else)
        from src.routers.downloads import _serialize
        with pytest.raises(ValueError, match="Unknown format"):
            _serialize(pd.DataFrame([{"a": 1}]), "invalid")

        # Empty data
        mock_get_market.return_value = []
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 404
        
        # Fetch fail
        mock_get_market.side_effect = Exception("Fail")
        response = client.get("/api/v1/download/market_data")
        assert response.status_code == 500

    @patch("src.routers.websocket.ws_manager", new_callable=AsyncMock)
    @patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock)
    async def test_websocket_branches(self, mock_verify, mock_ws_manager):
        from src.routers.websocket import websocket_endpoint
        from starlette.websockets import WebSocketDisconnect
        
        # Setup mock websocket
        mock_ws = AsyncMock()
        mock_ws.close = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect)
        
        # 1. Unknown channel
        await websocket_endpoint(mock_ws, "invalid_channel", "token")
        mock_ws.close.assert_called_with(code=4004, reason="Unknown channel")
        
        # 2. Auth fail
        mock_ws.reset_mock()
        mock_verify.return_value = None
        await websocket_endpoint(mock_ws, "experiments", "token")
        # verify_ws_token should have handled closure
        
        # 3. Success and Disconnect
        mock_ws.reset_mock()
        mock_verify.return_value = {"id": "user-123"}
        await websocket_endpoint(mock_ws, "experiments", "token")
        mock_ws_manager.connect.assert_called()
        mock_ws_manager.disconnect.assert_called()
        
        # 4. Exception in loop
        mock_ws.reset_mock()
        mock_ws.receive_text.side_effect = Exception("Fail")
        await websocket_endpoint(mock_ws, "experiments", "token")
        mock_ws_manager.disconnect.assert_called()
