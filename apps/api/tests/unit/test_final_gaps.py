import asyncio
import json
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.convergence import analyze_convergence_order
from src.cache.redis_client import get_redis
from src.main import lifespan
from src.notifications.hierarchy import notify_user
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper
from src.websocket.manager import WebSocketManager
from src.database.supabase_client import get_supabase_client
from src.main import app as fastapi_app

pytestmark = pytest.mark.unit


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
            {"error": 0},  # skip
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

    @pytest.mark.asyncio
    async def test_redis_listener_coroutine_and_types(self):
        """Cover lines 87 (iscoroutine) and 89->88 (non-message types)."""
        manager = WebSocketManager()
        with patch("src.websocket.manager.get_redis") as mock_redis_func:
            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_redis_func.return_value = mock_redis
            mock_redis.pubsub.return_value = mock_pubsub

            # Mock listen() returning a coroutine that returns an iterator (line 87)
            async def wrap_listen():
                async def mock_iter():
                    yield {"type": "subscribe"}  # Hits 89->88 branch
                    yield {"type": "message", "data": json.dumps({"test": 1})}

                return mock_iter()

            mock_pubsub.listen.return_value = wrap_listen()
            mock_pubsub.subscribe = AsyncMock()

            ws = AsyncMock()
            manager._connections["chan"] = {ws}
            await manager.start_redis_listener("chan")
            ws.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_listener_cancelled(self):
        """Cover line 96 (CancelledError)."""
        manager = WebSocketManager()
        with patch("src.websocket.manager.get_redis") as mock_redis_func:
            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_redis_func.return_value = mock_redis
            mock_redis.pubsub.return_value = mock_pubsub

            async def mock_listen():
                raise asyncio.CancelledError()
                yield {}

            mock_pubsub.listen.return_value = mock_listen()
            mock_pubsub.subscribe = AsyncMock()
            await manager.start_redis_listener("chan")


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
    async def test_email_no_api_key(self, mock_settings):
        from src.notifications.email import send_email

        mock_settings.return_value.resend_api_key = ""
        result = await send_email("test@ex.com", "Subject", "Body")
        assert result is False

    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    @patch("src.notifications.email.resend")
    async def test_email_success(self, mock_resend, mock_settings):
        from src.notifications.email import send_email

        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_resend.Emails.send.return_value = MagicMock(id="msg_123")
        result = await send_email("test@ex.com", "Subject", "Body")
        assert result is True

    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    async def test_email_exception(self, mock_settings):
        from src.notifications.email import send_email

        mock_settings.return_value.resend_api_key = "re_test_key"
        mock_settings.side_effect = Exception("Config error")
        result = await send_email("test@ex.com", "Subject", "Body")
        assert result is False

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_no_subscriptions(self, mock_repo):
        from src.notifications.push import send_push_notification

        mock_repo.get_push_subscriptions = AsyncMock(return_value=[])
        result = await send_push_notification("user1", "Title", "Body")
        assert result is False

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_valid_subscriptions(self, mock_repo):
        from src.notifications.push import send_push_notification

        mock_repo.get_push_subscriptions = AsyncMock(
            return_value=[
                {"subscription_info": {"endpoint": "https://push.example.com"}},
            ]
        )
        result = await send_push_notification("user1", "Title", "Body")
        assert result is True

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_invalid_subscription(self, mock_repo):
        from src.notifications.push import send_push_notification

        mock_repo.get_push_subscriptions = AsyncMock(
            return_value=[
                {"subscription_info": None},  # triggers ValueError branch
            ]
        )
        result = await send_push_notification("user1", "Title", "Body")
        assert result is False

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_outer_exception(self, mock_repo):
        from src.notifications.push import send_push_notification

        mock_repo.get_push_subscriptions = AsyncMock(side_effect=Exception("DB down"))
        result = await send_push_notification("user1", "Title", "Body")
        assert result is False


@pytest.mark.unit
class TestScrapersGaps:
    """Covers scraper parsing branches: short rows, ValueError, expiry, run()."""

    def _mock_playwright_chain(self, mock_p):
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        p = mock_p.return_value.__aenter__.return_value
        p.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_context.new_page = AsyncMock(return_value=mock_page)
        return mock_browser, mock_page

    # ── NSE Tests ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_nse_scraper_failure(self):
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            # Mock launch to raise, which is inside the try block
            mock_p.return_value.__aenter__.return_value.chromium.launch.side_effect = Exception(
                "Browser fail"
            )
            with pytest.raises(Exception):
                await scraper.scrape(date.today())

    @pytest.mark.asyncio
    async def test_nse_happy_path(self):
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_cols = [AsyncMock() for _ in range(25)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="10.5")
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    AsyncMock(inner_text=AsyncMock(return_value="UNDERLYING VALUE 22,000.00")),
                    AsyncMock(get_attribute=AsyncMock(return_value="25-Apr-2024")),
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert len(res) > 0

    @pytest.mark.asyncio
    async def test_nse_empty_selected_val(self):
        """Cover line 63->75 (selected_val is empty)."""
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    AsyncMock(inner_text=AsyncMock(return_value="UNDERLYING VALUE 22,000.00")),
                    AsyncMock(get_attribute=AsyncMock(return_value="")),  # Empty selected_val
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_nse_zero_ask_skipped(self):
        """Cover lines 109->126 and 126->76 (ask = 0)."""
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_cols = [AsyncMock() for _ in range(25)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="0")  # All zeros
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_nse_short_row_skipped(self):
        """Rows with < 20 cols trigger continue (line 79)."""
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            short_cols = [AsyncMock() for _ in range(5)]  # < 20
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=short_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_nse_parsing_valueerror(self):
        """ValueError in float parse triggers continue (line 143-144)."""
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_cols = [AsyncMock() for _ in range(25)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="NOT_A_NUMBER")
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_nse_expiry_invalid_date(self):
        """Invalid date string in expiry triggers ValueError pass (line 71-72)."""
        scraper = NSEScraper("run-nse")
        with patch("src.scrapers.nse_next_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    AsyncMock(inner_text=AsyncMock(return_value="UNDERLYING VALUE 22,000.00")),
                    AsyncMock(get_attribute=AsyncMock(return_value="INVALID-DATE")),
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[])
            res = await scraper.scrape(date.today())
            assert isinstance(res, list)

    @pytest.mark.asyncio
    async def test_nse_run_method(self):
        """Cover the run() method (line 162)."""
        scraper = NSEScraper("run-nse")
        await scraper.run()

    # ── SPY Tests ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_spy_happy_path(self):
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            # 15 cols so len(cols) >= 10
            mock_cols = [AsyncMock() for _ in range(15)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="1.23")
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_row.evaluate = AsyncMock(return_value="calls-table")

            mock_price_el = AsyncMock(inner_text=AsyncMock(return_value="500.0"))
            mock_expiry_el = AsyncMock(get_attribute=AsyncMock(return_value="1720000000"))
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    mock_price_el,
                    mock_price_el,
                    mock_price_el,  # price selectors
                    mock_expiry_el,  # expiry selector
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert len(res) > 0

    @pytest.mark.asyncio
    async def test_spy_underlying_valueerror(self):
        """Cover line 56-57 (ValueError in price parsing)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_el = AsyncMock(inner_text=AsyncMock(return_value="NOT_A_FLOAT"))
            mock_page.query_selector = AsyncMock(return_value=mock_el)
            mock_page.query_selector_all = AsyncMock(return_value=[])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_invalid_val_isdigit(self):
        """Cover line 69->78 (val.isdigit() is false)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_expiry_el = AsyncMock(get_attribute=AsyncMock(return_value="abc"))  # Not isdigit
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    None,
                    None,
                    None,  # price
                    mock_expiry_el,  # expiry
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_zero_ask_skipped(self):
        """Cover line 99->79 (ask = 0)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_cols = [AsyncMock() for _ in range(15)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="0")
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_short_row_skipped(self):
        """Rows with < 10 cols trigger continue (line 82)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            short_cols = [AsyncMock() for _ in range(5)]  # < 10
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=short_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_parsing_valueerror(self):
        """ValueError in float parse triggers continue (line 124-125)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_cols = [AsyncMock() for _ in range(15)]
            for col in mock_cols:
                col.inner_text = AsyncMock(return_value="NOT_NUM")
            mock_row = AsyncMock()
            mock_row.query_selector_all = AsyncMock(return_value=mock_cols)
            mock_page.query_selector = AsyncMock(return_value=None)
            mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
            res = await scraper.scrape(date.today())
            assert res == []

    @pytest.mark.asyncio
    async def test_spy_expiry_isdigit_branch(self):
        """Cover val.isdigit() true path (line 69-75)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_expiry_el = AsyncMock(get_attribute=AsyncMock(return_value="1720000000"))
            mock_page.query_selector = AsyncMock(
                side_effect=[
                    None,
                    None,
                    None,  # price selectors all miss
                    mock_expiry_el,
                ]
            )
            mock_page.query_selector_all = AsyncMock(return_value=[])
            res = await scraper.scrape(date.today())
            assert isinstance(res, list)

    @pytest.mark.asyncio
    async def test_spy_outer_exception(self):
        """Cover outer exception re-raise (lines 135-137)."""
        scraper = SPYScraper("run-spy")
        with patch("src.scrapers.spy_scraper.async_playwright") as mock_p:
            mock_browser, mock_page = self._mock_playwright_chain(mock_p)
            mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
            with pytest.raises(Exception, match="Network error"):
                await scraper.scrape(date.today())

    @pytest.mark.asyncio
    async def test_spy_run_method(self):
        """Cover the run() method (line 143)."""
        scraper = SPYScraper("run-spy")
        await scraper.run()


@pytest.mark.unit
class TestMainLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_variants(self):
        app = MagicMock()
        # 1. Generic Exception
        with patch("src.main.start_consumers", side_effect=Exception("RMQ Down")):
            async with lifespan(app):
                pass

        # 2. TimeoutError
        with patch("src.main.start_consumers", side_effect=asyncio.TimeoutError()):
            async with lifespan(app):
                pass


@pytest.mark.unit
class TestAuthDepsGaps:
    @pytest.mark.asyncio
    async def test_verify_ws_token_empty(self):
        from src.auth.dependencies import verify_ws_token

        res = await verify_ws_token(MagicMock(), None)
        assert res["email"] == "researcher@example.com"


@pytest.mark.unit
class TestPricingRouterGaps:
    @pytest.mark.asyncio
    async def test_compare_no_analytical_reference(self, monkeypatch):
        """Cover branch 227->232 in pricing.py where analytical result is missing."""
        from src.methods.base import OptionParams, PriceResult
        from src.routers.pricing import CompareRequest, compare_methods

        params = OptionParams(
            underlying_price=100.0,
            strike_price=100.0,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        request = CompareRequest(params=params, methods=["analytical"])

        # Mock get_method_instance to return something that returns a non-analytical method_type
        mock_method = MagicMock()
        mock_method.price.return_value = PriceResult(
            method_type="explicit_fdm", computed_price=10.0, exec_seconds=0.1
        )

        with patch("src.routers.pricing.get_method_instance", return_value=mock_method):
            # Bypass cache
            monkeypatch.setattr("src.routers.pricing.cache_response", lambda **kw: lambda fn: fn)

            # Call the unwrapped function to bypass decorator logic and get the model directly
            res = await compare_methods.__wrapped__(request)
            assert res.analytical_reference == 0.0

@pytest.mark.unit
class TestSupabaseGaps:
    def test_get_supabase_client_missing_env(self, monkeypatch):
        from src.database.supabase_client import get_supabase_client
        # Clear lru_cache for testing
        get_supabase_client.cache_clear()
        monkeypatch.setenv("SUPABASE_URL", "")
        monkeypatch.setenv("SUPABASE_KEY", "")
        # Reset settings
        from src.config import get_settings
        get_settings.cache_clear()
        
        with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_KEY must be set."):
            get_supabase_client()
        
        # Cleanup
        get_settings.cache_clear()
        get_supabase_client.cache_clear()

@pytest.mark.unit
class TestMainGaps:
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        from fastapi.testclient import TestClient
        client = TestClient(fastapi_app)
        response = client.get("/")
        assert response.status_code == 200
        assert "Production Stable" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_lifespan_success(self, monkeypatch):
        from src.main import lifespan
        mock_app = MagicMock()
        # Mock dependencies to avoid real infra
        monkeypatch.setattr("src.cache.redis_client.get_redis", MagicMock())
        monkeypatch.setattr("src.storage.minio_client.get_minio", MagicMock())
        
        with patch("src.main.start_consumers", new_callable=AsyncMock) as mock_start:
            async with lifespan(mock_app):
                pass
            mock_start.assert_called_once()

@pytest.mark.unit
class TestRouterErrors:
    """Cover error paths in routers (raising 404, 500, etc)."""
    
    @pytest.mark.asyncio
    async def test_health_error(self, monkeypatch):
        from src.routers.health import health_check
        # Patch clients to throw exceptions
        mock_supabase = MagicMock()
        mock_supabase.table.side_effect = Exception("DB Fail")
        
        with patch("src.routers.health.get_supabase_client", return_value=mock_supabase):
            mock_redis = MagicMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Redis Fail"))
            with patch("src.routers.health.get_redis", return_value=mock_redis):
                res = await health_check()
                assert res["status"] == "error"
                assert "DB Fail" in res["services"]["database"]

    @pytest.mark.asyncio
    async def test_experiments_detail_missing(self, monkeypatch):
        from src.routers.experiments import get_result_detail
        from src.exceptions import RepositoryError
        # Code raises 500 for generic Exception/RepositoryError
        with patch("src.database.repository.get_experiment_by_id", side_effect=RepositoryError("Not found")):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await get_result_detail("fake-id")
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_notifications_read_error(self, monkeypatch):
        from src.routers.notifications import acknowledge_notification
        from src.exceptions import RepositoryError
        with patch("src.database.repository.mark_notification_read", side_effect=RepositoryError("DB Fail")):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await acknowledge_notification("fake-id")
            assert exc.value.status_code == 500

@pytest.mark.unit
class TestPricingErrors:
    @pytest.mark.asyncio
    async def test_calculate_price_error(self, monkeypatch):
        from src.routers.pricing import calculate_price
        from src.methods.base import OptionParams
        params = OptionParams(underlying_price=100, strike_price=100, maturity_years=1, volatility=0.2, risk_free_rate=0.05, option_type="call")
        with patch("src.routers.pricing.get_method_instance", side_effect=Exception("Calc Boom")):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await calculate_price.__wrapped__(params, method_type="analytical")
            assert exc.value.status_code == 500

    @pytest.mark.asyncio
    async def test_compare_methods_error(self, monkeypatch):
        from src.routers.pricing import CompareRequest, compare_methods
        from src.methods.base import OptionParams
        params = OptionParams(underlying_price=100, strike_price=100, maturity_years=1, volatility=0.2, risk_free_rate=0.05, option_type="call")
        req = CompareRequest(params=params, methods=["analytical"])
        with patch("src.routers.pricing.get_method_instance", side_effect=Exception("Comp Boom")):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc:
                await compare_methods.__wrapped__(req)
            assert exc.value.status_code == 500

@pytest.mark.unit
class TestWebSocketGaps:
    @pytest.mark.asyncio
    async def test_websocket_endpoint_invalid_channel(self):
        from src.routers.websocket import websocket_endpoint
        mock_ws = AsyncMock()
        # Should call close, not raise HTTPException
        await websocket_endpoint(mock_ws, "invalid_channel_name")
        mock_ws.close.assert_called_once_with(code=4004, reason="Unknown channel")

    @pytest.mark.asyncio
    async def test_websocket_endpoint_disconnect(self):
        from src.routers.websocket import websocket_endpoint
        from fastapi import WebSocketDisconnect
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
        # verify_ws_token needs to be mocked to return a user
        with patch("src.routers.websocket.verify_ws_token", return_value={"id": "uid"}):
            await websocket_endpoint(mock_ws, "experiments")
        # ws_manager.connect should have been called
        mock_ws.receive_text.assert_called()

@pytest.mark.unit
class TestPipelineGaps:
    @pytest.mark.asyncio
    async def test_pipeline_run_no_date(self, monkeypatch):
        from src.data.pipeline import get_pipeline
        import uuid
        valid_uuid = str(uuid.uuid4())
        
        # Patching repository methods WHERE THEY ARE USED (in src.data.pipeline)
        with patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {"id": valid_uuid}
            with patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock):
                pipeline = get_pipeline("spy", run_id=valid_uuid)
                mock_scraper = MagicMock()
                mock_scraper.scrape = AsyncMock(return_value=[])
                with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper", return_value=mock_scraper):
                    res = await pipeline.run()
                    assert res["status"] == "success"

@pytest.mark.unit
class TestPricingMethodsCoverage:
    def test_get_method_instance_all(self):
        from src.routers.pricing import get_method_instance
        methods = [
            "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson",
            "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc",
            "binomial_crr", "binomial_crr_richardson", "trinomial", "trinomial_richardson"
        ]
        for m in methods:
            assert get_method_instance(m) is not None
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            get_method_instance("invalid")
        assert exc.value.status_code == 400

@pytest.mark.unit
class TestRepositoryErrorPaths:
    @pytest.mark.asyncio
    async def test_repository_exceptions(self, monkeypatch):
        from src.database import repository
        from src.exceptions import RepositoryError
        
        # Mock supabase to throw
        mock_supabase = MagicMock()
        mock_supabase.table.side_effect = Exception("DB Boom")
        monkeypatch.setattr("src.database.repository.get_supabase_client", lambda: mock_supabase)
        
        with pytest.raises(RepositoryError):
            await repository.get_user_profile("uid")
        with pytest.raises(RepositoryError):
            await repository.upsert_user_profile({"id": "uid"})
        with pytest.raises(RepositoryError):
            await repository.get_market_data("spy")
        with pytest.raises(RepositoryError):
            await repository.get_experiments()
        with pytest.raises(RepositoryError):
            await repository.get_experiment_by_id("eid")
        with pytest.raises(RepositoryError):
            await repository.get_push_subscriptions("uid")
        with pytest.raises(RepositoryError):
            await repository.delete_push_subscription("sid")
        with pytest.raises(RepositoryError):
            await repository.get_experiments_by_method("analytical")

