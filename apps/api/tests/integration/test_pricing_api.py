"""Integration tests for the pricing router."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user
from src.methods.base import MethodType

# Mock user for authentication override
MOCK_USER = {"id": "test-user-id", "email": "test@example.com"}


def mock_get_current_user():
    return MOCK_USER


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_list_methods(client: TestClient):
    """Test listing supported methods."""
    response = client.get("/api/v1/pricing/methods")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(MethodType)
    assert "analytical" in data


@pytest.mark.integration
def test_calculate_analytical(client: TestClient, sample_option_params):
    """Test pricing calculation via API using analytical method."""
    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "analytical", "persist": False},
        json=sample_option_params,
    )
    assert response.status_code == 200
    data = response.json()
    assert "computed_price" in data
    assert data["method_type"] == "analytical"
    # S=100, K=100, T=1, vol=0.2, r=0.05 => ~10.45
    assert abs(data["computed_price"] - 10.4506) < 1e-4


@pytest.mark.integration
def test_calculate_crank_nicolson(client: TestClient, sample_option_params):
    """Test pricing calculation via API using Crank-Nicolson method."""
    # Use slightly different volatility to avoid cache
    params = sample_option_params.copy()
    params["volatility"] = 0.25
    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "crank_nicolson", "persist": False},
        json=params,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["method_type"] == "crank_nicolson"


@pytest.mark.integration
def test_calculate_error_handling(client: TestClient, sample_option_params, monkeypatch):
    """Test error handling in calculate_price."""
    from src.methods.analytical import BlackScholesAnalytical

    # Use unique params to bypass cache
    err_params = sample_option_params.copy()
    err_params["underlying_price"] = 999.0

    def mock_price_fail(*args, **kwargs):
        raise ValueError("Calculation error")

    monkeypatch.setattr(BlackScholesAnalytical, "price", mock_price_fail)

    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "analytical", "persist": False},
        json=err_params,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Calculation error"

    # Critical failure
    crit_params = sample_option_params.copy()
    crit_params["underlying_price"] = 888.0

    def mock_price_critical(*args, **kwargs):
        raise RuntimeError("Critical failure")

    monkeypatch.setattr(BlackScholesAnalytical, "price", mock_price_critical)
    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "analytical", "persist": False},
        json=crit_params,
    )
    assert response.status_code == 500


@pytest.mark.integration
def test_compare_methods(client: TestClient, sample_option_params):
    """Test comparing multiple methods."""
    # Use unique params
    comp_params = sample_option_params.copy()
    comp_params["volatility"] = 0.3
    payload = {"params": comp_params, "methods": ["analytical", "crank_nicolson"]}
    response = client.post("/api/v1/pricing/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "analytical_reference" in data
    assert len(data["results"]) == 2


@pytest.mark.integration
def test_compare_methods_errors(client: TestClient, sample_option_params):
    """Test error cases for comparison."""
    # Missing params
    response = client.post("/api/v1/pricing/compare", json={"methods": ["analytical"]})
    assert response.status_code == 400

    # Failing method in loop
    payload = {"params": sample_option_params, "methods": ["analytical", "invalid_type"]}
    response = client.post("/api/v1/pricing/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    # "invalid_type" should be caught in the loop and skipped
    assert len(data["results"]) == 1


@pytest.mark.integration
def test_invalid_method(client: TestClient, sample_option_params):
    """Test error handling for invalid method type."""
    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "invalid_method"},
        json=sample_option_params,
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_persistence(client: TestClient, sample_option_params):
    """Test that result is persisted to Supabase when persist=True."""
    # Use unique params
    pers_params = sample_option_params.copy()
    pers_params["underlying_price"] = 777.0
    response = client.post(
        "/api/v1/pricing/calculate",
        params={"method_type": "analytical", "persist": True},
        json=pers_params,
    )
    assert response.status_code == 200
