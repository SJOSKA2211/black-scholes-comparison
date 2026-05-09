"""Integration tests for pricing API."""

import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.methods.base import OptionParameters
from src.main import app


# Mock authentication
async def mock_get_current_user():
    return {"id": "test-user", "email": "test@example.com"}


@pytest.fixture(autouse=True)
def auth_override():
    """Override auth dependency for integration tests."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compute_price_endpoint(async_client, sample_option_params: dict) -> None:
    """Test the POST /api/v1/pricing/compute endpoint."""
    response = await async_client.post(
        "/api/v1/pricing/compute", json=sample_option_params, params={"method": "analytical"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert data["method"] == "analytical"
    assert abs(data["price"] - 10.4506) < 1e-4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compute_price_crr(async_client, sample_option_params: dict) -> None:
    """Test the compute endpoint with CRR Richardson."""
    response = await async_client.post(
        "/api/v1/pricing/compute",
        json=sample_option_params,
        params={"method": "binomial_crr_richardson"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["method"] == "binomial_crr_richardson"
    assert abs(data["price"] - 10.4506) < 0.01
