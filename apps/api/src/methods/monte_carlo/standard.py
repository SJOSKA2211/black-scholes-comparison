"""Standard Monte Carlo simulation."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class StandardMC:
    """
    Standard Monte Carlo simulation for European options.
    Generates N random paths and computes the discounted average payoff.
    """

    method_type: MethodType = "standard_mc"

    def __init__(self, num_simulations: int = 100000) -> None:
        self.num_simulations = num_simulations

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using Standard Monte Carlo with CRN."""
        start_time = time.time()

        # Pre-generate Gaussian samples for Common Random Numbers (CRN)
        standard_normal_samples = np.random.standard_normal(self.num_simulations)

        def _solve_with_z(p: OptionParams, samples: np.ndarray[Any, Any]) -> float:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)
            terminal_prices = p.underlying_price * np.exp(drift + diffusion * samples)
            payoffs = (
                np.maximum(terminal_prices - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - terminal_prices, 0)
            )
            discount_factor = np.exp(-p.risk_free_rate * p.maturity_years)
            return float(np.mean(discount_factor * payoffs))

        computed_price = _solve_with_z(params, standard_normal_samples)

        # Bumping for Greeks using same Z (CRN)
        spot_bump, vol_bump, time_bump, rate_bump = params.underlying_price * 0.01, 0.01, 1 / 365.0, 0.01

        # Delta & Gamma (Central Difference)
        p_up = params.model_copy(update={"underlying_price": params.underlying_price + spot_bump})
        p_dn = params.model_copy(update={"underlying_price": params.underlying_price - spot_bump})
        price_up, price_dn = _solve_with_z(p_up, standard_normal_samples), _solve_with_z(p_dn, standard_normal_samples)
        delta = (price_up - price_dn) / (2 * spot_bump)
        gamma = (price_up - 2 * computed_price + price_dn) / (spot_bump**2)

        # Vega
        p_v_up = params.model_copy(update={"volatility": params.volatility + vol_bump})
        vega = (_solve_with_z(p_v_up, standard_normal_samples) - computed_price) / vol_bump

        # Theta
        if params.maturity_years > time_bump:
            p_t_dn = params.model_copy(update={"maturity_years": params.maturity_years - time_bump})
            theta = -(computed_price - _solve_with_z(p_t_dn, standard_normal_samples)) / time_bump
        else:
            theta = 0.0

        # Rho
        p_r_up = params.model_copy(update={"risk_free_rate": params.risk_free_rate + rate_bump})
        rho = (_solve_with_z(p_r_up, standard_normal_samples) - computed_price) / rate_bump

        return PriceResult(
            method_type=self.method_type,
            computed_price=computed_price,
            exec_seconds=time.time() - start_time,
            replications=self.num_simulations,
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            parameter_set={"num_simulations": self.num_simulations},
        )
