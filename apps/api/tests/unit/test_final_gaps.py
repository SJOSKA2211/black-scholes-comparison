import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime
from src.websocket.manager import WebSocketManager
from src.notifications.hierarchy import notify_user
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper
from src.main import lifespan
from src.cache.redis_client import get_redis

from src.analysis.convergence import analyze_convergence_order

@pytest.mark.unit
class TestAnalysisGaps:
    def test_analyze_convergence_order(self):
        # 1. Too few results
        assert analyze_convergence_order([]) == {"convergence_order": 0.0}
        assert analyze_convergence_order([{"error": 1.0}]) == {"convergence_order": 0.0}
        
        # 2. Linear convergence simulation
        # error = 1/resolution
        results = [
            {"parameter_set": {"num_steps": 10}, "error": 0.1},
            {"parameter_set": {"num_steps": 100}, "error": 0.01},
            {"parameter_set": {"num_steps": 1000}, "error": 0.001},
        ]
        res = analyze_convergence_order(results)
        # log(0.1) = -1, log(10) = 1
        # log(0.01) = -2, log(100) = 2
        # slope = (-2 - (-1)) / (2 - 1) = -1 / 1 = -1
        # order = -(-1) = 1.0
        assert pytest.approx(res["convergence_order"], 0.1) == 1.0
        
        # 3. Fallback resolution (dt)
        results_dt = [
            {"parameter_set": {"dt": 0.1}, "error": 0.1},
            {"parameter_set": {"dt": 0.01}, "error": 0.01},
        ]
        res_dt = analyze_convergence_order(results_dt)
        assert pytest.approx(res_dt["convergence_order"], 0.1) == 1.0
        
        # 4. Filtered cases (no resolution or zero error)
        results_bad = [
            {"error": 0}, # skip
            {"parameter_set": {"num_steps": 10}, "error": 1.0},
        ]
        assert analyze_convergence_order(results_bad) == {"convergence_order": 0.0}

@pytest.mark.unit
class TestWebsocketManagerGaps:
    @pytest.mark.asyncio
    async def test_broadcast_dead_connection(self):
        manager = WebSocketManager()
        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = Exception("Dead")
        
        await manager.connect(ws_good, "chan")
        await manager.connect(ws_bad, "chan")
        
        await manager.broadcast("chan", {"data": 1})
        
        ws_good.send_json.assert_called_once()
        assert ws_bad not in manager._connections["chan"]

    @pytest.mark.asyncio
    async def test_websocket_edge_cases(self):
        manager = WebSocketManager()
        # Disconnect non-existent channel
        await manager.disconnect(AsyncMock(), "invalid")
        # Broadcast non-existent channel
        await manager.broadcast("invalid", {})
        
        # Disconnect last client with no listener task
        ws = AsyncMock()
        manager._connections["chan"] = {ws}
        await manager.disconnect(ws, "chan")
        assert "chan" not in manager._connections

    @pytest.mark.asyncio
    async def test_redis_listener_error(self):
        manager = WebSocketManager()
        with patch("src.websocket.manager.get_redis") as mock_redis_func:
            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_redis_func.return_value = mock_redis
            mock_redis.pubsub.return_value = mock_pubsub
            
            # Simulate a failure in listen()
            mock_pubsub.listen.side_effect = Exception("Redis crash")
            
            await manager.start_redis_listener("error_chan")

    @pytest.mark.asyncio
    async def test_redis_listener_messages(self):
        manager = WebSocketManager()
        with patch("src.websocket.manager.get_redis") as mock_redis_func:
            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_redis_func.return_value = mock_redis
            mock_redis.pubsub.return_value = mock_pubsub
            
            # Mock listen as an async iterator
            async def mock_listen():
                yield {"type": "message", "data": "invalid-json"}
                yield {"type": "message", "data": json.dumps({"event": "test"})}
            
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.listen.return_value = mock_listen()
            
            # We need connections for broadcast to work
            ws = AsyncMock()
            manager._connections["chan"] = {ws}
            
            await manager.start_redis_listener("chan")
            ws.send_json.assert_called_once()

@pytest.mark.unit
class TestNotificationsGaps:
    @pytest.mark.asyncio
    @patch("src.notifications.hierarchy.insert_notification", new_callable=AsyncMock)
    @patch("src.notifications.hierarchy.get_redis")
    @patch("src.notifications.hierarchy.send_email", new_callable=AsyncMock)
    @patch("src.notifications.hierarchy.send_push_notification", new_callable=AsyncMock)
    async def test_notify_user_variants(self, mock_push, mock_email, mock_redis_func, mock_insert):
        mock_redis = AsyncMock()
        mock_redis_func.return_value = mock_redis
        
        # Test Critical Severity (triggers email)
        await notify_user("u1", "T", "B", severity="critical")
        mock_email.assert_called_once()
        
        # Test Push Channel
        await notify_user("u1", "T", "B", channel="push")
        mock_push.assert_called_once()
        
        # Test generic error
        mock_insert.side_effect = Exception("DB error")
        with pytest.raises(Exception):
            await notify_user("u1", "T", "B")

@pytest.mark.unit
class TestNotificationChannelsGaps:
    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    async def test_email_failures(self, mock_settings):
        from src.notifications.email import send_email
        mock_settings.return_value.smtp_server = "fail"
        # Should catch and log error
        await send_email("test@ex.com", "T", "B")
        
    @pytest.mark.asyncio
    @patch("src.notifications.push.get_settings")
    @patch("httpx.AsyncClient.post")
    async def test_push_failures(self, mock_post, mock_settings):
        from src.notifications.push import send_push_notification
        mock_settings.return_value.fcm_api_key = "key"
        mock_post.side_effect = Exception("HTTP fail")
        # Should catch and log error
        await send_push_notification("token", "T", "B")
        
        # Invalid response
        mock_post.side_effect = None
        mock_post.return_value = MagicMock(status_code=400, text="Error")
        await send_push_notification("token", "T", "B")

@pytest.mark.unit
class TestScrapersGaps:
    @pytest.mark.asyncio
    async def test_nse_scraper_failure(self):
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_p.return_value.__aenter__.side_effect = Exception("Browser fail")
            with pytest.raises(Exception):
                await scraper.scrape(date.today())

    @pytest.mark.asyncio
    async def test_nse_scraper_parsing(self):
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            p = mock_p.return_value.__aenter__.return_value
            p.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Mock selectors for parsing
            mock_page.query_selector.side_effect = [
                AsyncMock(inner_text=AsyncMock(return_value="UNDERLYING VALUE 22,000.00")), # underlying
                AsyncMock(get_attribute=AsyncMock(return_value="25-Apr-2024")), # expiry
            ]
            
            # Mock table rows - ensure inner_text is awaited properly
            mock_row = AsyncMock()
            mock_cols = [AsyncMock() for _ in range(25)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="10.5")
            
            mock_row.query_selector_all.return_value = mock_cols
            mock_page.query_selector_all.return_value = [mock_row]
            
            res = await scraper.scrape(date.today())
            assert len(res) > 0
            
            # Test empty parsing
            mock_page.query_selector.side_effect = None
            mock_page.query_selector.return_value = None
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_scraper_logic(self):
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            # Mock the whole playwright chain
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            p = mock_p.return_value.__aenter__.return_value
            p.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            # Mock data extraction
            mock_price_el = AsyncMock()
            mock_price_el.inner_text = AsyncMock(return_value="100.0")
            mock_page.query_selector.return_value = mock_price_el
            
            # Mock some rows
            mock_row = AsyncMock()
            mock_cols = [AsyncMock() for _ in range(15)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="1.23")
            mock_row.query_selector_all.return_value = mock_cols
            mock_page.query_selector_all.return_value = [mock_row]
            
            res = await scraper.scrape(date.today())
            assert len(res) > 0
            
            # Test numeric parsing logic (isdigit branch)
            mock_price_el.inner_text.return_value = "invalid"
            res = await scraper.scrape(date.today())
            assert len(res) > 0 # Should still return rows even if price parse fails or uses fallback

@pytest.mark.unit
class TestMainLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_variants(self):
        app = MagicMock()
        # 1. Generic Exception
        with patch("src.task_queues.consumer.start_consumers", side_effect=Exception("RMQ Down")):
            async with lifespan(app):
                pass 
        
        # 2. TimeoutError
        with patch("src.task_queues.consumer.start_consumers", side_effect=asyncio.TimeoutError()):
            async with lifespan(app):
                pass

@pytest.mark.unit
class TestAuthDepsGaps:
    @pytest.mark.asyncio
    async def test_verify_ws_token_empty(self):
        from src.auth.dependencies import verify_ws_token
        res = await verify_ws_token(MagicMock(), None)
        assert res["email"] == "researcher@example.com"
