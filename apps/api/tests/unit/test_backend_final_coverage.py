import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.main import app
from src.database.repository import upsert_option_parameters, get_experiments, get_notifications
from src.exceptions import RepositoryError
from src.database.supabase_client import get_supabase_client
from src.queue.rabbitmq_client import get_rabbitmq_connection

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
        mock_exec = mock_client.table.return_value.select.return_value.range.return_value.order.return_value.execute
        mock_exec.return_value.data = []
        mock_exec.return_value.count = 0
        
        # Test with no filters to hit skip branches
        res = await get_experiments(method_type=None, market_source=None)
        assert res["total"] == 0
        
        # Test with only method_type
        mock_exec = mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.order.return_value.execute
        mock_exec.return_value.data = []
        await get_experiments(method_type="analytical", market_source=None)

    @patch("src.database.repository.get_supabase_client")
    async def test_get_notifications_unread_branch(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
        
        # Call with unread_only=False
        await get_notifications("u1", unread_only=False)

    def test_supabase_client_direct(self):
        with patch("src.database.supabase_client.get_settings") as mock_settings:
            mock_settings.return_value.supabase_url = "http://test.com"
            mock_settings.return_value.supabase_key = "key"
            with patch("src.database.supabase_client.create_client") as mock_create:
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
                    # TestClient with context manager triggers startup/shutdown
                    pass
                assert mock_minio.called
                assert mock_start.called

    @patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock)
    @patch("src.routers.websocket.ws_manager", new_callable=AsyncMock)
    def test_websocket_endpoint_full(self, mock_ws_manager, mock_verify):
        client = TestClient(app)
        mock_verify.return_value = {"id": "user123"}
        
        # Test valid connection
        with client.websocket_connect("/ws/experiments?token=good") as websocket:
            websocket.send_text("ping")
            websocket.close()
        
        assert mock_ws_manager.connect.called
        assert mock_ws_manager.disconnect.called

    @patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock)
    @patch("src.routers.websocket.ws_manager", new_callable=AsyncMock)
    def test_websocket_endpoint_exception(self, mock_ws_manager, mock_verify):
        client = TestClient(app)
        mock_verify.return_value = {"id": "user123"}
        mock_ws_manager.connect.side_effect = Exception("WS Fail")
        
        with client.websocket_connect("/ws/experiments") as websocket:
            pass
        assert mock_ws_manager.disconnect.called

    @patch("src.routers.scrapers.publish_scrape_task", new_callable=AsyncMock)
    def test_scrapers_router_branches(self, mock_publish):
        client = TestClient(app)
        with patch("src.routers.scrapers.get_current_user", return_value={"id": "u1"}):
            client.post("/api/v1/scrapers/trigger", json={"market": "spy", "date": "2024-01-01"})
            assert mock_publish.called
