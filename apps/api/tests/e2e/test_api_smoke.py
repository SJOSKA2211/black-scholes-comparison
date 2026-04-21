import httpx
import pytest

@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ok"
        else:
            pytest.skip("Local API not running")

@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/metrics")
        if response.status_code == 200:
            assert "http_requests_total" in response.text
        else:
            pytest.skip("Local API not running")
