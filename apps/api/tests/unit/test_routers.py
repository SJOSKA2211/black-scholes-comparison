from typing import Any
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
from src.main import app
from src.methods.base import PriceResult

client = TestClient(app)

@pytest.mark.unit
class TestRouters:
    def test_root_endpoint(self) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "Black-Scholes Research API v4" in response.json()["message"]

    @patch("src.routers.health.get_redis")
    @patch("src.routers.health.get_rabbitmq_connection")
    @patch("src.routers.health.get_minio")
    @patch("src.routers.health.get_supabase_client")
    def test_health_check(self, mock_get_supabase: Any, mock_get_minio: Any, mock_get_rmq: Any, mock_get_redis: Any) -> None:
        mock_get_redis.return_value.ping = AsyncMock(return_value=True)
        mock_get_rmq.return_value = AsyncMock(is_closed=False)
        mock_get_minio.return_value.list_buckets.return_value = []
        
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.pricing.get_method_instance")
    def test_pricing_endpoint(self, mock_factory: Any, mock_get_supabase: Any) -> None:
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        
        mock_user = MagicMock()
        mock_user.id = "test-user"
        mock_user.email = "test@example.com"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"role": "researcher"}])
        
        explicit_res = PriceResult(computed_price=10.45, method_type="explicit_fdm", exec_seconds=0.005)
        mock_factory.return_value = MagicMock(price=MagicMock(return_value=explicit_res))
        
        payload = {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
            "is_american": False
        }
        
        # Test calculate endpoint
        response = client.post(
            "/api/v1/pricing/calculate?method_type=explicit_fdm", 
            json=payload,
            headers={"Authorization": "Bearer test-token"}
        )
        assert response.status_code == 200
        assert response.json()["computed_price"] == 10.45

    def test_methods_list(self) -> None:
        response = client.get("/api/v1/pricing/methods")
        assert response.status_code == 200
        assert len(response.json()) >= 12

    def test_docs_reachability(self) -> None:
        assert client.get("/api/docs").status_code == 200
        assert client.get("/api/openapi.json").status_code == 200
