"""Unit tests for additional pricing router coverage."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.methods.base import PriceResult

client = TestClient(app)


@pytest.mark.unit
class TestPricingRouterCoverage:
    def test_get_method_instance_all_branches(self) -> None:
        """Test that all supported methods can be instantiated through the factory."""
        from src.routers.pricing import get_method_instance

        methods = [
            "analytical",
            "explicit_fdm",
            "implicit_fdm",
            "crank_nicolson",
            "standard_mc",
            "antithetic_mc",
            "control_variate_mc",
            "quasi_mc",
            "binomial_crr",
            "binomial_crr_richardson",
            "trinomial",
            "trinomial_richardson",
        ]

        for m_type in methods:
            instance = get_method_instance(m_type)
            assert instance is not None

        with pytest.raises(Exception):  # HTTPException(400)
            get_method_instance("invalid_method")

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.pricing.upsert_option_parameters")
    @patch("src.routers.pricing.upsert_price_result")
    @patch("src.routers.pricing.get_method_instance")
    def test_calculate_price_persist(
        self, mock_factory, mock_upsert_res, mock_upsert_opt, mock_get_supabase
    ) -> None:
        """Test pricing calculation with persistence enabled."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        res = PriceResult(computed_price=10.45, method_type="analytical", exec_seconds=0.01)
        mock_factory.return_value = MagicMock(price=MagicMock(return_value=res))
        mock_upsert_opt.return_value = "opt-id"

        payload = {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }

        response = client.post(
            "/api/v1/pricing/calculate?method_type=analytical&persist=true",
            json=payload,
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        mock_upsert_opt.assert_called_once()
        mock_upsert_res.assert_called_once()

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.pricing.get_method_instance")
    def test_compare_methods_without_analytical(self, mock_factory, mock_get_supabase) -> None:
        """Test compare_methods ensures 'analytical' is included."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        res = PriceResult(computed_price=10.45, method_type="analytical", exec_seconds=0.01)
        mock_method = MagicMock(price=MagicMock(return_value=res))
        mock_factory.return_value = mock_method

        payload = {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }

        # Request only explicit_fdm
        response = client.post(
            "/api/v1/pricing/compare?methods=explicit_fdm",
            json=payload,
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 200
        # Since analytical was added, factory should have been called for it too
        assert mock_factory.call_count >= 2

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.pricing.get_method_instance")
    def test_compare_methods_exception(self, mock_factory, mock_get_supabase) -> None:
        """Test exception handling in compare_methods."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_factory.side_effect = Exception("Compare failed")

        payload = {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
        }

        response = client.post(
            "/api/v1/pricing/compare?methods=explicit_fdm",
            json=payload,
            headers={"Authorization": "Bearer token"},
        )
        assert response.status_code == 500
        assert "Pricing comparison failed" in response.json()["detail"]
