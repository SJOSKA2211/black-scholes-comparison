from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.config import Settings
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams
from src.methods.finite_difference.crank_nicolson import CrankNicolsonFDM
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.finite_difference.implicit import ImplicitFDM
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.monte_carlo.standard import StandardMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson, TrinomialRichardson
from src.methods.tree_methods.trinomial import TrinomialTree
from src.routers.pricing import compare_methods


@pytest.mark.unit
class TestMissingCoverage:
    def test_config_rabbitmq_override(self) -> None:
        # src/config.py:48
        s = Settings(RABBITMQ_URL="amqp://override")
        assert s.rabbitmq_url == "amqp://override"

    def test_config_rabbitmq_no_override(self) -> None:
        s = Settings(RABBITMQ_URL=None)
        assert "amqp://" in s.rabbitmq_url

    def test_analytical_iv_failure(self) -> None:
        method = BlackScholesAnalytical()
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        iv = method.implied_volatility(target_price=1000, params=params)
        assert iv == 0.0

    def test_fdm_boundary_delta(self) -> None:
        params_low = OptionParams(
            underlying_price=0.0001,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        CrankNicolsonFDM(num_time_steps=10, num_price_steps=10).price(params_low)
        ExplicitFDM(num_time_steps=10, num_price_steps=10).price(params_low)
        ImplicitFDM(num_time_steps=10, num_price_steps=10).price(params_low)

        params_high = OptionParams(
            underlying_price=500.0,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        CrankNicolsonFDM(num_time_steps=10, num_price_steps=10).price(params_high)
        ExplicitFDM(num_time_steps=10, num_price_steps=10).price(params_high)
        ImplicitFDM(num_time_steps=10, num_price_steps=10).price(params_high)

    def test_explicit_fdm_cfl_bumping(self) -> None:
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.22,
            risk_free_rate=0.05,
            option_type="call",
        )
        method = ExplicitFDM(num_time_steps=10, num_price_steps=10)
        method.price(params)

    def test_mc_replications_branch(self) -> None:
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=0.0001,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        StandardMC(num_simulations=10).price(params)
        AntitheticMC(num_simulations=10).price(params)
        ControlVariateMC(num_simulations=10).price(params)
        QuasiMC(num_simulations=10).price(params)

    def test_tree_steps_branch(self) -> None:
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=0.0001,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        BinomialCRRRichardson(num_steps=1).price(params)
        TrinomialTree(num_steps=0).price(params)
        TrinomialTree(num_steps=1).price(params)

    def test_richardson_none_greeks(self) -> None:
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        from src.methods.base import PriceResult

        mock_res = PriceResult(
            method_type="binomial_crr", computed_price=10.0, exec_seconds=0.1, delta=None
        )
        with patch("src.methods.tree_methods.richardson.BinomialCRR.price", return_value=mock_res):
            BinomialCRRRichardson(num_steps=10).price(params)

        with patch(
            "src.methods.tree_methods.richardson.TrinomialTree.price", return_value=mock_res
        ):
            TrinomialRichardson(num_steps=10).price(params)

    async def test_pricing_router_compare_success_with_analytical(self) -> None:
        # Coverage for pricing.py: 204->207 (branch where analytical is ALREADY in methods)
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        mock_user = {"id": "test-user"}
        # No need to patch anything if it works
        await compare_methods(params, methods=["analytical", "standard_mc"], user=mock_user)

    async def test_pricing_router_compare_exception(self) -> None:
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        mock_user = {"id": "test-user"}
        with (
            patch(
                "src.routers.pricing.get_method_instance", side_effect=Exception("Compare failed")
            ),
            pytest.raises(HTTPException),
        ):
            await compare_methods(params, methods=["standard_mc"], user=mock_user)

    async def test_scrapers_router_exception(self) -> None:
        from src.routers.scrapers import trigger_scraper

        mock_user = {"id": "test-user"}
        with patch(
            "src.routers.scrapers.publish_scrape_task", side_effect=Exception("Scraper failed")
        ):
            with pytest.raises(HTTPException) as excinfo:
                await trigger_scraper(market="spy", current_user=mock_user)
            assert excinfo.value.status_code == 500

    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_value_error(self, mock_pw) -> None:
        from src.scrapers.nse_next_scraper import NSEScraper

        s = NSEScraper("run-123")
        mock_page = AsyncMock()
        mock_expiry_el = MagicMock()
        mock_expiry_el.get_attribute = AsyncMock(return_value="INVALID-DATE")
        mock_page.query_selector.side_effect = [
            None,  # underlying
            mock_expiry_el,  # expirySelect
            None,  # optionChainTable
        ]
        mock_browser = AsyncMock()
        mock_browser.new_context.return_value.new_page.return_value = mock_page
        mock_pw.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
        await s.scrape(date(2024, 1, 1))

    def test_methods_base_protocol(self) -> None:
        from src.methods.base import NumericalMethod

        class Dummy:
            def price(self, params) -> None:
                pass

        assert isinstance(Dummy(), NumericalMethod)

    def test_analytical_asian(self) -> None:
        method = BlackScholesAnalytical()
        params = OptionParams(
            underlying_price=100,
            strike_price=100,
            maturity_years=1,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type="call",
        )
        method.geometric_asian_price(params, num_steps=10)
        params_put = params.model_copy(update={"option_type": "put"})
        method.geometric_asian_price(params_put, num_steps=10)
