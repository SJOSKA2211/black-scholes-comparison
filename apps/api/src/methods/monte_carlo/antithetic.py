"""Monte Carlo with Antithetic Variates for variance reduction."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class AntitheticMC:
    """
    Monte Carlo simulation using Antithetic Variates.
    Reduces variance by using both gaussian_samples and -gaussian_samples for path generation,
    effectively creating negatively correlated pairs.
    """

    method_type: MethodType = "antithetic_mc"

    def __init__(self, num_simulations: int = 50000) -> None:
        # We use num_simulations pairs (total 2 * num_simulations paths)
        self.num_simulations = num_simulations

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using Antithetic Monte Carlo with CRN."""
        start_time = time.time()

        # Pre-generate Gaussian samples for Common Random Numbers (CRN)
        z = np.random.standard_normal(self.num_simulations)

        def _solve_with_z(p: OptionParams, samples: np.ndarray) -> tuple[float, float]:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)
            df = np.exp(-p.risk_free_rate * p.maturity_years)

            # Antithetic paths
            terminal_prices_one = p.underlying_price * np.exp(drift + diffusion * samples)
            terminal_prices_two = p.underlying_price * np.exp(drift - diffusion * samples)

            if p.option_type == "call":
                payoffs_one = np.maximum(terminal_prices_one - p.strike_price, 0)
                payoffs_two = np.maximum(terminal_prices_two - p.strike_price, 0)
            else:
                payoffs_one = np.maximum(p.strike_price - terminal_prices_one, 0)
                payoffs_two = np.maximum(p.strike_price - terminal_prices_two, 0)

            pair_averages = 0.5 * df * (payoffs_one + payoffs_two)
            return float(np.mean(pair_averages)), float(np.std(pair_averages) / np.sqrt(len(samples)))

        computed_price, std_err = _solve_with_z(params, z)

        # Bumping for Greeks using same Z (CRN)
        h_s, h_v, h_t, h_r = params.underlying_price * 0.01, 0.01, 1 / 365.0, 0.01

        # Delta & Gamma
        p_up = params.model_copy(update={"underlying_price": params.underlying_price + h_s})
        p_dn = params.model_copy(update={"underlying_price": params.underlying_price - h_s})
        price_up, _ = _solve_with_z(p_up, z)
        price_dn, _ = _solve_with_z(p_dn, z)
        delta = (price_up - price_dn) / (2 * h_s)
        gamma = (price_up - 2 * computed_price + price_dn) / (h_s**2)

        # Vega
        p_v_up = params.model_copy(update={"volatility": params.volatility + h_v})
        price_v_up, _ = _solve_with_z(p_v_up, z)
        vega = (price_v_up - computed_price) / h_v

        # Theta
        if params.maturity_years > h_t:
            p_t_dn = params.model_copy(update={"maturity_years": params.maturity_years - h_t})
            price_t_dn, _ = _solve_with_z(p_t_dn, z)
            theta = -(computed_price - price_t_dn) / h_t
        else:
            theta = 0.0

        # Rho
        p_r_up = params.model_copy(update={"risk_free_rate": params.risk_free_rate + h_r})
        price_r_up, _ = _solve_with_z(p_r_up, z)
        rho = (price_r_up - computed_price) / h_r

        return PriceResult(
            method_type=self.method_type,
            computed_price=computed_price,
            exec_seconds=time.time() - start_time,
            replications=self.num_simulations * 2,
            confidence_interval=(
                float(computed_price - 1.96 * std_err),
                float(computed_price + 1.96 * std_err),
            ),
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            parameter_set={"num_pairs": self.num_simulations},
        )
