"""Unit tests for additional numerical methods coverage."""

import pytest

from unittest.mock import MagicMock, patch
from src.methods.base import OptionParams
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson


@pytest.mark.unit
class TestMethodsCoverage:
    def test_binomial_crr_richardson_logic(self) -> None:
        """Test the Richardson extrapolation branch in BinomialCRR."""
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )

        # Test direct use_richardson=True
        method = BinomialCRR(num_steps=100, use_richardson=True)
        assert method.method_type == "binomial_crr_richardson"
        result = method.price(params)
        assert result.computed_price > 0

        # Test steps < 1 branch
        res_0, _, _ = method._tree_solve(params, 0)
        assert res_0 == 0.0

    def test_binomial_crr_richardson_wrapper(self) -> None:
        """Test the BinomialCRRRichardson wrapper class."""
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        method = BinomialCRRRichardson(num_steps=100)
        result = method.price(params)
        assert result.method_type == "binomial_crr_richardson"
        assert result.computed_price > 0

        # Test extrap_g with None
        val = method.price(params)  # Normal
        assert method.price(params).delta is not None

    def test_richardson_none_greek(self) -> None:
        """Test the None branch in extrap_g."""
        from src.methods.tree_methods.richardson import BinomialCRRRichardson

        method = BinomialCRRRichardson(num_steps=10)
        # We can't easily make BinomialCRR return None without patching its return type
        # But we can just call extrap_g directly if we want to be sure
        from src.methods.tree_methods.richardson import BinomialCRRRichardson as BCR

        instance = BCR()
        # Accessing internal function if possible, or just trust the previous 100% logic
        # Actually I'll just use extrap_g directly
        # But it's an internal function.
        # I'll just patch BinomialCRR.price to return None greeks
        with patch("src.methods.tree_methods.binomial_crr.BinomialCRR.price") as mock_price:
            from src.methods.base import PriceResult

            mock_price.return_value = PriceResult(
                method_type="binomial_crr",
                computed_price=10.0,
                exec_seconds=0.01,
                delta=None,
                gamma=None,
                theta=None,
                vega=None,
                rho=None,
            )
            params = OptionParams(underlying_price=100, strike_price=100, maturity_years=1.0, 
                                 volatility=0.2, risk_free_rate=0.05, option_type="call")
            res = instance.price(params)
            assert res.delta is None
