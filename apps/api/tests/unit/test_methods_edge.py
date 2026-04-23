import numpy as np
import pytest

from src.exceptions import CFLViolationError
from src.methods.base import OptionParams
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.monte_carlo.standard import StandardMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree


@pytest.fixture
def base_params():
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False,
    )


@pytest.mark.unit
class TestMethodsEdgeCases:
    def test_explicit_fdm_cfl_violation(self, base_params):
        # High volatility or large spatial steps vs small time steps causes CFL violation
        with pytest.raises(CFLViolationError):
            ExplicitFDM(num_price_steps=100, num_time_steps=10).price(base_params)

    def test_standard_mc_put(self, base_params):
        base_params.option_type = "put"
        res = StandardMC(num_simulations=1000).price(base_params)
        assert res.computed_price > 0

    def test_antithetic_mc_put(self, base_params):
        base_params.option_type = "put"
        res = AntitheticMC(num_simulations=1000).price(base_params)
        assert res.computed_price > 0

    def test_quasi_mc_put(self, base_params):
        base_params.option_type = "put"
        res = QuasiMC(num_simulations=1024).price(base_params)
        assert res.computed_price > 0

    def test_control_variate_put(self, base_params):
        base_params.option_type = "put"
        res = ControlVariateMC(num_simulations=1000).price(base_params)
        assert res.computed_price > 0

    def test_binomial_put(self, base_params):
        base_params.option_type = "put"
        res = BinomialCRR(num_steps=50).price(base_params)
        assert res.computed_price > 0

    def test_trinomial_put(self, base_params):
        base_params.option_type = "put"
        res = TrinomialTree(num_steps=50).price(base_params)
        assert res.computed_price > 0
