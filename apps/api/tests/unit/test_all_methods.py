import pytest
from src.methods.base import OptionParams
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference import FiniteDifferenceMethods
from src.methods.monte_carlo import MonteCarloMethods
from src.methods.trees import TreeMethods

@pytest.fixture
def atm_call_params():
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False
    )

def test_analytical_price(atm_call_params):
    res = BlackScholesAnalytical().price(atm_call_params)
    assert abs(res.computed_price - 10.4506) < 0.001

def test_explicit_fdm_price(atm_call_params):
    res = FiniteDifferenceMethods().explicit_fdm(atm_call_params, num_s=100, num_t=2000)
    assert abs(res.computed_price - 10.4506) < 0.05

def test_implicit_fdm_price(atm_call_params):
    res = FiniteDifferenceMethods().implicit_fdm(atm_call_params, num_s=100, num_t=100)
    assert abs(res.computed_price - 10.4506) < 0.05

def test_crank_nicolson_price(atm_call_params):
    res = FiniteDifferenceMethods().crank_nicolson(atm_call_params, num_s=100, num_t=100)
    assert abs(res.computed_price - 10.4506) < 0.01

def test_standard_mc_price(atm_call_params):
    res = MonteCarloMethods().standard_mc(atm_call_params, num_paths=200000)
    # MC has high variance, so check if analytical is within CI
    assert res.confidence_interval[0] <= 10.4506 <= res.confidence_interval[1]

def test_antithetic_mc_price(atm_call_params):
    res = MonteCarloMethods().antithetic_mc(atm_call_params, num_paths=100000)
    assert res.confidence_interval[0] <= 10.4506 <= res.confidence_interval[1]

def test_control_variate_mc_price(atm_call_params):
    res = MonteCarloMethods().control_variate_mc(atm_call_params, num_paths=100000)
    assert abs(res.computed_price - 10.4506) < 0.01

def test_quasi_mc_price(atm_call_params):
    res = MonteCarloMethods().quasi_mc(atm_call_params, num_paths=65536)
    assert abs(res.computed_price - 10.4506) < 0.01

def test_binomial_crr_price(atm_call_params):
    res = TreeMethods().binomial_crr(atm_call_params, n=1000)
    assert abs(res.computed_price - 10.4506) < 0.01

def test_trinomial_price(atm_call_params):
    res = TreeMethods().trinomial(atm_call_params, n=500)
    assert abs(res.computed_price - 10.4506) < 0.005

def test_binomial_richardson_price(atm_call_params):
    res = TreeMethods().binomial_crr_richardson(atm_call_params, n=500)
    assert abs(res.computed_price - 10.4506) < 0.001

def test_trinomial_richardson_price(atm_call_params):
    res = TreeMethods().trinomial_richardson(atm_call_params, n=250)
    assert abs(res.computed_price - 10.4506) < 0.001
    
def test_cross_method_agreement(atm_call_params):
    """Assert all methods achieve MAPE < 0.1% at standard resolution."""
    target = 10.4506
    methods = [
        BlackScholesAnalytical().price(atm_call_params),
        FiniteDifferenceMethods().crank_nicolson(atm_call_params, num_s=200, num_t=200),
        MonteCarloMethods().control_variate_mc(atm_call_params, num_paths=100000),
        TreeMethods().binomial_crr_richardson(atm_call_params, n=1000),
        TreeMethods().trinomial_richardson(atm_call_params, n=500)
    ]
    
    for res in methods:
        mape = abs(res.computed_price - target) / target
        assert mape < 0.001, f"Method {res.method_type} failed with MAPE {mape}"
