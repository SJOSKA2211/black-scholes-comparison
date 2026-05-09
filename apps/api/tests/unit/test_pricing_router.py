"""Unit tests for the pricing router."""
from __future__ import annotations
from typing import Any
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.auth.dependencies import get_current_user
from unittest.mock import MagicMock, patch, AsyncMock

client = TestClient(app)

# Mock user and Redis for dependency injection
def mock_get_current_user() -> dict[str, Any]:
    return {"id": "test-user", "email": "test@example.com"}

@pytest.fixture(autouse=True)
def mock_redis() -> Any:
    """Mock Redis client globally for these tests."""
    with patch("src.cache.decorators.get_redis") as mock_get:
        mock_redis_inst = MagicMock()
        mock_redis_inst.get = AsyncMock(return_value=None)
        mock_redis_inst.setex = AsyncMock()
        mock_get.return_value = mock_redis_inst
        yield mock_redis_inst

@pytest.mark.unit
def test_compute_price_analytical() -> None:
    """Verify analytical pricing via API."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    payload = {
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    response = client.post("/api/v1/pricing/compute?method=analytical", json=payload)
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert "price" in data
    assert pytest.approx(data["price"], 0.01) == 10.45

@pytest.mark.unit
def test_compute_price_unsupported_method() -> None:
    """Verify error for unsupported pricing method."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    payload = {
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    response = client.post("/api/v1/pricing/compute?method=invalid", json=payload)
    app.dependency_overrides.clear()
    
    assert response.status_code == 400
    assert "Unsupported method" in response.json()["detail"]

@pytest.mark.unit
def test_compute_price_all_methods() -> None:
    """Verify all supported methods via API."""
    app.dependency_overrides[get_current_user] = mock_get_current_user
    methods = ["crank_nicolson", "quasi_mc", "binomial_crr_richardson"]
    payload = {
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call"
    }
    
    for method in methods:
        response = client.post(f"/api/v1/pricing/compute?method={method}", json=payload)
        assert response.status_code == 200
        assert "price" in response.json()
    
    app.dependency_overrides.clear()
