"""Quasi-Monte Carlo Pricing using Sobol sequences."""

import time

import numpy as np
from scipy.stats import norm, qmc

from src.methods.base import NumericalMethod, OptionParams, OptionType, PriceResult


class QuasiMC(NumericalMethod):
    """
    Quasi-Monte Carlo pricing using Sobol sequences.
    Achieves O(N^-1) convergence vs O(N^-1/2) for standard MC.
    """

    async def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        # Power of 2 paths for Sobol efficiency
        num_paths = 2**17  # 131,072

        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        vol = params.volatility
        rate = params.risk_free_rate

        # Sobol sequence generation
        sampler = qmc.Sobol(d=1, scramble=True)
        sample = sampler.random(n=num_paths)

        # Probit transform (Inverse Normal CDF)
        # Clip sample to avoid infinity at 0 and 1
        z_scores = norm.ppf(np.clip(sample, 1e-10, 1 - 1e-10)).flatten()

        # Asset price paths at maturity
        prices_at_maturity = underlying * np.exp(
            (rate - 0.5 * vol**2) * maturity + vol * np.sqrt(maturity) * z_scores
        )

        # Payoff calculation
        if params.option_type == OptionType.CALL:
            payoffs = np.maximum(prices_at_maturity - strike, 0)
        else:
            payoffs = np.maximum(strike - prices_at_maturity, 0)

        # Discounted mean payoff
        price = np.exp(-rate * maturity) * np.mean(payoffs)

        exec_time = time.perf_counter() - start_time
        return PriceResult(
            price=float(price), exec_seconds=exec_time, metadata={"num_paths": num_paths}
        )
