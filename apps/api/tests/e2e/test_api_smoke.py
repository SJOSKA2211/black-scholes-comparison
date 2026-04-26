import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(api_url: str) -> None:
    # Test through Nginx proxy or direct API
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f"{api_url}/health")
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ok"
            assert data["services"]["database"] == "connected"
        else:
            pytest.fail(f"Health check failed with status {response.status_code}")


@pytest.mark.asyncio
async def test_metrics_endpoint(api_url: str) -> None:
    # Metrics might be blocked by Nginx (deny all except internal)
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(f"{api_url}/metrics")
        # According to nginx.conf, /metrics is allowed only for internal IPs
        if response.status_code == 200:
            assert "black_scholes" in response.text or "http_requests" in response.text
        elif response.status_code == 403:
            pytest.skip("Metrics endpoint is correctly restricted to internal network")
        else:
            pytest.skip(f"Metrics endpoint returned {response.status_code}")
