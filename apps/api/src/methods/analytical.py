"""Standard Black-Scholes-Merton analytical formula implementation."""

from __future__ import annotations

import time
from math import exp, log, sqrt

from scipy.stats import norm

from src.methods.base import NumericalMethod, OptionParams, PriceResult


class BlackScholesAnalytical(NumericalMethod):
    """Closed-form solution for European options."""

    def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        vol = params.volatility
        rate = params.risk_free_rate

        sqrt_t = sqrt(maturity)
        d1 = (log(underlying / strike) + (rate + 0.5 * vol**2) * maturity) / (vol * sqrt_t)
        d2 = d1 - vol * sqrt_t

        if params.is_call:
            price = underlying * norm.cdf(d1) - strike * exp(-rate * maturity) * norm.cdf(d2)
            delta = norm.cdf(d1)
        else:
            price = strike * exp(-rate * maturity) * norm.cdf(-d2) - underlying * norm.cdf(-d1)
            delta = norm.cdf(d1) - 1

        # Common Greeks
        gamma = norm.pdf(d1) / (underlying * vol * sqrt_t)
        vega = underlying * norm.pdf(d1) * sqrt_t

        return PriceResult(
            method_type="analytical",
            computed_price=price,
            exec_seconds=time.perf_counter() - start_time,
            delta=delta,
            gamma=gamma,
            vega=vega,
        )
