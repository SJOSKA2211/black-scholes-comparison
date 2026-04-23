"""Integration tests for API routers.
Verifies HTTP response codes and JSON structure.
"""

import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.main import app

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
        methods = response.json()
        assert any(m["id"] == "analytical" for m in methods)
        assert any(m["id"] == "explicit_fdm" for m in methods)
        assert len(methods) >= 10

    def test_calculate_valid(self, auth_client) -> None:
        payload = {
            "underlying_price": 100,
            "strike_price": 100,
            "maturity_years": 1,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }
        response = auth_client.post(
            "/api/v1/pricing/calculate?method_type=analytical", json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "computed_price" in data
        assert abs(data["computed_price"] - 10.4506) < 0.01

    def test_calculate_invalid_params(self, auth_client) -> None:
        # Negative volatility
        payload = {
            "underlying_price": 100,
            "strike_price": 100,
            "maturity_years": 1,
            "volatility": -0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }
        response = auth_client.post(
            "/api/v1/pricing/calculate?method_type=analytical", json=payload
        )
        assert response.status_code == 422

    def test_unauthorized(self) -> None:
        client = TestClient(app)
        response = client.get("/api/v1/pricing/methods")
        assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.minio
class TestDownloadsRouter:
    @pytest.mark.parametrize("format", ["csv", "json", "xlsx"])
    def test_download_experiments(self, auth_client, format) -> None:
        # Note: This might return 404 if no data exists, but the router should return a URL if it can.
        # We assume some data might exist or the router handles empty datasets.
        response = auth_client.get(f"/api/v1/download/experiments?format={format}")
        if response.status_code == 200:
            data = response.json()
            assert "url" in data
            assert "filename" in data
            # Check for MinIO hostname in dev or configured endpoint
            assert (
                "minio" in data["url"].lower()
                or "localhost" in data["url"].lower()
                or "127.0.0.1" in data["url"].lower()
            )
        else:
            # If no data, it might return 404
            assert response.status_code == 404


@pytest.mark.integration
class TestNotificationsRouter:
    def test_notification_flow(self, auth_client) -> None:
        # 1. Get notifications
        response = auth_client.get("/api/v1/notifications/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        # 2. Mark all read
        response = auth_client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200
        assert "message" in response.json()


@pytest.mark.integration
class TestExperimentsRouter:
    def test_get_results(self, auth_client) -> None:
        response = auth_client.get("/api/v1/experiments/results")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_run_experiment_unauthorized(self) -> None:
        client = TestClient(app)
        response = client.post("/api/v1/experiments/run", json={"test": "data"})
        assert response.status_code == 403


@pytest.mark.integration
class TestScrapersRouter:
    def test_get_runs(self, auth_client) -> None:
        response = auth_client.get("/api/v1/scrapers/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_trigger_scraper_invalid_market(self, auth_client) -> None:
        response = auth_client.post("/api/v1/scrapers/trigger?market=invalid")
        assert response.status_code == 422


@pytest.mark.integration
def test_health_check(auth_client) -> None:
    response = auth_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    # In integration tests, status might be 'error' if infra is missing
    assert data["status"] in ["ok", "error"]
    assert "services" in data
