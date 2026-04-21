import time

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from src.methods.base import OptionParams, PriceResult


class BlackScholesAnalytical:
    """Closed-form Black-Scholes model for European options."""

    def price(self, params: OptionParams) -> PriceResult:
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        d1 = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        d2 = d1 - volatility * np.sqrt(maturity_years)

        if params.option_type == "call":
            price = underlying_price * norm.cdf(d1) - strike_price * np.exp(
                -risk_free_rate * maturity_years
            ) * norm.cdf(d2)
        else:
            price = strike_price * np.exp(-risk_free_rate * maturity_years) * norm.cdf(
                -d2
            ) - underlying_price * norm.cdf(-d1)

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="analytical",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={},
        )

    def delta(self, params: OptionParams) -> float:
        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        d1 = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        if params.option_type == "call":
            return float(norm.cdf(d1))
        else:
            return float(norm.cdf(d1) - 1)

    def gamma(self, params: OptionParams) -> float:
        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        d1 = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        gamma_value = norm.pdf(d1) / (
            underlying_price * volatility * np.sqrt(maturity_years)
        )
        return float(gamma_value)

    def vega(self, params: OptionParams) -> float:
        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        d1 = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        vega_value = underlying_price * norm.pdf(d1) * np.sqrt(maturity_years)
        return float(vega_value)

    def implied_volatility(self, market_price: float, params: OptionParams) -> float:
        def objective(sigma_test):
            test_params = params.model_copy(update={"volatility": sigma_test})
            return self.price(test_params).computed_price - market_price

        try:
            return float(brentq(objective, 1e-6, 5.0))
        except ValueError:
            return 0.0

    def geometric_asian_price(self, params: OptionParams) -> PriceResult:
        """Closed-form solution for continuous geometric Asian options."""
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        volatility_geometric = volatility / np.sqrt(3)
        drift_geometric = 0.5 * (risk_free_rate - (volatility**2 / 6))

        d1 = (
            np.log(underlying_price / strike_price)
            + (drift_geometric + 0.5 * volatility_geometric**2) * maturity_years
        ) / (volatility_geometric * np.sqrt(maturity_years))
        d2 = d1 - volatility_geometric * np.sqrt(maturity_years)

        if params.option_type == "call":
            price = underlying_price * np.exp(
                (drift_geometric - risk_free_rate) * maturity_years
            ) * norm.cdf(d1) - strike_price * np.exp(
                -risk_free_rate * maturity_years
            ) * norm.cdf(
                d2
            )
        else:
            price = strike_price * np.exp(-risk_free_rate * maturity_years) * norm.cdf(
                -d2
            ) - underlying_price * np.exp(
                (drift_geometric - risk_free_rate) * maturity_years
            ) * norm.cdf(
                -d1
            )

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="analytical",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"asian_type": "geometric_continuous"},
        )
