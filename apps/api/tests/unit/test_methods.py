"""Unit tests for Black-Scholes numerical methods."""

import numpy as np
import pytest

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParameters, OptionType
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson


@pytest.fixture
def atm_call_params():
    """Standard ATM European call: S=100, K=100, T=1, sigma=0.2, r=0.05."""
    return OptionParameters(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type=OptionType.CALL,
        is_american=False,
    )


@pytest.mark.unit
def test_analytical_price(atm_call_params):
    """Verify analytical price is 10.4506."""
    solver = BlackScholesAnalytical()
    result = solver.price(atm_call_params)
    assert pytest.approx(result.computed_price, abs=1e-4) == 10.45058


@pytest.mark.unit
def test_crank_nicolson_agreement(atm_call_params):
    """Verify Crank-Nicolson MAPE < 0.1% vs analytical."""
    analytical_solver = BlackScholesAnalytical()
    analytical_price = analytical_solver.price(atm_call_params).computed_price

    cn_solver = CrankNicolson(mesh_points_s=200, mesh_points_t=200)
    cn_price = cn_solver.price(atm_call_params).computed_price

    mape = abs(cn_price - analytical_price) / analytical_price
    assert mape < 0.001


@pytest.mark.unit
def test_quasi_mc_agreement(atm_call_params):
    """Verify Quasi-MC MAPE < 0.1% vs analytical."""
    analytical_solver = BlackScholesAnalytical()
    analytical_price = analytical_solver.price(atm_call_params).computed_price

    qmc_solver = QuasiMC(num_paths=131072)
    qmc_price = qmc_solver.price(atm_call_params).computed_price

    mape = abs(qmc_price - analytical_price) / analytical_price
    assert mape < 0.001


@pytest.mark.unit
def test_crr_richardson_agreement(atm_call_params):
    """Verify CRR+Richardson MAPE < 0.1% vs analytical."""
    analytical_solver = BlackScholesAnalytical()
    analytical_price = analytical_solver.price(atm_call_params).computed_price

    rich_solver = BinomialCRRRichardson(steps=500)
    rich_price = rich_solver.price(atm_call_params).computed_price

    mape = abs(rich_price - analytical_price) / analytical_price
    assert mape < 0.001


@pytest.mark.unit
def test_option_params_validation():
    """Test OptionParameters pydantic validation."""
    with pytest.raises(ValueError):
        OptionParameters(
            underlying_price=-10,  # invalid
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type=OptionType.CALL,
        )

    with pytest.raises(ValueError, match="Volatility too high"):
        OptionParameters(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=6.0,  # invalid (> 5.0)
            risk_free_rate=0.05,
            option_type=OptionType.CALL,
        )
