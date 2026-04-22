import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import app
from src.methods.base import PriceResult

client = TestClient(app)

@pytest.mark.unit
class TestRouters:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "Black-Scholes Research API v4" in response.json()["message"]

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_rabbitmq_connection")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    def test_health_check(self, mock_get_supabase, mock_get_minio, mock_get_rmq, mock_get_redis):
        # Mocking health checks
        mock_get_redis.return_value.ping = AsyncMock(return_value=True)
        mock_get_rmq.return_value = AsyncMock(is_closed=False)
        mock_get_minio.return_value.list_buckets.return_value = []
        
        # Mock Supabase chain
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.pricing.analytical_engine")
    def test_pricing_endpoint(self, mock_analytical_engine, mock_get_supabase):
        # Mock Auth
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        mock_user = MagicMock()
        mock_user.id = "test-user"
        mock_user.email = "test@example.com"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        
        # Mock Profile Role
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"role": "researcher"}])
        
        # Mock Results
        analytical_res = PriceResult(computed_price=10.5, method_type="analytical", exec_seconds=0.001)
        mock_analytical_engine.price.return_value = analytical_res
        
        explicit_res = PriceResult(computed_price=10.45, method_type="explicit_fdm", exec_seconds=0.005)
        
        # Patch METHOD_MAP to return a lambda that returns the PriceResult
        from src.routers.pricing import METHOD_MAP
        original_pricer = METHOD_MAP.get("explicit_fdm")
        METHOD_MAP["explicit_fdm"] = lambda params: explicit_res
        
        try:
            payload = {
                "params": {
                    "underlying_price": 100.0,
                    "strike_price": 100.0,
                    "maturity_years": 1.0,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                    "is_american": False
                },
                "methods": ["explicit_fdm"]
            }
            
            response = client.post(
                "/api/v1/price", 
                json=payload,
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["results"][0]["computed_price"] == 10.45
            assert data["analytical_reference"] == 10.5
        finally:
            if original_pricer:
                METHOD_MAP["explicit_fdm"] = original_pricer

    def test_methods_list(self):
        response = client.get("/api/v1/methods")
        assert response.status_code == 200
        assert len(response.json()) > 10

    def test_docs_reachability(self):
        assert client.get("/api/docs").status_code == 200
        assert client.get("/api/openapi.json").status_code == 200
