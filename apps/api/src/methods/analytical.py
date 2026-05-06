"""Analytical Black-Scholes-Merton implementation."""
from __future__ import annotations
import time
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
from src.methods.base import NumericalMethod, OptionParams, PriceResult


class BlackScholesAnalytical(NumericalMethod):
    """Closed-form analytical solution for European options."""

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the analytical price and Greeks."""
        start_time = time.perf_counter()
        price, greeks = self._compute_price_and_greeks(params)
        return PriceResult(
            method_type="analytical",
            computed_price=price,
            exec_seconds=time.perf_counter() - start_time,
            delta=greeks.get("delta"),
            gamma=greeks.get("gamma"),
            vega=greeks.get("vega"),
            metadata=greeks
        )

    def _compute_price_and_greeks(self, params: OptionParams) -> tuple[float, dict[str, float]]:
        underlying = params.underlying_price
        strike = params.strike_price
        expiry = params.maturity_years
        rate = params.risk_free_rate
        sigma = params.volatility
        sqrt_expiry = np.sqrt(expiry)
        term_one = (np.log(underlying / strike) + (rate + 0.5 * sigma**2) * expiry) / (sigma * sqrt_expiry)
        term_two = term_one - sigma * sqrt_expiry
        if params.is_call:
            price = underlying * norm.cdf(term_one) - strike * np.exp(-rate * expiry) * norm.cdf(term_two)
            delta = norm.cdf(term_one)
        else:
            price = strike * np.exp(-rate * expiry) * norm.cdf(-term_two) - underlying * norm.cdf(-term_one)
            delta = norm.cdf(term_one) - 1
        gamma = norm.pdf(term_one) / (underlying * sigma * sqrt_expiry)
        vega = underlying * norm.pdf(term_one) * sqrt_expiry
        return float(price), {"delta": float(delta), "gamma": float(gamma), "vega": float(vega)}

    def implied_volatility(self, market_price: float, params: OptionParams) -> float:
        if market_price <= 0: return 0.0
        def obj(v: float) -> float:
            p, _ = self._compute_price_and_greeks(params.model_copy(update={"volatility": v}))
            return p - market_price
        try: return float(brentq(obj, 1e-6, 5.0))
        except ValueError: return 0.0

    def delta(self, p: OptionParams) -> float: return self._compute_price_and_greeks(p)[1]["delta"]
    def gamma(self, p: OptionParams) -> float: return self._compute_price_and_greeks(p)[1]["gamma"]
    def vega(self, p: OptionParams) -> float: return self._compute_price_and_greeks(p)[1]["vega"]
    def rho(self, p: OptionParams) -> float: return 0.0
    def theta(self, p: OptionParams) -> float: return 0.0
    def geometric_asian_price(self, p: OptionParams) -> PriceResult:
        return self.price(p)
