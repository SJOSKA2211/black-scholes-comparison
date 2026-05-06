"""Unit tests for all numerical pricing methods."""

import pytest
import numpy as np
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.base import OptionParams, OptionType


@pytest.mark.unit
class TestAnalytical:
    """Tests for Black-Scholes analytical method."""

    @pytest.mark.asyncio
    async def test_analytical_call(self, atm_call_params: OptionParams) -> None:
        method = BlackScholesAnalytical()
        result = await method.price(atm_call_params)
        # BSM Reference: 10.4506
        assert pytest.approx(result.price, abs=1e-4) == 10.4506

    @pytest.mark.asyncio
    async def test_analytical_put(self, atm_put_params: OptionParams) -> None:
        method = BlackScholesAnalytical()
        result = await method.price(atm_put_params)
        # BSM Reference: 5.5735
        assert pytest.approx(result.price, abs=1e-4) == 5.5735


@pytest.mark.unit
class TestCrankNicolson:
    """Tests for Crank-Nicolson FDM."""

    @pytest.mark.asyncio
    async def test_cn_european_call(self, atm_call_params: OptionParams) -> None:
        method = CrankNicolson()
        result = await method.price(atm_call_params)
        assert pytest.approx(result.price, abs=0.01) == 10.4506

    @pytest.mark.asyncio
    async def test_cn_european_put(self, atm_put_params: OptionParams) -> None:
        method = CrankNicolson()
        result = await method.price(atm_put_params)
        assert pytest.approx(result.price, abs=0.01) == 5.5735

    @pytest.mark.asyncio
    async def test_cn_american_put(self) -> None:
        """American puts should be more expensive than European puts."""
        params = OptionParams(
            underlying_price=100.0,
            strike_price=100.0,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type=OptionType.PUT,
            is_american=True,
        )
        method = CrankNicolson()
        result = await method.price(params)
        # European put is ~5.57. American should be > 5.57.
        assert result.price > 5.58


@pytest.mark.unit
class TestQuasiMC:
    """Tests for Quasi-Monte Carlo."""

    @pytest.mark.asyncio
    async def test_qmc_european_call(self, atm_call_params: OptionParams) -> None:
        method = QuasiMC()
        result = await method.price(atm_call_params)
        # QMC should be very close to analytical
        assert pytest.approx(result.price, abs=0.05) == 10.4506


@pytest.mark.unit
class TestTreeMethods:
    """Tests for Binomial Tree methods."""

    @pytest.mark.asyncio
    async def test_binomial_crr_call(self, atm_call_params: OptionParams) -> None:
        method = BinomialCRR()
        result = await method.price(atm_call_params)
        assert pytest.approx(result.price, abs=0.01) == 10.4506

    @pytest.mark.asyncio
    async def test_crr_richardson_call(self, atm_call_params: OptionParams) -> None:
        method = BinomialCRRRichardson()
        result = await method.price(atm_call_params)
        assert pytest.approx(result.price, abs=0.01) == 10.4506


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cross_method_agreement(atm_call_params: OptionParams) -> None:
    """Verify all methods agree within 0.5% for standard ATM call."""
    analytical_res = await BlackScholesAnalytical().price(atm_call_params)
    analytical = analytical_res.price
    
    cn_res = await CrankNicolson().price(atm_call_params)
    cn = cn_res.price
    
    qmc_res = await QuasiMC().price(atm_call_params)
    qmc = qmc_res.price
    
    crr_res = await BinomialCRRRichardson().price(atm_call_params)
    crr = crr_res.price

    results = [cn, qmc, crr]
    for res in results:
        mape = abs(res - analytical) / analytical
        assert mape < 0.005  # 0.5% tolerance for different methods
