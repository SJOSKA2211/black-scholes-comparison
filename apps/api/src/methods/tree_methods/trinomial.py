"""Trinomial tree method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class TrinomialTree:
    """Trinomial tree wrapper using Boyle (1988) lattice."""

    def __init__(self, num_steps: int = 500) -> None:
        self.num_steps = num_steps
        self.method_type: MethodType = "trinomial"

    def price(self, params: OptionParams) -> PriceResult:
        """Boyle (1988) Three-branch lattice Trinomial tree solver with Greeks."""
        if self.num_steps < 1:
            return PriceResult(
                method_type=self.method_type,
                computed_price=0.0,
                exec_seconds=0.0,
                delta=0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
            )
        start_time = time.time()

        def _solve(p: OptionParams) -> tuple[float, float, float]:
            time_step_size = p.maturity_years / self.num_steps
            up_factor = np.exp(p.volatility * np.sqrt(2 * time_step_size))
            discount = np.exp(-p.risk_free_rate * time_step_size)

            # Boyle probabilities
            num_up = np.exp(p.risk_free_rate * time_step_size / 2) - np.exp(
                -p.volatility * np.sqrt(time_step_size / 2)
            )
            den = np.exp(p.volatility * np.sqrt(time_step_size / 2)) - np.exp(
                -p.volatility * np.sqrt(time_step_size / 2)
            )
            prob_up = (num_up / den) ** 2
            prob_down = (
                (
                    np.exp(p.volatility * np.sqrt(time_step_size / 2))
                    - np.exp(p.risk_free_rate * time_step_size / 2)
                )
                / den
            ) ** 2
            prob_middle = 1.0 - prob_up - prob_down

            # Terminal values
            indices = np.arange(self.num_steps, -self.num_steps - 1, -1)
            underlyings = p.underlying_price * (up_factor**indices)

            if p.option_type == "call":
                values = np.maximum(underlyings - p.strike_price, 0)
            else:
                values = np.maximum(p.strike_price - underlyings, 0)

            terminal_values = np.copy(values)

            # Backward induction
            for step in range(self.num_steps - 1, -1, -1):
                values = discount * (
                    prob_up * values[:-2] + prob_middle * values[1:-1] + prob_down * values[2:]
                )
                if p.is_american:
                    step_indices = np.arange(step, -step - 1, -1)
                    s_step = p.underlying_price * (up_factor**step_indices)
                    exercise = (
                        np.maximum(s_step - p.strike_price, 0)
                        if p.option_type == "call"
                        else np.maximum(p.strike_price - s_step, 0)
                    )
                    values = np.maximum(values, exercise)

                # Capture values at step 1 for Delta/Gamma
                if step == 1:
                    v_u, v_m, v_d = values[0], values[1], values[2]

            # If num_steps=1, we don't go through the loop correctly for v_u/v_m/v_d
            if self.num_steps == 1:
                # Manually compute step 1 values (terminal values)
                v_u, v_m, v_d = terminal_values[0], terminal_values[1], terminal_values[2]

            # For delta/gamma we need step 1 underlyings
            s_u = p.underlying_price * up_factor
            s_m = p.underlying_price
            s_d = p.underlying_price / up_factor

            delta = (v_u - v_d) / (s_u - s_d)
            gamma = ((v_u - v_m) / (s_u - s_m) - (v_m - v_d) / (s_m - s_d)) / (0.5 * (s_u - s_d))

            return float(values[0]), float(delta), float(gamma)

        computed_price, delta, gamma = _solve(params)

        # Bumping for Vega, Theta, Rho
        vol_bump, time_bump, rate_bump = 0.01, 1 / 365.0, 0.01

        def get_p(p: OptionParams) -> float:
            v_val, _, _ = _solve(p)
            return v_val

        vega = (
            get_p(params.model_copy(update={"volatility": params.volatility + vol_bump}))
            - computed_price
        ) / vol_bump
        theta = (
            -(
                computed_price
                - get_p(
                    params.model_copy(
                        update={"maturity_years": max(0.0001, params.maturity_years - time_bump)}
                    )
                )
            )
            / time_bump
            if params.maturity_years > time_bump
            else 0.0
        )
        rho = (
            get_p(params.model_copy(update={"risk_free_rate": params.risk_free_rate + rate_bump}))
            - computed_price
        ) / rate_bump

        return PriceResult(
            method_type=self.method_type,
            computed_price=computed_price,
            exec_seconds=time.time() - start_time,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            parameter_set={"num_steps": self.num_steps},
        )
