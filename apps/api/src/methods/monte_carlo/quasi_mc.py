"""Quasi-Monte Carlo implementation using Sobol sequences."""

from __future__ import annotations

import time

import numpy as np
from scipy.stats import norm, qmc

from src.methods.base import OptionParams, NumericalMethod, PriceResult


class QuasiMC(NumericalMethod):
    """
    Quasi-Monte Carlo pricing using Sobol sequences with scrambling.
    Achieves O(N^-1) convergence.
    """

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price using Quasi-Monte Carlo."""
        start_time = time.perf_counter()

        # Enforce num_paths = 2^n
        power_of_two = 17
        num_paths = 2**power_of_two

        sampler = qmc.Sobol(d=1, scramble=True)
        uniform_samples = sampler.random(num_paths)

        clipped_samples = np.clip(uniform_samples, 1e-10, 1.0 - 1e-10)
        normal_samples = norm.ppf(clipped_samples).flatten()

        underlying = params.underlying_price
        strike = params.strike_price
        expiry = params.maturity_years
        rate = params.risk_free_rate
        sigma = params.volatility

        terminal_prices = underlying * np.exp(
            (rate - 0.5 * sigma**2) * expiry + sigma * np.sqrt(expiry) * normal_samples
        )

        if params.is_call:
            payoffs = np.maximum(terminal_prices - strike, 0.0)
        else:
            payoffs = np.maximum(strike - terminal_prices, 0.0)

        discount_factor = np.exp(-rate * expiry)
        final_price = discount_factor * np.mean(payoffs)

        return PriceResult(
            method_type="quasi_mc",
            computed_price=float(final_price),
            exec_seconds=time.perf_counter() - start_time,
            metadata={"num_paths": num_paths},
        )
