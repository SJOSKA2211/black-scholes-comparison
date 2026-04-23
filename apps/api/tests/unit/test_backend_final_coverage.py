import asyncio
import datetime
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, verify_ws_token
from src.auth.oauth import get_github_user, get_google_user, sync_user_profile
from src.data.pipeline import DataPipeline
from src.database.repository import (
    get_experiments,
    get_market_data,
    get_notifications,
    upsert_option_parameters,
    upsert_user_profile,
)
from src.database.supabase_client import get_supabase_client
from src.exceptions import AuthenticationError, RepositoryError
from src.main import app
from src.task_queues.rabbitmq_client import get_rabbitmq_connection
from src.routers.websocket import websocket_endpoint
from src.scrapers.nse_next_scraper import NSEScraper
from src.websocket.manager import WebSocketManager

@pytest.mark.unit
async def test_upsert_option_parameters_error() -> None:
    with patch("src.database.repository.get_supabase_client") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.side_effect = Exception("DB Fail")
        with pytest.raises(RepositoryError):
            await upsert_option_parameters({"strike": 100})

async def test_get_experiments_branches() -> None:
    with patch("src.database.repository.get_supabase_client") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_response = MagicMock()
        mock_response.data = []
        mock_response.count = 0
        mock_client.table.return_value.select.return_value.range.return_value.order.return_value.execute.return_value = (
            mock_response
        )
        res = await get_experiments(method_type=None, market_source=None)
        assert res["total"] == 0
        mock_client.table.return_value.select.return_value.eq.return_value.range.return_value.order.return_value.execute.return_value = (
            mock_response
        )
        await get_experiments(method_type="analytical", market_source=None)

async def test_get_market_data_branches() -> None:
    with patch("src.database.repository.get_supabase_client") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
            []
        )
        await get_market_data("spy", trade_date=None, from_date=None, to_date=None, limit=100)

async def test_get_notifications_unread_branch() -> None:
    with patch("src.database.repository.get_supabase_client") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = (
            []
        )
        await get_notifications("u1", unread_only=False)

def test_supabase_client_direct() -> None:
    with patch("src.database.supabase_client.get_settings") as mock_settings:
        mock_settings.return_value.supabase_url = "http://test.com"
        mock_settings.return_value.supabase_key = "key"
        with patch("src.database.supabase_client.create_client") as mock_create:
            get_supabase_client.cache_clear()
            get_supabase_client()
            assert mock_create.called

async def test_rabbitmq_client_direct() -> None:
    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        await get_rabbitmq_connection()
        assert mock_connect.called

def test_startup_event() -> None:
    with (
        patch("src.storage.minio_client.get_minio") as mock_minio,
        patch("src.cache.redis_client.get_redis") as mock_redis,
        patch("src.task_queues.consumer.start_consumers", new_callable=AsyncMock) as mock_start,
    ):
        with TestClient(app):
            pass
        assert mock_minio.called
        assert mock_redis.called
        assert mock_start.called

async def test_websocket_endpoint_direct() -> None:
    with patch("src.auth.dependencies.get_supabase_client") as mock_get_supabase:
        with patch("src.routers.websocket.ws_manager", new_callable=AsyncMock) as mock_ws_manager:
            mock_ws = AsyncMock()
            mock_client = MagicMock()
            mock_get_supabase.return_value = mock_client
            mock_client.auth.get_user.return_value.user.id = "u1"
            mock_ws.receive_text.side_effect = asyncio.exceptions.CancelledError()
            try:
                await websocket_endpoint(mock_ws, "experiments", "token")
            except asyncio.exceptions.CancelledError:
                pass
            mock_ws.receive_text.side_effect = WebSocketDisconnect()
            await websocket_endpoint(mock_ws, "experiments", "token")
            assert mock_ws_manager.disconnect.called
            mock_ws = AsyncMock()
            await websocket_endpoint(mock_ws, "invalid", "token")
            assert mock_ws.close.called
            mock_ws = AsyncMock()
            mock_ws_manager.connect.side_effect = Exception("Fail")
            await websocket_endpoint(mock_ws, "experiments", "token")
            assert mock_ws_manager.disconnect.called
            mock_client.auth.get_user.return_value = None
            await websocket_endpoint(mock_ws, "experiments", "token")

def test_scrapers_router_branches() -> None:
    with patch("src.routers.scrapers.publish_scrape_task", new_callable=AsyncMock) as mock_publish:
        app.dependency_overrides[get_current_user] = lambda: {"id": "u1"}
        client = TestClient(app)
        try:
            client.post("/api/v1/scrapers/trigger?market=spy&trade_date=2024-01-01")
            client.post("/api/v1/scrapers/trigger?market=nse")
            mock_publish.side_effect = Exception("Fail")
            client.post("/api/v1/scrapers/trigger?market=spy")
        finally:
            app.dependency_overrides.clear()

async def test_auth_dependencies_errors() -> None:
    with patch("src.auth.dependencies.get_supabase_client") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.auth.get_user.return_value = None
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            await get_current_user(MagicMock(credentials="bad"))
        mock_client.auth.get_user.side_effect = Exception("Auth fail")
        with pytest.raises(HTTPException):
            await get_current_user(MagicMock(credentials="error"))
        mock_ws = AsyncMock()
        mock_client.auth.get_user.side_effect = Exception("WS Auth fail")
        res = await verify_ws_token(mock_ws, "error")
        assert res is None
        assert mock_ws.close.called

async def test_oauth_errors() -> None:
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_post.return_value = MagicMock(status_code=400)
            with pytest.raises(AuthenticationError):
                await get_github_user("code")
            mock_post.return_value = MagicMock(status_code=200)
            mock_post.return_value.json.return_value = {"error": "bad"}
            with pytest.raises(AuthenticationError):
                await get_github_user("code")
            mock_post.return_value.json.return_value = {"access_token": "at"}
            mock_get.return_value = MagicMock(status_code=404)
            with pytest.raises(AuthenticationError):
                await get_github_user("code")
            mock_post.return_value = MagicMock(status_code=500)
            with pytest.raises(AuthenticationError):
                await get_google_user("code")
            mock_post.return_value = MagicMock(status_code=200)
            mock_post.return_value.json.return_value = {"error": "bad"}
            with pytest.raises(AuthenticationError):
                await get_google_user("code")
            mock_post.return_value.json.return_value = {"access_token": "at"}
            mock_get.return_value = MagicMock(status_code=401)
            with pytest.raises(AuthenticationError):
                await get_google_user("code")

async def test_sync_user_profile() -> None:
    with patch("src.database.repository.upsert_user_profile", new_callable=AsyncMock) as mock_upsert:
        with pytest.raises(ValueError):
            await sync_user_profile({})
        mock_upsert.side_effect = Exception("Sync fail")
        with pytest.raises(Exception):
            await sync_user_profile({"id": "u1"})
        mock_upsert.side_effect = None
        mock_upsert.return_value = {"id": "u1"}
        await sync_user_profile({"id": "u1", "email": "test@test.com"})

async def test_websocket_manager_exit_loop() -> None:
    with patch("src.websocket.manager.get_redis") as mock_get_redis:
        manager = WebSocketManager()
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        async def mock_listen() -> Generator[dict[str, Any], None, None]:
            yield {"type": "message", "data": '{"foo": "bar"}'}
        mock_pubsub.listen = mock_listen
        mock_redis.pubsub.return_value = mock_pubsub
        mock_get_redis.return_value = mock_redis
        await manager.start_redis_listener("test")

async def test_pipeline_empty_market_data_branch() -> None:
    with patch("src.data.pipeline.ScraperFactory.get_scraper") as mock_get_scraper:
        with patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock) as mock_audit:
            pipeline = DataPipeline("run1", "spy")
            mock_scraper = AsyncMock()
            mock_scraper.scrape.return_value = MagicMock()
            mock_scraper.scrape.return_value.to_dict.return_value = []
            mock_get_scraper.return_value = mock_scraper
            await pipeline.run()

def test_cors_preflight() -> None:
    client = TestClient(app)
    client.options("/api/v1/methods", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})

async def test_nse_scraper_branches() -> None:
    with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
        scraper = NSEScraper("run1")
        mock_browser = AsyncMock()
        mock_p.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_val_elem = AsyncMock()
        mock_val_elem.inner_text.return_value = "Underlying: 22000"
        mock_expiry_elem = AsyncMock()
        mock_expiry_elem.get_attribute.return_value = "25-Apr-2024"
        async def mock_qs(sel):
            if sel == "#equity_underlyingVal": return mock_val_elem
            if sel == "#expirySelect": return mock_expiry_elem
            return None
        mock_page.query_selector.side_effect = mock_qs
        mock_row = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(21)]
        for i, col in enumerate(mock_cols):
            col.inner_text.return_value = "100" if i in [11, 8, 9, 12, 13] else "10"
        mock_row.query_selector_all.return_value = mock_cols
        mock_page.query_selector_all.return_value = [mock_row]
        await scraper.scrape(datetime.date(2024, 1, 1))
        mock_page.goto.side_effect = Exception("Fail")
        with pytest.raises(Exception):
            await scraper.scrape(datetime.date(2024, 1, 1))
