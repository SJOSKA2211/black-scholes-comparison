import pytest
import numpy as np
from src.methods.base import OptionParams
from src.methods.finite_difference.explicit import price_explicit_fdm
from src.methods.monte_carlo.standard import price_standard_mc
from src.methods.monte_carlo.antithetic import price_antithetic_mc
from src.methods.monte_carlo.control_variates import price_control_variate_mc
from src.methods.monte_carlo.quasi_mc import price_quasi_mc
from src.methods.tree_methods.binomial_crr import price_binomial_crr
from src.methods.tree_methods.trinomial import price_trinomial
from src.exceptions import CFLViolationError

@pytest.fixture
def base_params():
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False
    )

@pytest.mark.unit
class TestMethodsEdgeCases:
    def test_explicit_fdm_cfl_violation(self, base_params):
        # High volatility or large spatial steps vs small time steps causes CFL violation
        with pytest.raises(CFLViolationError):
            price_explicit_fdm(base_params, num_spatial=100, num_time=10)

    def test_standard_mc_put(self, base_params):
        base_params.option_type = "put"
        res = price_standard_mc(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_antithetic_mc_put(self, base_params):
        base_params.option_type = "put"
        res = price_antithetic_mc(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_quasi_mc_put(self, base_params):
        base_params.option_type = "put"
        res = price_quasi_mc(base_params, num_paths=1024)
        assert res.computed_price > 0

    def test_control_variate_put(self, base_params):
        base_params.option_type = "put"
        res = price_control_variate_mc(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_binomial_put(self, base_params):
        base_params.option_type = "put"
        res = price_binomial_crr(base_params, num_steps=50)
        assert res.computed_price > 0

    def test_trinomial_put(self, base_params):
        base_params.option_type = "put"
        res = price_trinomial(base_params, num_steps=50)
        assert res.computed_price > 0
