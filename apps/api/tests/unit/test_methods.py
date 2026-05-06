"""Unit tests for all numerical pricing methods."""

import pytest
import numpy as np

from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson
from src.methods.base import OptionParams


@pytest.fixture
def atm_call_params() -> OptionParams:
    """Standard ATM Call: S=100, K=100, T=1, vol=0.2, r=0.05."""
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False,
    )


@pytest.fixture
def atm_put_params() -> OptionParams:
    """Standard ATM Put: S=100, K=100, T=1, vol=0.2, r=0.05."""
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="put",
        is_american=False,
    )


@pytest.mark.unit
class TestAnalytical:
    """Tests for Black-Scholes analytical method."""

    def test_analytical_call(self, atm_call_params: OptionParams) -> None:
        method = BlackScholesAnalytical()
        result = method.price(atm_call_params)
        # BSM Reference: 10.4506
        assert pytest.approx(result.computed_price, abs=1e-4) == 10.4506
        assert result.delta > 0
        assert result.gamma > 0
        assert result.vega > 0

    def test_analytical_put(self, atm_put_params: OptionParams) -> None:
        method = BlackScholesAnalytical()
        result = method.price(atm_put_params)
        # BSM Reference: 5.5735
        assert pytest.approx(result.computed_price, abs=1e-4) == 5.5735
        assert result.delta < 0


@pytest.mark.unit
class TestCrankNicolson:
    """Tests for Crank-Nicolson FDM."""

    def test_cn_european_call(self, atm_call_params: OptionParams) -> None:
        method = CrankNicolson(num_time_steps=200, num_price_steps=400)
        result = method.price(atm_call_params)
        assert pytest.approx(result.computed_price, abs=0.01) == 10.4506

    def test_cn_european_put(self, atm_put_params: OptionParams) -> None:
        method = CrankNicolson(num_time_steps=200, num_price_steps=400)
        result = method.price(atm_put_params)
        assert pytest.approx(result.computed_price, abs=0.01) == 5.5735

    def test_cn_american_put(self) -> None:
        """American puts should be more expensive than European puts."""
        params = OptionParams(
            underlying_price=100.0,
            strike_price=100.0,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="put",
            is_american=True,
        )
        method = CrankNicolson(num_time_steps=100, num_price_steps=200)
        result = method.price(params)
        # European put is ~5.57. American should be > 5.57.
        assert result.computed_price > 5.58


@pytest.mark.unit
class TestQuasiMC:
    """Tests for Quasi-Monte Carlo."""

    def test_qmc_european_call(self, atm_call_params: OptionParams) -> None:
        method = QuasiMC()
        result = method.price(atm_call_params)
        # QMC should be very close to analytical
        assert pytest.approx(result.computed_price, abs=0.02) == 10.4506


@pytest.mark.unit
class TestCRRRichardson:
    """Tests for Binomial CRR with Richardson Extrapolation."""

    def test_crr_richardson_call(self, atm_call_params: OptionParams) -> None:
        method = BinomialCRRRichardson()
        result = method.price(atm_call_params)
        assert pytest.approx(result.computed_price, abs=0.01) == 10.4506


@pytest.mark.unit
def test_cross_method_agreement(atm_call_params: OptionParams) -> None:
    """Verify all methods agree within 0.1% MAPE for standard ATM call."""
    analytical = BlackScholesAnalytical().price(atm_call_params).computed_price
    cn = CrankNicolson().price(atm_call_params).computed_price
    qmc = QuasiMC().price(atm_call_params).computed_price
    crr = BinomialCRRRichardson().price(atm_call_params).computed_price

    results = [cn, qmc, crr]
    for res in results:
        mape = abs(res - analytical) / analytical
        assert mape < 0.001  # 0.1%
