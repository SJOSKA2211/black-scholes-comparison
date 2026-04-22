"""Crank-Nicolson Finite Difference Method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PriceResult
from src.methods.finite_difference.implicit import _thomas_algorithm


class CrankNicolsonFDM:
    """Crank-Nicolson Finite Difference Method wrapper."""

    def price(
        self, params: OptionParams, num_spatial: int = 100, num_time: int = 100
    ) -> PriceResult:
        """Crank-Nicolson FDM solver."""
        start_time = time.time()
        strike_price = params.strike_price
        max_underlying = 4 * strike_price
        time_step = params.maturity_years / num_time
        underlying_values = np.linspace(0, max_underlying, num_spatial + 1)

        if params.option_type == "call":
            values = np.maximum(underlying_values - strike_price, 0)
        else:
            values = np.maximum(strike_price - underlying_values, 0)

        vol_sq = params.volatility**2
        risk_free_rate = params.risk_free_rate
        space_indices = np.arange(1, num_spatial)

        alpha = 0.25 * time_step * (vol_sq * space_indices**2 - risk_free_rate * space_indices)
        beta = 0.5 * time_step * (vol_sq * space_indices**2 + risk_free_rate)
        gamma = 0.25 * time_step * (vol_sq * space_indices**2 + risk_free_rate * space_indices)

        lower_diag = -alpha
        main_diag = 1 + beta
        upper_diag = -gamma

        for time_idx in range(num_time):
            rhs_values = alpha * values[:-2] + (1 - beta) * values[1:-1] + gamma * values[2:]

            if params.option_type == "call":
                bound_prev = max_underlying - strike_price * np.exp(
                    -risk_free_rate * time_idx * time_step
                )
                bound_curr = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                rhs_values[-1] += gamma[-1] * (bound_curr + bound_prev)
            else:
                bound_prev = strike_price * np.exp(-risk_free_rate * time_idx * time_step)
                bound_curr = strike_price * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
                rhs_values[0] += alpha[0] * (bound_curr + bound_prev)

            values[1:-1] = _thomas_algorithm(lower_diag, main_diag, upper_diag, rhs_values)

            if params.option_type == "call":
                values[0] = 0
                values[num_spatial] = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
            else:
                values[0] = strike_price * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
                values[num_spatial] = 0

        price = np.interp(params.underlying_price, underlying_values, values)
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="crank_nicolson",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_spatial": num_spatial, "num_time": num_time},
        )
