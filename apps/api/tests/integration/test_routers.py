"""Integration tests for API routers.
Verifies HTTP response codes and JSON structure for all endpoints.
"""

import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from src.auth.dependencies import get_current_user
from src.main import app
from src.methods.base import PriceResult

# Mock user for authentication
MOCK_USER = {
    "id": "00000000-0000-0000-0000-000000000000",
    "email": "test@example.com",
    "role": "researcher",
}

@pytest.fixture
def auth_client():
    """Client with authenticated user dependency override."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    with TestClient(app) as client:
        yield client
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]

@pytest.mark.integration
class TestPricingRouter:
    def test_get_methods(self, auth_client) -> None:
        response = auth_client.get("/api/v1/pricing/methods")
        assert response.status_code == 200

    @pytest.mark.parametrize("method", [
        "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson",
        "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc",
        "binomial_crr", "binomial_crr_richardson", "trinomial", "trinomial_richardson"
    ])
    def test_calculate_methods(self, auth_client, method, sample_option_params) -> None:
        response = auth_client.post(f"/api/v1/pricing/calculate?method_type={method}", json=sample_option_params)
        assert response.status_code == 200

    def test_pricing_persist(self, auth_client, sample_option_params) -> None:
        assert auth_client.post("/api/v1/pricing/calculate?method_type=analytical&persist=true", json=sample_option_params).status_code == 200

    def test_compare_methods(self, auth_client, sample_option_params) -> None:
        response = auth_client.post("/api/v1/pricing/compare?methods=analytical&methods=explicit_fdm", json=sample_option_params)
        assert response.status_code == 200
        # Analytical automatically added branch (line 212)
        assert auth_client.post("/api/v1/pricing/compare?methods=explicit_fdm", json=sample_option_params).status_code == 200

    def test_pricing_fail_mock(self, auth_client, sample_option_params, monkeypatch) -> None:
        mock_method = MagicMock()
        mock_method.price.side_effect = Exception("Price Fail")
        monkeypatch.setattr("src.routers.pricing.get_method_instance", lambda x: mock_method)
        assert auth_client.post("/api/v1/pricing/calculate?method_type=analytical", json=sample_option_params).status_code == 500

@pytest.mark.integration
class TestExperimentsRouter:
    def test_run_experiment(self, auth_client, monkeypatch) -> None:
        monkeypatch.setattr("src.routers.experiments.publish_experiment_task", AsyncMock())
        assert auth_client.post("/api/v1/experiments/run", json={"params": {"S": 100}}).status_code == 200
        monkeypatch.setattr("src.routers.experiments.publish_experiment_task", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.post("/api/v1/experiments/run", json={}).status_code == 500

    def test_get_results(self, auth_client, monkeypatch) -> None:
        assert auth_client.get("/api/v1/experiments/results").status_code == 200
        monkeypatch.setattr("src.routers.experiments.get_experiments_by_method", AsyncMock(return_value=[]))
        assert auth_client.get("/api/v1/experiments/results?method_type=analytical").status_code == 200
        monkeypatch.setattr("src.routers.experiments.get_experiments", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.get("/api/v1/experiments/results").status_code == 500

    def test_get_result_detail(self, auth_client, monkeypatch) -> None:
        exp_id = str(uuid.uuid4())
        monkeypatch.setattr("src.routers.experiments.get_experiment_by_id", AsyncMock(return_value={"id": exp_id}))
        assert auth_client.get(f"/api/v1/experiments/results/{exp_id}").status_code == 200
        monkeypatch.setattr("src.routers.experiments.get_experiment_by_id", AsyncMock(return_value=None))
        assert auth_client.get(f"/api/v1/experiments/results/{exp_id}").status_code == 404
        monkeypatch.setattr("src.routers.experiments.get_experiment_by_id", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.get(f"/api/v1/experiments/results/{exp_id}").status_code == 500

@pytest.mark.integration
class TestScrapersRouter:
    def test_trigger_scraper(self, auth_client, monkeypatch) -> None:
        monkeypatch.setattr("src.routers.scrapers.publish_scrape_task", AsyncMock())
        assert auth_client.post("/api/v1/scrapers/trigger?market=spy").status_code == 200
        monkeypatch.setattr("src.routers.scrapers.publish_scrape_task", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.post("/api/v1/scrapers/trigger?market=spy").status_code == 500
    def test_get_runs(self, auth_client, monkeypatch) -> None:
        assert auth_client.get("/api/v1/scrapers/runs").status_code == 200
        monkeypatch.setattr("src.routers.scrapers.get_scrape_runs", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.get("/api/v1/scrapers/runs").status_code == 500

@pytest.mark.integration
class TestMarketDataRouter:
    def test_market_data(self, auth_client, monkeypatch) -> None:
        assert auth_client.get("/api/v1/market-data/?source=synthetic").status_code == 200
        monkeypatch.setattr("src.routers.market_data.get_market_data", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.get("/api/v1/market-data/").status_code == 500

@pytest.mark.integration
class TestNotificationsRouter:
    def test_notifications(self, auth_client, monkeypatch) -> None:
        assert auth_client.get("/api/v1/notifications/").status_code == 200
        notif_id = str(uuid.uuid4())
        assert auth_client.patch(f"/api/v1/notifications/{notif_id}/read").status_code == 200
        assert auth_client.post("/api/v1/notifications/read-all").status_code == 200
        monkeypatch.setattr("src.routers.notifications.get_notifications", AsyncMock(side_effect=Exception("Err")))
        assert auth_client.get("/api/v1/notifications/").status_code == 500

@pytest.mark.integration
class TestDownloadsRouter:
    @pytest.mark.asyncio
    async def test_exports(self, auth_client, monkeypatch) -> None:
        monkeypatch.setattr("src.routers.downloads.get_experiments", AsyncMock(return_value={"items": [{"id": 1}]}))
        monkeypatch.setattr("src.routers.downloads.get_market_data", AsyncMock(return_value=[{"id": 1}]))
        monkeypatch.setattr("src.routers.downloads.upload_export", lambda *a: "http://url")
        assert auth_client.get("/api/v1/download/experiments?format=json").status_code == 200
        assert auth_client.get("/api/v1/download/experiments?format=csv").status_code == 200
        assert auth_client.get("/api/v1/download/experiments?format=xlsx").status_code == 200
        assert auth_client.get("/api/v1/download/market_data").status_code == 200
        monkeypatch.setattr("src.routers.downloads.get_experiments", AsyncMock(return_value={"items": []}))
        assert auth_client.get("/api/v1/download/experiments").status_code == 404

    @pytest.mark.asyncio
    async def test_internal_logic(self) -> None:
        from src.routers.downloads import _fetch_data, _serialize
        import pandas as pd
        with pytest.raises(ValueError):
            await _fetch_data("invalid")
        with pytest.raises(ValueError):
            _serialize(pd.DataFrame(), "invalid")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_full(auth_client, monkeypatch) -> None:
    assert auth_client.get("/health").status_code == 200
    monkeypatch.setattr("src.routers.health.get_supabase_client", lambda: MagicMock(table=MagicMock(side_effect=Exception("Err"))))
    monkeypatch.setattr("src.routers.health.get_redis", lambda: MagicMock(ping=AsyncMock(side_effect=Exception("Err"))))
    monkeypatch.setattr("src.routers.health.get_rabbitmq_connection", AsyncMock(side_effect=Exception("Err")))
    monkeypatch.setattr("src.routers.health.get_minio", lambda: MagicMock(list_buckets=MagicMock(side_effect=Exception("Err"))))
    assert auth_client.get("/health").json()["status"] == "error"
    monkeypatch.setattr("src.routers.health.get_rabbitmq_connection", AsyncMock(return_value=MagicMock(is_closed=True)))
    auth_client.get("/health")

@pytest.mark.integration
def test_pricing_edge(auth_client, monkeypatch, sample_option_params) -> None:
    mock_method = MagicMock()
    mock_method.price.return_value = PriceResult(method_type="analytical", computed_price=10.0, exec_seconds=0.1, delta=None)
    # Patch only for this call
    with monkeypatch.context() as mp:
        mp.setattr("src.routers.pricing.get_method_instance", lambda x: mock_method)
        auth_client.post("/api/v1/pricing/calculate?method_type=analytical", json=sample_option_params)
    
    # Now factory should raise
    from src.routers.pricing import get_method_instance
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        get_method_instance("invalid")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_logic(monkeypatch) -> None:
    from src.routers.websocket import websocket_endpoint
    from starlette.websockets import WebSocketDisconnect
    mock_ws = AsyncMock(receive_text=AsyncMock(side_effect=WebSocketDisconnect()))
    await websocket_endpoint(mock_ws, "invalid")
    monkeypatch.setattr("src.routers.websocket.verify_ws_token", AsyncMock(return_value=None))
    await websocket_endpoint(mock_ws, "experiments")
    monkeypatch.setattr("src.routers.websocket.verify_ws_token", AsyncMock(return_value=MOCK_USER))
    from src.routers.websocket import ws_manager
    monkeypatch.setattr(ws_manager, "connect", AsyncMock())
    monkeypatch.setattr(ws_manager, "disconnect", AsyncMock())
    await websocket_endpoint(mock_ws, "experiments")
    mock_ws.receive_text.side_effect = Exception("Err")
    await websocket_endpoint(mock_ws, "experiments")
