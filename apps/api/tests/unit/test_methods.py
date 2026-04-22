import pytest
import numpy as np
from src.methods.base import OptionParams
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference.explicit import price_explicit_fdm
from src.methods.finite_difference.implicit import price_implicit_fdm
from src.methods.finite_difference.crank_nicolson import price_crank_nicolson
from src.methods.monte_carlo.standard import price_standard_mc
from src.methods.monte_carlo.antithetic import price_antithetic_mc
from src.methods.monte_carlo.control_variates import price_control_variate_mc
from src.methods.monte_carlo.quasi_mc import price_quasi_mc
from src.methods.tree_methods.binomial_crr import price_binomial_crr
from src.methods.tree_methods.trinomial import price_trinomial
from src.methods.tree_methods.richardson import price_binomial_crr_richardson, price_trinomial_richardson
from src.exceptions import CFLViolationError

@pytest.fixture
def standard_params():
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False
    )

ALL_METHODS = [
    BlackScholesAnalytical().price,
    price_explicit_fdm,
    price_implicit_fdm,
    price_crank_nicolson,
    price_standard_mc,
    price_antithetic_mc,
    price_control_variate_mc,
    price_quasi_mc,
    price_binomial_crr,
    price_trinomial,
    price_binomial_crr_richardson,
    price_trinomial_richardson
]

AMERICAN_SUPPORTED = [
    price_binomial_crr,
    price_trinomial,
    price_binomial_crr_richardson,
    price_trinomial_richardson
]

@pytest.mark.unit
def test_all_methods_call(standard_params):
    for method in ALL_METHODS:
        res = method(standard_params)
        assert res.computed_price > 0

@pytest.mark.unit
def test_all_methods_put(standard_params):
    standard_params.option_type = "put"
    for method in ALL_METHODS:
        res = method(standard_params)
        assert res.computed_price > 0

@pytest.mark.unit
def test_american_call(standard_params):
    standard_params.is_american = True
    for method in AMERICAN_SUPPORTED:
        res = method(standard_params)
        assert res.computed_price > 0

@pytest.mark.unit
def test_american_put(standard_params):
    standard_params.is_american = True
    standard_params.option_type = "put"
    for method in AMERICAN_SUPPORTED:
        res = method(standard_params)
        assert res.computed_price > 0

@pytest.mark.unit
def test_analytical_extras(standard_params):
    bs = BlackScholesAnalytical()
    assert bs.delta(standard_params) > 0
    assert bs.gamma(standard_params) > 0
    assert bs.vega(standard_params) > 0
    
    standard_params.option_type = "put"
    assert bs.delta(standard_params) < 0
    
    res_asian = bs.geometric_asian_price(standard_params)
    assert res_asian.computed_price > 0
    
    standard_params.option_type = "call"
    res_asian_call = bs.geometric_asian_price(standard_params)
    assert res_asian_call.computed_price > 0

@pytest.mark.unit
def test_implied_volatility_logic(standard_params):
    bs = BlackScholesAnalytical()
    price_call = bs.price(standard_params).computed_price
    iv = bs.implied_volatility(price_call, standard_params)
    assert abs(iv - 0.2) < 1e-4
    
    iv_err = bs.implied_volatility(-10.0, standard_params)
    assert iv_err == 0.0

@pytest.mark.unit
def test_explicit_fdm_cfl_violation(standard_params):
    # Trigger CFL violation
    with pytest.raises(CFLViolationError):
        price_explicit_fdm(standard_params, num_spatial=200, num_time=10)
