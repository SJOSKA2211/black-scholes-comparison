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
        """Boyle (1988) Three-branch lattice Trinomial tree solver."""
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        time_step = maturity_years / self.num_steps
        up_factor = np.exp(volatility * np.sqrt(2 * time_step))
        discount_factor = np.exp(-risk_free_rate * time_step)

        # Boyle (1986) probabilities
        numerator_up = np.exp(risk_free_rate * time_step / 2) - np.exp(
            -volatility * np.sqrt(time_step / 2)
        )
        denominator_base = np.exp(volatility * np.sqrt(time_step / 2)) - np.exp(
            -volatility * np.sqrt(time_step / 2)
        )
        prob_up = (numerator_up / denominator_base) ** 2

        numerator_down = np.exp(volatility * np.sqrt(time_step / 2)) - np.exp(
            risk_free_rate * time_step / 2
        )
        prob_down = (numerator_down / denominator_base) ** 2

        prob_mid = 1.0 - prob_up - prob_down

        # Grid sizes
        indices = np.arange(self.num_steps, -self.num_steps - 1, -1)
        terminal_underlyings = underlying_price * (up_factor**indices)

        if params.option_type == "call":
            values = np.maximum(terminal_underlyings - strike_price, 0)
        else:
            values = np.maximum(strike_price - terminal_underlyings, 0)

        for step_idx in range(self.num_steps - 1, -1, -1):
            values = discount_factor * (
                prob_up * values[:-2] + prob_mid * values[1:-1] + prob_down * values[2:]
            )
            if params.is_american:
                step_indices = np.arange(step_idx, -step_idx - 1, -1)
                underlyings_at_step = underlying_price * (up_factor**step_indices)
                if params.option_type == "call":
                    exercise_values = np.maximum(underlyings_at_step - strike_price, 0)
                else:
                    exercise_values = np.maximum(strike_price - underlyings_at_step, 0)
                values = np.maximum(values, exercise_values)

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=float(values[0]),
            exec_seconds=exec_seconds,
            parameter_set={"num_steps": self.num_steps},
        )
