"""Black-Scholes analytical closed-form implementation."""

import time
from typing import Any, cast

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from src.methods.base import NumericalMethod, OptionParams, OptionType, PriceResult


class BlackScholesAnalytical(NumericalMethod):
    """Standard Black-Scholes-Merton analytical formula."""

    async def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        vol = params.volatility
        rate = params.risk_free_rate

        d1 = (np.log(underlying / strike) + (rate + 0.5 * vol**2) * maturity) / (
            vol * np.sqrt(maturity)
        )
        d2 = d1 - vol * np.sqrt(maturity)

        if params.option_type == OptionType.CALL:
            price = underlying * norm.cdf(d1) - strike * np.exp(-rate * maturity) * norm.cdf(d2)
        else:
            price = strike * np.exp(-rate * maturity) * norm.cdf(-d2) - underlying * norm.cdf(-d1)

        exec_time = time.perf_counter() - start_time
        return PriceResult(price=float(price), exec_seconds=exec_time)

    def implied_volatility(self, market_price: float, params: OptionParams) -> float:
        """Invert Black-Scholes to find implied volatility using Brent's method."""

        def objective(sigma: float) -> float:
            # Synchronous version for optimization
            d1 = (
                np.log(params.underlying_price / params.strike_price)
                + (params.risk_free_rate + 0.5 * sigma**2) * params.maturity_years
            ) / (sigma * np.sqrt(params.maturity_years))
            d2 = d1 - sigma * np.sqrt(params.maturity_years)
            if params.option_type == OptionType.CALL:
                price = params.underlying_price * norm.cdf(d1) - params.strike_price * np.exp(
                    -params.risk_free_rate * params.maturity_years
                ) * norm.cdf(d2)
            else:
                price = params.strike_price * np.exp(
                    -params.risk_free_rate * params.maturity_years
                ) * norm.cdf(-d2) - params.underlying_price * norm.cdf(-d1)
            return float(price - market_price)

        try:
            return cast(float, brentq(objective, 1e-6, 5.0))
        except ValueError:
            return 0.0
