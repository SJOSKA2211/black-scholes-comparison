"""Quasi-Monte Carlo pricing using Sobol sequences."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm, qmc

from src.methods.base import BasePricingMethod, OptionParameters, OptionType


class QuasiMC(BasePricingMethod):
    """Quasi-Monte Carlo solver with Sobol sequences."""

    def __init__(self, num_paths: int = 131072) -> None:
        super().__init__("quasi_mc")
        # Enforce power of 2 for Sobol
        exponent = int(np.round(np.log2(num_paths)))
        self.num_paths = 2**exponent

    def _compute(self, params: OptionParameters) -> float:
        """Execute Quasi-Monte Carlo computation."""
        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        volatility = params.volatility
        rate = params.risk_free_rate

        # Sobol sequence generation
        sampler = qmc.Sobol(d=1, scramble=True)
        sobol_points = sampler.random(n=self.num_paths).flatten()

        # Probit transform (clipped to avoid inf)
        clipped_points = np.clip(sobol_points, 1e-10, 1 - 1e-10)
        norm_variates = norm.ppf(clipped_points)

        # Path simulation
        drift = (rate - 0.5 * volatility**2) * maturity
        diffusion = volatility * np.sqrt(maturity) * norm_variates
        terminal_prices = underlying * np.exp(drift + diffusion)

        # Payoff calculation
        if params.option_type == OptionType.CALL:
            payoffs = np.maximum(terminal_prices - strike, 0)
        else:
            payoffs = np.maximum(strike - terminal_prices, 0)

        discounted_mean = np.exp(-rate * maturity) * np.mean(payoffs)
        return float(discounted_mean)
