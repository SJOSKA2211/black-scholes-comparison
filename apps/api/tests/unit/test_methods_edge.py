import pytest
import numpy as np
from src.methods.base import OptionParams
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.monte_carlo.standard import StandardMC
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree
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
            ExplicitFDM().price(base_params, num_spatial=100, num_time=10)

    def test_standard_mc_put(self, base_params):
        base_params.option_type = "put"
        res = StandardMC().price(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_antithetic_mc_put(self, base_params):
        base_params.option_type = "put"
        res = AntitheticMC().price(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_quasi_mc_put(self, base_params):
        base_params.option_type = "put"
        res = QuasiMC().price(base_params, num_paths=1024)
        assert res.computed_price > 0

    def test_control_variate_put(self, base_params):
        base_params.option_type = "put"
        res = ControlVariateMC().price(base_params, num_paths=1000)
        assert res.computed_price > 0

    def test_binomial_put(self, base_params):
        base_params.option_type = "put"
        res = BinomialCRR().price(base_params, num_steps=50)
        assert res.computed_price > 0

    def test_trinomial_put(self, base_params):
        base_params.option_type = "put"
        res = TrinomialTree().price(base_params, num_steps=50)
        assert res.computed_price > 0
