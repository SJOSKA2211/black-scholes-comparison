from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.exceptions import CFLViolationError
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import NumericalMethod, OptionParams, PriceResult
from src.methods.finite_difference.crank_nicolson import CrankNicolsonFDM
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.finite_difference.implicit import ImplicitFDM
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.monte_carlo.standard import StandardMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson, TrinomialRichardson
from src.methods.tree_methods.trinomial import TrinomialTree


@pytest.fixture
def standard_params() -> OptionParams:
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
    )


@pytest.mark.unit
class TestOptionParams:
    def test_valid_params(self, standard_params):
        assert standard_params.underlying_price == 100.0
        assert standard_params.option_type == "call"

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            OptionParams(
                underlying_price=-1,
                strike_price=100,
                maturity_years=1,
                volatility=0.2,
                risk_free_rate=0.05,
                option_type="call",
            )

    def test_invalid_volatility(self):
        with pytest.raises(ValueError):
            OptionParams(
                underlying_price=100,
                strike_price=100,
                maturity_years=1,
                volatility=-0.1,
                risk_free_rate=0.05,
                option_type="call",
            )

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            OptionParams(
                underlying_price=100,
                strike_price=100,
                maturity_years=1,
                volatility=0.2,
                risk_free_rate=0.05,
                option_type="invalid",
            )

    def test_methods_base_protocol(self):
        class Dummy:
            def price(self, params: OptionParams) -> PriceResult:
                return PriceResult(method_type="dummy", computed_price=0.0, exec_seconds=0.0)

        assert isinstance(Dummy(), NumericalMethod)


@pytest.mark.unit
class TestAnalytical:
    def test_price_call(self, standard_params):
        res = BlackScholesAnalytical().price(standard_params)
        assert abs(res.computed_price - 10.4506) < 1e-4

    def test_price_put(self, standard_params):
        standard_params.option_type = "put"
        res = BlackScholesAnalytical().price(standard_params)
        assert abs(res.computed_price - 5.5735) < 1e-4

    def test_greeks(self, standard_params):
        bs = BlackScholesAnalytical()
        assert bs.delta(standard_params) > 0
        assert bs.gamma(standard_params) > 0
        assert bs.vega(standard_params) > 0
        assert bs.rho(standard_params) > 0
        standard_params.option_type = "put"
        assert bs.theta(standard_params) < 0

    def test_implied_volatility(self, standard_params):
        bs = BlackScholesAnalytical()
        price = bs.price(standard_params).computed_price
        assert abs(bs.implied_volatility(price, standard_params) - 0.2) < 1e-4
        assert bs.implied_volatility(-1, standard_params) == 0.0

    def test_implied_volatility_failure(self, standard_params):
        bs = BlackScholesAnalytical()
        assert bs.implied_volatility(1000.0, standard_params) == 0.0

    def test_asian_option(self, standard_params):
        bs = BlackScholesAnalytical()
        res = bs.geometric_asian_price(standard_params)
        assert res.computed_price > 0
        standard_params.option_type = "put"
        res_put = bs.geometric_asian_price(standard_params)
        assert res_put.computed_price > 0


@pytest.mark.unit
class TestFDM:
    @pytest.mark.parametrize("method_class", [ExplicitFDM, ImplicitFDM, CrankNicolsonFDM])
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_fdm_basic(self, method_class, option_type, standard_params):
        standard_params.option_type = option_type
        res = method_class().price(standard_params)
        assert res.computed_price > 0
        assert res.delta is not None

    def test_fdm_boundary_conditions(self, standard_params):
        # Test low price boundary
        standard_params.underlying_price = 0.0001
        for method_class in [ExplicitFDM, ImplicitFDM, CrankNicolsonFDM]:
            res = method_class(num_time_steps=10, num_price_steps=10).price(standard_params)
            assert res is not None

        # Test high price boundary
        standard_params.underlying_price = 500.0
        for method_class in [ExplicitFDM, ImplicitFDM, CrankNicolsonFDM]:
            res = method_class(num_time_steps=10, num_price_steps=10).price(standard_params)
            assert res is not None

    def test_explicit_cfl_violation(self, standard_params):
        with pytest.raises(CFLViolationError):
            ExplicitFDM(num_price_steps=200, num_time_steps=10).price(standard_params)

    def test_explicit_cfl_bumping(self, standard_params):
        # Trigger vega=0 branch by bumping CFL
        standard_params.volatility = 0.31
        fdm = ExplicitFDM(num_price_steps=100, num_time_steps=2000)
        res = fdm.price(standard_params)
        assert res.vega == 0.0


@pytest.mark.unit
class TestMonteCarlo:
    @pytest.mark.parametrize("method_class", [StandardMC, AntitheticMC, ControlVariateMC, QuasiMC])
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_mc_basic(self, method_class, option_type, standard_params):
        standard_params.option_type = option_type
        res = method_class(num_simulations=1024).price(standard_params)
        assert res.computed_price > 0

    @pytest.mark.parametrize("method_class", [StandardMC, AntitheticMC, ControlVariateMC, QuasiMC])
    def test_small_maturity_theta(self, method_class, standard_params):
        standard_params.maturity_years = 0.0001
        res = method_class(num_simulations=10).price(standard_params)
        assert res.theta == 0.0


@pytest.mark.unit
class TestTrees:
    def test_binomial_crr_european(self, standard_params):
        res = BinomialCRR(num_steps=100).price(standard_params)
        assert abs(res.computed_price - 10.4506) < 0.1

    def test_binomial_crr_american_put(self, standard_params):
        standard_params.option_type = "put"
        standard_params.is_american = True
        res = BinomialCRR(num_steps=100).price(standard_params)
        assert res.computed_price > 5.5735

    def test_binomial_crr_richardson_logic(self, standard_params):
        method = BinomialCRR(num_steps=100, use_richardson=True)
        assert method.method_type == "binomial_crr_richardson"
        res = method.price(standard_params)
        assert res.computed_price > 0
        # Steps < 1 branch
        res_0, _, _ = method._tree_solve(standard_params, 0)
        assert res_0 == 0.0

    def test_trinomial_basic(self, standard_params):
        res = TrinomialTree(num_steps=100).price(standard_params)
        assert abs(res.computed_price - 10.4506) < 0.1
        # Steps branches
        assert TrinomialTree(num_steps=0).price(standard_params).computed_price == 0.0
        assert TrinomialTree(num_steps=1).price(standard_params).computed_price > 0

    def test_trinomial_put(self, standard_params):
        standard_params.option_type = "put"
        res = TrinomialTree(num_steps=100).price(standard_params)
        assert res.computed_price > 0

    def test_trinomial_american(self, standard_params):
        # American Call
        standard_params.is_american = True
        res_call = TrinomialTree(num_steps=100).price(standard_params)
        assert res_call.computed_price > 0
        # American Put
        standard_params.option_type = "put"
        res_put = TrinomialTree(num_steps=100).price(standard_params)
        assert res_put.computed_price > 0

    def test_richardson_wrappers(self, standard_params):
        res_b = BinomialCRRRichardson(num_steps=100).price(standard_params)
        assert res_b.method_type == "binomial_crr_richardson"
        res_t = TrinomialRichardson(num_steps=100).price(standard_params)
        assert res_t.method_type == "trinomial_richardson"

        # Zero steps
        assert BinomialCRRRichardson(num_steps=0).price(standard_params).computed_price == 0.0
        assert TrinomialRichardson(num_steps=0).price(standard_params).computed_price == 0.0

    def test_richardson_none_greeks(self, standard_params):
        mock_res = PriceResult(
            method_type="binomial_crr", computed_price=10.0, exec_seconds=0.1, delta=None
        )
        with patch("src.methods.tree_methods.richardson.BinomialCRR.price", return_value=mock_res):
            assert BinomialCRRRichardson(num_steps=10).price(standard_params).delta is None
        with patch(
            "src.methods.tree_methods.richardson.TrinomialTree.price", return_value=mock_res
        ):
            assert TrinomialRichardson(num_steps=10).price(standard_params).delta is None


@pytest.mark.unit
class TestAnalysis:
    def test_channels(self):
        from src.websocket.channels import ALLOWED_CHANNELS

        assert "experiments" in ALLOWED_CHANNELS
        assert "scrapers" in ALLOWED_CHANNELS

    def test_compute_mape(self):
        from src.analysis.statistics import compute_mape

        results = [{"computed_price": 110}]
        assert compute_mape(results, 100) == 10.0
        assert compute_mape([], 100) == 0.0
        assert compute_mape(results, 0) == 0.0

    def test_get_convergence_metrics(self):
        from src.analysis.statistics import get_convergence_metrics

        results = [{"computed_price": 100}, {"computed_price": 110}]
        metrics = get_convergence_metrics(results)
        assert metrics["count"] == 2
        assert metrics["mean_price"] == 105.0
        assert get_convergence_metrics([]) == {}


@pytest.mark.unit
def test_cross_method_agreement(standard_params):
    ref = BlackScholesAnalytical().price(standard_params).computed_price
    methods = [
        CrankNicolsonFDM(num_time_steps=2000, num_price_steps=200).price,
        ControlVariateMC(num_simulations=50000).price,
        BinomialCRRRichardson(num_steps=2000).price,
        TrinomialRichardson(num_steps=1000).price,
    ]
    for m in methods:
        res = m(standard_params)
        mape = abs(res.computed_price - ref) / ref
        assert mape < 0.001
