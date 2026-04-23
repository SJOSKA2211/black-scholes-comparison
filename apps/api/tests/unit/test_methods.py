from typing import Any, Callable

import numpy as np
import pytest

from src.exceptions import CFLViolationError
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams, PriceResult
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
        is_american=False,
    )


ALL_METHODS: list[Callable[[OptionParams], PriceResult]] = [
    BlackScholesAnalytical().price,
    ExplicitFDM().price,
    ImplicitFDM().price,
    CrankNicolsonFDM().price,
    StandardMC().price,
    AntitheticMC().price,
    ControlVariateMC().price,
    QuasiMC().price,
    BinomialCRR().price,
    TrinomialTree().price,
    BinomialCRRRichardson().price,
    TrinomialRichardson().price,
]

AMERICAN_SUPPORTED: list[Callable[[OptionParams], PriceResult]] = [
    BinomialCRR().price,
    TrinomialTree().price,
    BinomialCRRRichardson().price,
    TrinomialRichardson().price,
]


@pytest.mark.unit
def test_all_methods_call(standard_params: OptionParams) -> None:
    for method in ALL_METHODS:
        res = method(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
def test_all_methods_put(standard_params: OptionParams) -> None:
    standard_params.option_type = "put"
    for method in ALL_METHODS:
        res = method(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
def test_american_call(standard_params: OptionParams) -> None:
    standard_params.is_american = True
    for method in AMERICAN_SUPPORTED:
        res = method(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
def test_american_put(standard_params: OptionParams) -> None:
    standard_params.is_american = True
    standard_params.option_type = "put"
    for method in AMERICAN_SUPPORTED:
        res = method(standard_params)
        assert res.computed_price > 0


@pytest.mark.unit
def test_analytical_extras(standard_params: OptionParams) -> None:
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
def test_implied_volatility_logic(standard_params: OptionParams) -> None:
    bs = BlackScholesAnalytical()
    price_call = bs.price(standard_params).computed_price
    iv = bs.implied_volatility(price_call, standard_params)
    assert abs(iv - 0.2) < 1e-4

    iv_err = bs.implied_volatility(-10.0, standard_params)
    assert iv_err == 0.0


@pytest.mark.unit
def test_explicit_fdm_cfl_violation(standard_params: OptionParams) -> None:
    # Trigger CFL violation
    with pytest.raises(CFLViolationError):
        # We need to pass kwargs directly to the instance since we are using the .price method from list
        # But here we create a fresh instance
        ExplicitFDM().price(standard_params, num_spatial=200, num_time=10)
