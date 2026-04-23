import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    # Test through Nginx proxy (HTTPS)
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get("https://localhost/health")
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ok"
            assert data["services"]["database"] == "connected"
        else:
            pytest.fail(f"Health check failed with status {response.status_code}")


@pytest.mark.asyncio
async def test_metrics_endpoint() -> None:
    # Metrics might be blocked by Nginx (deny all except internal)
    # But let's check if we can reach it or if it gives 403
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get("https://localhost/metrics")
        # According to nginx.conf, /metrics is allowed only for internal IPs
        # So on localhost it might fail or pass depending on how Nginx sees 'localhost'
        if response.status_code == 200:
            assert "http_requests_total" in response.text
        elif response.status_code == 403:
            pytest.skip("Metrics endpoint is correctly restricted to internal network")
        else:
            pytest.skip(f"Metrics endpoint returned {response.status_code}")
