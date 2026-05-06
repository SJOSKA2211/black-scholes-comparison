"""Unit tests for the Analytical (Black-Scholes-Merton) pricing method."""

import pytest

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams


@pytest.mark.unit
def test_analytical_call_atm() -> None:
    """Test ATM Call option pricing."""
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False,
    )
    method = BlackScholesAnalytical()
    result = method.price(params)

    # BSM price for S=100, K=100, T=1, vol=0.2, r=0.05 is ~10.45058
    assert pytest.approx(result.computed_price, abs=1e-4) == 10.4506
    assert pytest.approx(result.delta, abs=1e-3) == 0.637
    assert pytest.approx(result.gamma, abs=1e-4) == 0.0187
    assert pytest.approx(result.vega, abs=1e-2) == 37.52


@pytest.mark.unit
def test_analytical_put_atm() -> None:
    """Test ATM Put option pricing."""
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="put",
        is_american=False,
    )
    method = BlackScholesAnalytical()
    result = method.price(params)

    # BSM price for S=100, K=100, T=1, vol=0.2, r=0.05 is ~5.57352
    assert pytest.approx(result.computed_price, abs=1e-4) == 5.5735
    assert pytest.approx(result.delta, abs=1e-3) == -0.363


@pytest.mark.unit
def test_analytical_itm_otm() -> None:
    """Test ITM and OTM options."""
    method = BlackScholesAnalytical()

    # ITM Call
    itm_params = OptionParams(
        underlying_price=120.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False,
    )
    itm_res = method.price(itm_params)
    assert itm_res.computed_price > 20.0

    # OTM Call
    otm_params = OptionParams(
        underlying_price=80.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False,
    )
    otm_res = method.price(otm_params)
    assert otm_res.computed_price < 5.0
