"""Monte Carlo with Control Variates for variance reduction."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class ControlVariateMC:
    """
    Monte Carlo simulation using Control Variates.
    Uses the terminal stock price (S_T) as the control variate for European options.
    Provides excellent variance reduction for Black-Scholes comparison.
    """

    method_type: MethodType = "control_variate_mc"

    def __init__(self, num_simulations: int = 100000, num_steps: int = 1) -> None:
        # For European options with S_T as CV, we only need terminal prices (1 step)
        self.num_simulations = num_simulations
        self.num_steps = num_steps

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using CV Monte Carlo with CRN."""
        start_time = time.time()

        # Pre-generate samples for Common Random Numbers (CRN)
        standard_normal_samples = np.random.standard_normal((self.num_simulations, 1))

        def _solve_with_z(p: OptionParams, samples: np.ndarray[Any, Any]) -> float:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)

            terminal_prices = p.underlying_price * np.exp(drift + diffusion * samples)

            if p.option_type == "call":
                payoffs = np.maximum(terminal_prices - p.strike_price, 0)
            else:
                payoffs = np.maximum(p.strike_price - terminal_prices, 0)

            discount_factor = np.exp(-p.risk_free_rate * p.maturity_years)
            undiscounted_payoff = discount_factor * payoffs
            discounted_terminal_price = discount_factor * terminal_prices
            expected_cv = p.underlying_price  # E[discount_factor * S_T] = S_0

            # Optimal beta
            cov_matrix = np.cov(undiscounted_payoff.flatten(), discounted_terminal_price.flatten())
            beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] > 0 else 0.0
            return float(
                np.mean(undiscounted_payoff - beta * (discounted_terminal_price - expected_cv))
            )

        computed_price = _solve_with_z(params, standard_normal_samples)

        def _get_std_err(p: OptionParams, samples: np.ndarray[Any, Any]) -> float:
            drift = (p.risk_free_rate - 0.5 * p.volatility**2) * p.maturity_years
            diffusion = p.volatility * np.sqrt(p.maturity_years)
            terminal_prices = p.underlying_price * np.exp(drift + diffusion * samples)
            payoffs = (
                np.maximum(terminal_prices - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - terminal_prices, 0)
            )
            discount_factor = np.exp(-p.risk_free_rate * p.maturity_years)
            y, x = discount_factor * payoffs, discount_factor * terminal_prices
            expected_cv = p.underlying_price
            cov_matrix = np.cov(y.flatten(), x.flatten())
            beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] > 0 else 0.0
            controlled = y - beta * (x - expected_cv)
            return float(np.std(controlled) / np.sqrt(self.num_simulations))

        standard_error = _get_std_err(params, standard_normal_samples)

        # Bumping for Greeks using same Z (CRN)
        spot_bump, vol_bump, time_bump, rate_bump = (
            params.underlying_price * 0.01,
            0.01,
            1 / 365.0,
            0.01,
        )

        # Delta & Gamma
        p_up = params.model_copy(update={"underlying_price": params.underlying_price + spot_bump})
        p_dn = params.model_copy(update={"underlying_price": params.underlying_price - spot_bump})
        price_up, price_dn = _solve_with_z(p_up, standard_normal_samples), _solve_with_z(
            p_dn, standard_normal_samples
        )
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
            computed_price=float(computed_price),
            exec_seconds=time.time() - start_time,
            replications=self.num_simulations,
            confidence_interval=(
                float(computed_price - 1.96 * standard_error),
                float(computed_price + 1.96 * standard_error),
            ),
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            parameter_set={
                "num_simulations": self.num_simulations,
                "num_steps": self.num_steps,
            },
        )
