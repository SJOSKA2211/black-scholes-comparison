"""Binomial CRR tree method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PriceResult


class BinomialCRR:
    """Binomial CRR tree wrapper."""

    def price(self, params: OptionParams, num_steps: int = 500) -> PriceResult:
        """CRR 1D in-place backward induction."""
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        time_step = maturity_years / num_steps
        up_factor = np.exp(volatility * np.sqrt(time_step))
        down_factor = 1.0 / up_factor

        discount_factor = np.exp(-risk_free_rate * time_step)
        prob_up = (np.exp(risk_free_rate * time_step) - down_factor) / (up_factor - down_factor)
        prob_down = 1.0 - prob_up

        # Terminal price grid
        terminal_underlyings = (
            underlying_price
            * (up_factor ** np.arange(num_steps, -1, -1))
            * (down_factor ** np.arange(0, num_steps + 1))
        )

        if params.option_type == "call":
            values = np.maximum(terminal_underlyings - strike_price, 0)
        else:
            values = np.maximum(strike_price - terminal_underlyings, 0)

        # Backward induction
        for step_idx in range(num_steps - 1, -1, -1):
            values = discount_factor * (prob_up * values[:-1] + prob_down * values[1:])
            # Early exercise (American) check
            if params.is_american:
                underlyings_at_step = (
                    underlying_price
                    * (up_factor ** np.arange(step_idx, -1, -1))
                    * (down_factor ** np.arange(0, step_idx + 1))
                )
                if params.option_type == "call":
                    exercise_values = np.maximum(underlyings_at_step - strike_price, 0)
                else:
                    exercise_values = np.maximum(strike_price - underlyings_at_step, 0)
                values = np.maximum(values, exercise_values)

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="binomial_crr",
            computed_price=float(values[0]),
            exec_seconds=exec_seconds,
            parameter_set={"num_steps": num_steps},
        )
