"""Quasi-Monte Carlo method for option pricing."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from scipy.stats import norm, qmc

from src.methods.base import MethodType, OptionParams, PriceResult


class QuasiMC:
    """Quasi-Monte Carlo wrapper using Sobol sequences."""

    method_type: MethodType = "quasi_mc"

    def __init__(self, num_simulations: int = 65536) -> None:
        self.num_simulations = num_simulations

    def price(self, params: OptionParams) -> PriceResult:
        """Quasi-Monte Carlo using Sobol sequence with CRN for Greeks."""
        start_time = time.time()
        # Enforce power of 2 for Sobol efficiency
        effective_num_simulations = 2 ** int(np.round(np.log2(self.num_simulations)))

        sampler = qmc.Sobol(d=1, scramble=True)
        uniform_samples = sampler.random(n=effective_num_simulations)
        # Inverse transform to standard normal
        gaussian_samples = norm.ppf(uniform_samples).flatten()

        def _solve_with_samples(p: OptionParams, samples: np.ndarray[Any, Any]) -> float:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)
            terminal_prices = p.underlying_price * np.exp(drift + diffusion * samples)

            if p.option_type == "call":
                payoffs = np.maximum(terminal_prices - p.strike_price, 0)
            else:
                payoffs = np.maximum(p.strike_price - terminal_prices, 0)

            discount_factor = np.exp(-p.risk_free_rate * p.maturity_years)
            return float(np.mean(discount_factor * payoffs))

        computed_price = _solve_with_samples(params, gaussian_samples)

        # Bumping for Greeks using same Sobol samples (CRN)
        spot_bump, vol_bump, time_bump, rate_bump = params.underlying_price * 0.01, 0.01, 1 / 365.0, 0.01

        # Delta & Gamma
        p_up = params.model_copy(update={"underlying_price": params.underlying_price + spot_bump})
        p_dn = params.model_copy(update={"underlying_price": params.underlying_price - spot_bump})
        price_up, price_dn = _solve_with_samples(p_up, gaussian_samples), _solve_with_samples(
            p_dn, gaussian_samples
        )
        delta = (price_up - price_dn) / (2 * spot_bump)
        gamma = (price_up - 2 * computed_price + price_dn) / (spot_bump**2)

        # Vega
        p_v_up = params.model_copy(update={"volatility": params.volatility + vol_bump})
        vega = (_solve_with_samples(p_v_up, gaussian_samples) - computed_price) / vol_bump

        # Theta
        if params.maturity_years > time_bump:
            p_t_dn = params.model_copy(update={"maturity_years": params.maturity_years - time_bump})
            theta = -(computed_price - _solve_with_samples(p_t_dn, gaussian_samples)) / time_bump
        else:
            theta = 0.0

        # Rho
        p_r_up = params.model_copy(update={"risk_free_rate": params.risk_free_rate + rate_bump})
        rho = (_solve_with_samples(p_r_up, gaussian_samples) - computed_price) / rate_bump

        return PriceResult(
            method_type=self.method_type,
            computed_price=computed_price,
            exec_seconds=time.time() - start_time,
            replications=effective_num_simulations,
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            parameter_set={"num_simulations": effective_num_simulations},
        )
