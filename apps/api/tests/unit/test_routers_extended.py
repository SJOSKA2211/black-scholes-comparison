"""Unit tests for remaining routers."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch, AsyncMock

client = TestClient(app)

def mock_user(): return {"id": "u1"}

@pytest.mark.unit
def test_health():
    with patch("src.routers.health.get_supabase") as su, \
         patch("src.routers.health.get_redis") as re:
        # Success path
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute = AsyncMock()
        su.return_value.table.return_value = mock_table
        re.return_value.ping = AsyncMock(return_value=True)
        
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        
        # Fail path
        re.return_value.ping.side_effect = Exception("err")
        res = client.get("/api/v1/health")
        assert res.status_code == 503

@pytest.mark.unit
def test_experiments():
    app.dependency_overrides[get_current_user] = mock_user
    with patch("src.routers.experiments.publish_experiment_task", AsyncMock()):
        res = client.post("/api/v1/experiments/run", json={"params": {"market": "spy"}})
        assert res.status_code == 200
    app.dependency_overrides.clear()

@pytest.mark.unit
def test_market_data():
    app.dependency_overrides[get_current_user] = mock_user
    with patch("src.routers.market_data.list_market_data", AsyncMock(return_value=[])):
        res = client.get("/api/v1/market-data")
        assert res.status_code == 200
    app.dependency_overrides.clear()

@pytest.mark.unit
def test_notifications():
    app.dependency_overrides[get_current_user] = mock_user
    with patch("src.routers.notifications.list_notifications", AsyncMock(return_value=[])), \
         patch("src.routers.notifications.mark_notification_read", AsyncMock()):
        res = client.get("/api/v1/notifications")
        assert res.status_code == 200
        res = client.patch("/api/v1/notifications/1/read")
        assert res.status_code == 200
        
        # Error path
        with patch("src.routers.notifications.list_notifications", AsyncMock(side_effect=Exception("err"))):
            res = client.get("/api/v1/notifications")
            assert res.status_code == 500
    app.dependency_overrides.clear()

@pytest.mark.unit
def test_scrapers():
    app.dependency_overrides[get_current_user] = mock_user
    with patch("src.routers.scrapers.publish_scrape_task", AsyncMock()):
        res = client.post("/api/v1/scrapers/run?market=spy")
        assert res.status_code == 200
    app.dependency_overrides.clear()

@pytest.mark.unit
def test_methods_list():
    res = client.get("/api/v1/pricing/methods"); assert res.status_code == 200
