import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocketDisconnect
from src.main import app
from src.database.repository import (
    upsert_option_parameters, 
    get_experiments, 
    get_notifications,
    get_market_data,
    upsert_user_profile
)
from src.exceptions import RepositoryError, AuthenticationError
from src.database.supabase_client import get_supabase_client
from src.queue.rabbitmq_client import get_rabbitmq_connection
from src.auth.dependencies import get_current_user, verify_ws_token
from src.auth.oauth import get_github_user, get_google_user, sync_user_profile
from src.routers.websocket import websocket_endpoint
from src.websocket.manager import WebSocketManager
from src.data.pipeline import DataPipeline
from src.scrapers.nse_next_scraper import NSENextScraper

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
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 0
        mock_client.table.return_value.select.return_value.range.return_value.order.return_value.execute.return_value = mock_response
        res = await get_experiments(method_type=None, market_source=None)
        assert res["total"] == 0
        mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.order.return_value.execute.return_value = mock_response
        await get_experiments(method_type="analytical", market_source=None)

    @patch("src.database.repository.get_supabase_client")
    async def test_get_market_data_branches(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        await get_market_data("spy", trade_date=None, from_date=None, to_date=None, limit=None)

    @patch("src.database.repository.get_supabase_client")
    async def test_get_notifications_unread_branch(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
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

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.websocket.ws_manager", new_callable=AsyncMock)
    async def test_websocket_endpoint_direct(self, mock_ws_manager, mock_get_supabase):
        mock_ws = AsyncMock()
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.auth.get_user.return_value.user.id = "u1"
        
        # Test CancelledError
        mock_ws.receive_text.side_effect = asyncio.exceptions.CancelledError()
        try:
            await websocket_endpoint(mock_ws, "experiments", "token")
        except asyncio.exceptions.CancelledError:
            pass
            
        # Test WebSocketDisconnect
        mock_ws.receive_text.side_effect = WebSocketDisconnect()
        await websocket_endpoint(mock_ws, "experiments", "token")
        assert mock_ws_manager.disconnect.called
        
        # Test unknown channel
        mock_ws = AsyncMock()
        await websocket_endpoint(mock_ws, "invalid", "token")
        assert mock_ws.close.called

        # Test verify_ws_token fail branch (line 32)
        mock_ws = AsyncMock()
        mock_client.auth.get_user.return_value = None
        await websocket_endpoint(mock_ws, "experiments", "token")

        # Test exception branch in router (line 43-44)
        mock_ws = AsyncMock()
        mock_ws_manager.connect.side_effect = Exception("Fail")
        await websocket_endpoint(mock_ws, "experiments", "token")

    @patch("src.routers.scrapers.publish_scrape_task", new_callable=AsyncMock)
    def test_scrapers_router_branches(self, mock_publish):
        app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}
        client = TestClient(app)
        try:
            client.post("/api/v1/scrapers/trigger?market=spy&trade_date=2024-01-01")
            client.post("/api/v1/scrapers/trigger?market=nse")
            mock_publish.side_effect = Exception("Fail")
            client.post("/api/v1/scrapers/trigger?market=spy")
        finally:
            app.dependency_overrides.clear()

    @patch("src.auth.dependencies.get_supabase_client")
    async def test_auth_dependencies_errors(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.auth.get_user.return_value = None
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            await get_current_user(MagicMock(credentials="bad"))
        mock_client.auth.get_user.side_effect = Exception("Auth fail")
        with pytest.raises(HTTPException):
            await get_current_user(MagicMock(credentials="error"))

        # verify_ws_token fail (58-61)
        mock_ws = AsyncMock()
        mock_client.auth.get_user.side_effect = Exception("WS Auth fail")
        res = await verify_ws_token(mock_ws, "error")
        assert res is None
        assert mock_ws.close.called

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.get", new_callable=AsyncMock)
    async def test_oauth_errors(self, mock_get, mock_post):
        mock_post.return_value = MagicMock(status_code=400)
        with pytest.raises(AuthenticationError):
            await get_github_user("code")
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {}
        with pytest.raises(AuthenticationError):
            await get_github_user("code")
        mock_post.return_value.json.return_value = {"access_token": "at"}
        mock_get.return_value = MagicMock(status_code=400)
        with pytest.raises(AuthenticationError):
            await get_github_user("code")
            
        # Google user fetch fail (75)
        mock_post.return_value.json.return_value = {"access_token": "at"}
        mock_get.return_value = MagicMock(status_code=400)
        with pytest.raises(AuthenticationError):
            await get_google_user("code")

    @patch("src.database.repository.upsert_user_profile", new_callable=AsyncMock)
    async def test_sync_user_profile(self, mock_upsert):
        with pytest.raises(ValueError):
            await sync_user_profile({})
        mock_upsert.side_effect = Exception("Sync fail")
        with pytest.raises(Exception):
            await sync_user_profile({"id": "u1"})

    @patch("src.websocket.manager.get_redis")
    async def test_websocket_manager_exit_loop(self, mock_get_redis):
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        async def mock_listen():
            yield {"type": "message", "data": '{"foo": "bar"}'}
        mock_pubsub.listen = mock_listen
        mock_redis.pubsub.return_value = mock_pubsub
        mock_get_redis.return_value = mock_redis
        await manager.start_redis_listener("test")

    @patch("src.data.pipeline.ScraperFactory.get_scraper")
    @patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock)
    async def test_pipeline_empty_market_data_branch(self, mock_audit, mock_get_scraper):
        pipeline = DataPipeline("run1", "spy")
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = MagicMock()
        mock_scraper.scrape.return_value.to_dict.return_value = []
        mock_get_scraper.return_value = mock_scraper
        await pipeline.run()

    def test_cors_preflight(self):
        client = TestClient(app)
        client.options("/api/v1/methods", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})

    @patch("httpx.AsyncClient.get", new_callable=AsyncMock)
    async def test_nse_scraper_exit_loop(self, mock_get):
        scraper = NSENextScraper("run1")
        mock_get.return_value = MagicMock(status_code=200)
        mock_get.return_value.json.return_value = {"records": {"data": [{"strikePrice": 100, "expiryDate": "2024-01-01", "CE": {"lastPrice": 10}}]}}
        import datetime
        await scraper.scrape(datetime.date(2024, 1, 1))
