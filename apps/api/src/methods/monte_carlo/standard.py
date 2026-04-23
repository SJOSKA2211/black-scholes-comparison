"""Standard Monte Carlo simulation."""

from __future__ import annotations

import time

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
        z = np.random.standard_normal(self.num_simulations)
        discount_factor = np.exp(-params.risk_free_rate * params.maturity_years)

        def _solve_with_z(p: OptionParams, samples: np.ndarray) -> float:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)
            s_t = p.underlying_price * np.exp(drift + diffusion * samples)
            payoffs = (
                np.maximum(s_t - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - s_t, 0)
            )
            df = np.exp(-p.risk_free_rate * p.maturity_years)
            return float(np.mean(df * payoffs))

        computed_price = _solve_with_z(params, z)

        # Bumping for Greeks using same Z (CRN)
        h_s, h_v, h_t, h_r = params.underlying_price * 0.01, 0.01, 1 / 365.0, 0.01

        # Delta & Gamma (Central Difference)
        p_up = params.model_copy(update={"underlying_price": params.underlying_price + h_s})
        p_dn = params.model_copy(update={"underlying_price": params.underlying_price - h_s})
        price_up, price_dn = _solve_with_z(p_up, z), _solve_with_z(p_dn, z)
        delta = (price_up - price_dn) / (2 * h_s)
        gamma = (price_up - 2 * computed_price + price_dn) / (h_s**2)

        # Vega
        p_v_up = params.model_copy(update={"volatility": params.volatility + h_v})
        vega = (_solve_with_z(p_v_up, z) - computed_price) / h_v

        # Theta
        if params.maturity_years > h_t:
            p_t_dn = params.model_copy(update={"maturity_years": params.maturity_years - h_t})
            theta = -(computed_price - _solve_with_z(p_t_dn, z)) / h_t
        else:
            theta = 0.0

        # Rho
        p_r_up = params.model_copy(update={"risk_free_rate": params.risk_free_rate + h_r})
        rho = (_solve_with_z(p_r_up, z) - computed_price) / h_r

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
