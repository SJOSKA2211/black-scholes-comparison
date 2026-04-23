import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.mark.e2e
def test_metrics_endpoint_reachability() -> None:
    """
    E2E test to verify that the /metrics endpoint is reachable and returns Prometheus data.
    """
    client = TestClient(app)
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "black_scholes_price_computations_total" in response.text
    assert "process_cpu_seconds_total" in response.text

@pytest.mark.e2e
def test_health_endpoint_integration() -> None:
    """
    Verifies that the health check reflects the status of infrastructure dependencies.
    """
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # These might be 'connected' or 'disconnected' depending on the environment
    assert "db" in data
    assert "redis" in data
    assert "rabbitmq" in data
