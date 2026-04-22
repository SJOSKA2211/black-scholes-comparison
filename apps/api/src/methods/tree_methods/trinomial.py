"""Trinomial tree method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PriceResult


def price_trinomial(params: OptionParams, num_steps: int = 500) -> PriceResult:
    """Boyle (1988) Three-branch lattice Trinomial tree solver."""
    start_time = time.time()

    underlying_price = params.underlying_price
    strike_price = params.strike_price
    maturity_years = params.maturity_years
    risk_free_rate = params.risk_free_rate
    volatility = params.volatility

    time_step = maturity_years / num_steps
    up_factor = np.exp(volatility * np.sqrt(2 * time_step))
    discount_factor = np.exp(-risk_free_rate * time_step)

    # Boyle (1986) probabilities
    prob_up = (
        (np.exp(risk_free_rate * time_step / 2) - np.exp(-volatility * np.sqrt(time_step / 2)))
        / (
            np.exp(volatility * np.sqrt(time_step / 2))
            - np.exp(-volatility * np.sqrt(time_step / 2))
        )
    ) ** 2
    prob_down = (
        (np.exp(volatility * np.sqrt(time_step / 2)) - np.exp(risk_free_rate * time_step / 2))
        / (
            np.exp(volatility * np.sqrt(time_step / 2))
            - np.exp(-volatility * np.sqrt(time_step / 2))
        )
    ) ** 2
    prob_mid = 1.0 - prob_up - prob_down

    # Grid sizes
    terminal_underlyings = underlying_price * (
        up_factor ** np.arange(num_steps, -num_steps - 1, -1)
    )

    if params.option_type == "call":
        values = np.maximum(terminal_underlyings - strike_price, 0)
    else:
        values = np.maximum(strike_price - terminal_underlyings, 0)

    for step_idx in range(num_steps - 1, -1, -1):
        values = discount_factor * (
            prob_up * values[:-2] + prob_mid * values[1:-1] + prob_down * values[2:]
        )
        if params.is_american:
            underlyings_at_step = underlying_price * (
                up_factor ** np.arange(step_idx, -step_idx - 1, -1)
            )
            if params.option_type == "call":
                exercise_values = np.maximum(underlyings_at_step - strike_price, 0)
            else:
                exercise_values = np.maximum(strike_price - underlyings_at_step, 0)
            values = np.maximum(values, exercise_values)

    exec_seconds = time.time() - start_time
    return PriceResult(
        method_type="trinomial",
        computed_price=float(values[0]),
        exec_seconds=exec_seconds,
        parameter_set={"num_steps": num_steps},
    )
