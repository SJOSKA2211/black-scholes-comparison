import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.database.repository import upsert_option_parameters, get_experiments, get_notifications
from src.exceptions import RepositoryError
from src.database.supabase_client import get_supabase_client
from src.queue.rabbitmq_client import get_rabbitmq_connection
from src.auth.dependencies import get_current_user

@pytest.mark.unit
class TestBackendFinalCoverage:
    
    @patch("src.database.repository.get_supabase_client")
    async def test_upsert_option_parameters_error(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.side_effect = Exception("DB Fail")
        
        with pytest.raises(RepositoryError):
            await upsert_option_parameters({"strike": 100})

    @patch("src.database.repository.get_supabase_client")
    async def test_get_experiments_branches(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_range = mock_select.range.return_value
        mock_order = mock_range.order.return_value
        
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 0
        mock_order.execute.return_value = mock_response
        
        res = await get_experiments(method_type=None, market_source=None)
        assert res["total"] == 0
        
        mock_eq = mock_select.eq.return_value
        mock_range_eq = mock_eq.range.return_value
        mock_order_eq = mock_range_eq.order.return_value
        mock_order_eq.execute.return_value = mock_response
        
        await get_experiments(method_type="analytical", market_source=None)

    @patch("src.database.repository.get_supabase_client")
    async def test_get_notifications_unread_branch(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        
        mock_table = mock_client.table.return_value
        mock_select = mock_table.select.return_value
        mock_eq = mock_select.eq.return_value
        mock_order = mock_eq.order.return_value
        mock_limit = mock_order.limit.return_value
        
        mock_response = MagicMock()
        mock_response.data = []
        mock_limit.execute.return_value = mock_response
        
        await get_notifications("u1", unread_only=False)

    def test_supabase_client_direct(self):
        with patch("src.database.supabase_client.get_settings") as mock_settings:
            mock_settings.return_value.supabase_url = "http://test.com"
            mock_settings.return_value.supabase_key = "key"
            with patch("src.database.supabase_client.create_client") as mock_create:
                get_supabase_client.cache_clear()
                get_supabase_client()
                assert mock_create.called

    @patch("aio_pika.connect_robust", new_callable=AsyncMock)
    async def test_rabbitmq_client_direct(self, mock_connect):
        await get_rabbitmq_connection()
        assert mock_connect.called

    def test_startup_event(self):
        with patch("src.main.get_minio") as mock_minio:
            with patch("src.main.start_consumers", new_callable=AsyncMock) as mock_start:
                with TestClient(app) as client:
                    pass
                assert mock_minio.called
                assert mock_start.called

    @patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock)
    @patch("src.routers.websocket.ws_manager")
    def test_websocket_endpoint_full(self, mock_ws_manager, mock_verify):
        client = TestClient(app)
        mock_verify.return_value = {"id": "user123"}
        
        async def mock_connect(ws, channel):
            await ws.accept()
        
        mock_ws_manager.connect = AsyncMock(side_effect=mock_connect)
        mock_ws_manager.disconnect = AsyncMock()
        
        with client.websocket_connect("/ws/experiments?token=good") as websocket:
            websocket.close()
        
        assert mock_ws_manager.connect.called
        assert mock_ws_manager.disconnect.called

    @patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock)
    @patch("src.routers.websocket.ws_manager")
    def test_websocket_endpoint_exception(self, mock_ws_manager, mock_verify):
        client = TestClient(app)
        mock_verify.return_value = {"id": "user123"}
        
        async def mock_connect_fail(ws, channel):
            # No accept() here to trigger failure at router level if it calls it
            # Or just raise
            raise Exception("WS Fail")
            
        mock_ws_manager.connect = AsyncMock(side_effect=mock_connect_fail)
        mock_ws_manager.disconnect = AsyncMock()
        
        # We use a try-except to catch the Starlette side-effect
        try:
            with client.websocket_connect("/ws/experiments") as websocket:
                pass
        except Exception:
            pass
            
        assert mock_ws_manager.disconnect.called

    @patch("src.routers.scrapers.publish_scrape_task", new_callable=AsyncMock)
    def test_scrapers_router_branches(self, mock_publish):
        # Override dependency
        app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}
        client = TestClient(app)
        try:
            response = client.post("/api/v1/scrapers/trigger?market=spy&trade_date=2024-01-01")
            assert response.status_code == 200
            assert mock_publish.called
            
            client.post("/api/v1/scrapers/trigger?market=nse")
            assert mock_publish.call_count == 2
            
            mock_publish.side_effect = Exception("Fail")
            response = client.post("/api/v1/scrapers/trigger?market=spy")
            assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()
