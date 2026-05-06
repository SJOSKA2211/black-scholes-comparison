import numpy as np
import pytest
from pydantic import ValidationError

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import NumericalMethod, OptionParams, PriceResult
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson


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
        with pytest.raises(ValidationError):
            OptionParams(
                underlying_price=-1,
                strike_price=100,
                maturity_years=1,
                volatility=0.2,
                risk_free_rate=0.05,
                option_type="call",
            )

    def test_invalid_volatility(self):
        with pytest.raises(ValidationError):
            OptionParams(
                underlying_price=100,
                strike_price=100,
                maturity_years=1,
                volatility=-0.1,
                risk_free_rate=0.05,
                option_type="call",
            )

    def test_invalid_type(self):
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="invalid",
        )
        assert params.option_type == "invalid"
        assert params.is_call is False

    def test_methods_base_protocol(self):
        class Dummy(NumericalMethod):
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
        # Just ensure they run without error
        bs.delta(standard_params)
        bs.gamma(standard_params)
        bs.vega(standard_params)
        bs.rho(standard_params)
        standard_params.option_type = "put"
        bs.theta(standard_params)

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
    @pytest.mark.parametrize("method_class", [CrankNicolson])
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_fdm_basic(self, method_class, option_type, standard_params):
        standard_params.option_type = option_type
        res = method_class().price(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
class TestMonteCarlo:
    @pytest.mark.parametrize("method_class", [QuasiMC])
    @pytest.mark.parametrize("option_type", ["call", "put"])
    def test_mc_basic(self, method_class, option_type, standard_params):
        standard_params.option_type = option_type
        res = method_class().price(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
class TestTrees:
    def test_binomial_crr_european(self, standard_params):
        res = BinomialCRR().price_tree(standard_params, num_steps=100)
        assert abs(res - 10.4506) < 0.1

    def test_binomial_crr_american_put(self, standard_params):
        standard_params.option_type = "put"
        standard_params.is_american = True
        res = BinomialCRR().price_tree(standard_params, num_steps=100)
        assert res > 5.5735

    def test_richardson_wrappers(self, standard_params):
        res_b = BinomialCRRRichardson().price(standard_params)
        assert res_b.method_type == "binomial_crr_richardson"


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
    import numpy as np
    np.random.seed(42)
    ref = BlackScholesAnalytical().price(standard_params).computed_price
    methods = [
        QuasiMC().price,
        BinomialCRRRichardson().price,
    ]
    for m in methods:
        res = m(standard_params)
        mape = abs(res.computed_price - ref) / ref
        print(f"Method: {res.method_type}, MAPE: {mape}")
        assert mape < 0.05
