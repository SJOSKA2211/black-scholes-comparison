from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.statistics import compute_mape
from src.auth.dependencies import verify_ws_token
from src.data.transformers import transform_market_row
from src.notifications.hierarchy import notify_user
from src.scrapers.scraper_factory import ScraperFactory
from src.storage.storage_service import upload_export
from src.websocket.manager import WebSocketManager


@pytest.mark.unit
class TestDataTransformers:
    def test_transform_market_row_success(self) -> None:
        row = {
            "underlying_price": "100.0",
            "strike_price": 100,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }
        params = transform_market_row(row)
        assert params.underlying_price == 100.0


@pytest.mark.unit
class TestAnalysis:
    def test_compute_mape(self) -> None:
        results = [{"computed_price": 110}]
        assert compute_mape(results, 100) == 10.0


@pytest.mark.unit
class TestScraperFactory:
    def test_get_scraper(self) -> None:
        scraper = ScraperFactory.get_scraper("spy", "run-1")
        assert scraper.run_id == "run-1"

        with pytest.raises(ValueError):
            ScraperFactory.get_scraper("invalid", "run-1")


@pytest.mark.unit
class TestStorage:
    @patch("src.storage.storage_service.get_minio")
    def test_upload_export(self, mock_get_minio) -> None:
        mock_client = MagicMock()
        mock_get_minio.return_value = mock_client
        mock_client.presigned_get_object.return_value = "http://minio/url"

        url = upload_export(data=b"data", filename="test.csv", content_type="text/csv")
        assert url == "http://minio/url"
        mock_client.put_object.assert_called_once()


@pytest.mark.unit
class TestAuthDeps:
    @pytest.mark.asyncio
    @patch("src.auth.dependencies.get_supabase_client")
    async def test_verify_ws_token_success(self, mock_get_supabase) -> None:
        mock_ws = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_get_supabase.return_value.auth.get_user.return_value = MagicMock(user=mock_user)

        res = await verify_ws_token(mock_ws, "valid-token")
        assert res["id"] == "u1"

    @pytest.mark.asyncio
    async def test_verify_ws_token_missing(self) -> None:
        mock_ws = AsyncMock()
        res = await verify_ws_token(mock_ws, None)
        assert res is None
        mock_ws.close.assert_called_once()


@pytest.mark.unit
class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self) -> None:
        manager = WebSocketManager()
        ws = AsyncMock()
        await manager.connect(ws, "test")
        assert "test" in manager._connections
        await manager.disconnect(ws, "test")
        assert "test" not in manager._connections


@pytest.mark.unit
class TestNotifications:
    @pytest.mark.asyncio
    @patch("src.notifications.hierarchy.insert_notification", new_callable=AsyncMock)
    @patch("src.notifications.hierarchy.get_redis")
    async def test_notify_user(self, mock_get_redis, mock_insert_notif) -> None:
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        await notify_user("user-1", "T", "B")
        mock_insert_notif.assert_called_once()
