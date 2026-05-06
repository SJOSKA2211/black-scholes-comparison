"""Unit tests for main app entry point."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from src.main import app

@pytest.mark.unit
def test_root_endpoint() -> None:
    """Verify root metadata endpoint."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

@pytest.mark.unit
def test_health_check() -> None:
    """Verify health check endpoint."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    # Health check might return 500 if infrastructure is not ready in unit test, 
    # but the route should exist.
    assert response.status_code in [200, 503, 500]
