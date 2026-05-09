"""Unit tests for remaining routers."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch, AsyncMock

@pytest.fixture
def client():
    # Use dependency override inside the fixture for isolation
    app.dependency_overrides[get_current_user] = mock_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_redis():
    with patch("src.cache.decorators.get_redis") as m:
        r = MagicMock()
        r.get = AsyncMock(return_value=None)
        r.setex = AsyncMock()
        r.ping = AsyncMock(return_value=True)
        m.return_value = r
        yield r

@pytest.mark.unit
def test_health():
    with patch("src.routers.health.get_supabase") as su:
        # Success path
        mock_table = MagicMock()
        mock_table.select.return_value.limit.return_value.execute = MagicMock()
        su.return_value.table.return_value = mock_table
        
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["db"] == "connected"
        
        # Fail path
        su.return_value.table.side_effect = Exception("err")
        res = client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["db"] == "disconnected"

@pytest.mark.unit
def test_experiments(client):
    with patch("src.routers.experiments.publish_experiment_task", AsyncMock()):
        res = client.post("/api/v1/experiments/run", json={"params": {"market": "spy"}})
        assert res.status_code == 200

@pytest.mark.unit
def test_market_data(client):
    with patch("src.routers.market_data.list_market_data", AsyncMock(return_value=[])):
        res = client.get("/api/v1/market-data")
        assert res.status_code == 200

@pytest.mark.unit
def test_notifications(client):
    with patch("src.routers.notifications.get_notifications", AsyncMock(return_value=[])), \
         patch("src.routers.notifications.mark_notification_read", AsyncMock()):
        res = client.get("/api/v1/notifications")
        assert res.status_code == 200
        res = client.patch("/api/v1/notifications/1/read")
        assert res.status_code == 200

@pytest.mark.unit
def test_notifications_no_user_id():
    app.dependency_overrides[get_current_user] = lambda: {"id": ""}
    res = client.get("/api/v1/notifications")
    assert res.status_code == 200
    assert res.json() == []
    app.dependency_overrides.clear()

@pytest.mark.unit
def test_scrapers(client):
    with patch("src.routers.scrapers.publish_scrape_task", AsyncMock()):
        res = client.post("/api/v1/scrapers/run?market=spy")
        assert res.status_code == 200

@pytest.mark.unit
def test_methods_list(client):
    res = client.get("/api/v1/pricing/methods")
    assert res.status_code == 200
    assert len(res.json()) > 0
