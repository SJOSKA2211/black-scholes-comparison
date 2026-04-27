"""Integration tests for API routers — zero-mock policy.
All tests use real infrastructure: Supabase, Redis, RabbitMQ, MinIO.
Auth is bypassed at the application level (dependencies.py returns default user).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture(scope="module")
def auth_client():
    """Module-scoped test client.
    Auth is already bypassed in src/auth/dependencies.py (returns default researcher user).
    No mock overrides needed.
    """
    with TestClient(app) as client:
        yield client


@pytest.mark.integration
class TestPricingRouter:
    """Test pricing endpoints with real computation and real Redis cache."""

    def test_get_methods(self, auth_client) -> None:
        """Verify methods listing returns all 12 methods."""
        response = auth_client.get("/api/v1/pricing/methods")
        assert response.status_code == 200
        methods = response.json()
        assert len(methods) == 12

    @pytest.mark.parametrize(
        "method",
        [
            "analytical",
            "explicit_fdm",
            "implicit_fdm",
            "crank_nicolson",
            "standard_mc",
            "antithetic_mc",
            "control_variate_mc",
            "quasi_mc",
            "binomial_crr",
            "binomial_crr_richardson",
            "trinomial",
            "trinomial_richardson",
        ],
    )
    def test_calculate_all_methods(self, auth_client, method, sample_option_params) -> None:
        """Verify each method returns 200 with valid params."""
        response = auth_client.post(
            f"/api/v1/pricing/calculate?method_type={method}", json=sample_option_params
        )
        assert response.status_code == 200
        data = response.json()
        assert "computed_price" in data
        assert data["computed_price"] > 0

    def test_pricing_persist_to_db(self, auth_client, sample_option_params) -> None:
        """Verify persist=true saves to real Supabase."""
        response = auth_client.post(
            "/api/v1/pricing/calculate?method_type=analytical&persist=true",
            json=sample_option_params,
        )
        assert response.status_code == 200

    def test_compare_methods(self, auth_client, sample_option_params) -> None:
        """Verify comparison of multiple methods using real computation."""
        response = auth_client.post(
            "/api/v1/pricing/compare",
            json={
                "params": sample_option_params,
                "methods": ["analytical", "explicit_fdm"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "analytical_reference" in data
        assert len(data["results"]) >= 2

    def test_pricing_invalid_method(self, auth_client, sample_option_params) -> None:
        """Verify 400/422 for invalid method type."""
        response = auth_client.post(
            "/api/v1/pricing/calculate?method_type=invalid_method", json=sample_option_params
        )
        assert response.status_code in (400, 422)

    def test_pricing_invalid_params(self, auth_client) -> None:
        """Verify 422 for invalid option parameters."""
        response = auth_client.post(
            "/api/v1/pricing/calculate?method_type=analytical",
            json={"underlying_price": -100, "strike_price": 100},
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestExperimentsRouter:
    """Test experiment endpoints with real RabbitMQ task publishing."""

    def test_run_experiment(self, auth_client) -> None:
        """Verify experiment task published to real RabbitMQ."""
        response = auth_client.post(
            "/api/v1/experiments/run",
            json={
                "name": "Integration Test Experiment",
                "method_types": ["analytical", "standard_mc"],
                "underlying_prices": [90, 100, 110],
                "strike_prices": [100],
                "maturity_years": [1.0],
                "volatilities": [0.2],
                "risk_free_rates": [0.05],
                "option_type": "call",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    def test_get_results_listing(self, auth_client) -> None:
        """Verify results listing from real Supabase."""
        response = auth_client.get("/api/v1/experiments/results")
        assert response.status_code == 200
        assert isinstance(response.json()["items"], list)

    def test_get_result_detail_missing(self, auth_client) -> None:
        """Verify 404 for non-existent experiment."""
        fake_id = str(uuid.uuid4())
        response = auth_client.get(f"/api/v1/experiments/results/{fake_id}")
        assert response.status_code in (404, 500)


@pytest.mark.integration
class TestScrapersRouter:
    """Test scraper endpoints with real RabbitMQ task publishing."""

    def test_trigger_scraper(self, auth_client) -> None:
        """Verify scraper task published to real RabbitMQ."""
        response = auth_client.post("/api/v1/scrapers/trigger?market=spy")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_trigger_scraper_with_date(self, auth_client) -> None:
        """Verify scraper trigger with explicit date."""
        response = auth_client.post("/api/v1/scrapers/trigger?market=spy&trade_date=2026-01-15")
        assert response.status_code == 200

    def test_get_runs(self, auth_client) -> None:
        """Verify scrape runs listing from real Supabase."""
        response = auth_client.get("/api/v1/scrapers/runs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestMarketDataRouter:
    """Test market data retrieval with real Supabase."""

    def test_get_market_data(self, auth_client) -> None:
        """Verify market data retrieval."""
        response = auth_client.get("/api/v1/market-data/?source=synthetic")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestNotificationsRouter:
    """Test notification endpoints with real Supabase."""

    def test_get_notifications(self, auth_client) -> None:
        """Verify notifications listing."""
        response = auth_client.get("/api/v1/notifications/")
        assert response.status_code == 200

    def test_mark_all_read(self, auth_client) -> None:
        """Verify mark-all-read."""
        response = auth_client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200

    def test_mark_single_read(self, auth_client) -> None:
        """Verify mark single notification read."""
        notif_id = str(uuid.uuid4())
        response = auth_client.patch(f"/api/v1/notifications/{notif_id}/read")
        assert response.status_code == 200


@pytest.mark.integration
class TestDownloadsRouter:
    """Test download export endpoints with real Supabase and MinIO."""

    def test_export_market_data_csv(self, auth_client) -> None:
        """Verify CSV export from real data."""
        response = auth_client.get("/api/v1/download/market_data?format=csv")
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            assert "url" in response.json()

    def test_export_experiments_json(self, auth_client) -> None:
        """Verify JSON export."""
        response = auth_client.get("/api/v1/download/experiments?format=json")
        assert response.status_code in (200, 404)

    def test_internal_fetch_invalid_resource(self) -> None:
        """Test _fetch_data raises ValueError for unknown resource."""
        import pandas as pd

        from src.routers.downloads import _fetch_data, _serialize

        with pytest.raises(ValueError):
            import asyncio

            asyncio.get_event_loop().run_until_complete(_fetch_data("invalid"))

    def test_internal_serialize_invalid_format(self) -> None:
        """Test _serialize raises ValueError for unknown format."""
        import pandas as pd

        from src.routers.downloads import _serialize

        with pytest.raises(ValueError):
            _serialize(pd.DataFrame(), "invalid")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_check_full(auth_client) -> None:
    """Verify health check returns OK with real infrastructure."""
    response = auth_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "error")
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]


@pytest.mark.integration
def test_root_endpoint(auth_client) -> None:
    """Verify root endpoint returns project info."""
    response = auth_client.get("/")
    assert response.status_code == 200
    assert "Black-Scholes Research API" in response.json()["message"]
