"""Integration tests for pricing API."""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user

# Mock authentication
async def mock_get_current_user():
    return {"id": "test-user", "email": "test@example.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

@pytest.mark.integration
def test_compute_price_endpoint(client: TestClient, sample_option_params: dict) -> None:
    """Test the POST /api/v1/pricing/compute endpoint."""
    response = client.post(
        "/api/v1/pricing/compute",
        json=sample_option_params,
        params={"method": "analytical"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert data["method"] == "analytical"
    assert abs(data["price"] - 10.4506) < 1e-4

@pytest.mark.integration
def test_compute_price_crr(client: TestClient, sample_option_params: dict) -> None:
    """Test the compute endpoint with CRR Richardson."""
    response = client.post(
        "/api/v1/pricing/compute",
        json=sample_option_params,
        params={"method": "binomial_crr_richardson"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "binomial_crr_richardson"
    assert abs(data["price"] - 10.4506) < 0.01
