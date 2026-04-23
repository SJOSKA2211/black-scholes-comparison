from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.main import app


async def mock_get_current_user():
    return {"id": "u1"}

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

params = {
    "underlying_price": 100,
    "strike_price": 100,
    "maturity_years": 1,
    "volatility": 0.2,
    "risk_free_rate": 0.05,
    "option_type": "call",
}

print("Testing POST /api/v1/pricing/calculate")
res = client.post("/api/v1/pricing/calculate?method_type=standard_mc", json=params)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")

print("\nTesting POST /api/v1/pricing/compare")
res = client.post("/api/v1/pricing/compare?methods=standard_mc", json=params)
print(f"Status: {res.status_code}")
print(f"Body: {res.text}")
