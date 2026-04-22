"""Explicit Finite Difference Method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.exceptions import CFLViolationError
from src.methods.base import OptionParams, PriceResult


class ExplicitFDM:
    """Explicit Finite Difference Method wrapper."""

    def price(
        self, params: OptionParams, num_spatial: int = 100, num_time: int = 1000
    ) -> PriceResult:
        """FTCS Explicit FDM solver."""
        start_time = time.time()
        strike_price = params.strike_price
        max_underlying = 4 * strike_price
        time_step = params.maturity_years / num_time
        spatial_step = max_underlying / num_spatial

        volatility = params.volatility
        risk_free_rate = params.risk_free_rate

        # CFL Condition check
        cfl_threshold = 0.5 * (spatial_step**2) / (volatility**2 * max_underlying**2)
        if time_step > cfl_threshold:
            suggested_num_time = int(params.maturity_years / (0.9 * cfl_threshold)) + 1
            raise CFLViolationError(
                f"CFL condition violated. dt ({time_step:.6f}) > threshold ({cfl_threshold:.6f}).",
                suggested_dt=params.maturity_years / suggested_num_time,
            )

        underlying_values = np.linspace(0, max_underlying, num_spatial + 1)
        grid = np.zeros((num_time + 1, num_spatial + 1))

        # Terminal condition
        if params.option_type == "call":
            grid[0, :] = np.maximum(underlying_values - strike_price, 0)
        else:
            grid[0, :] = np.maximum(strike_price - underlying_values, 0)

        # Time stepping
        for time_idx in range(0, num_time):
            for space_idx in range(1, num_spatial):
                vol_sq = volatility**2

                a_coeff = 0.5 * time_step * (vol_sq * space_idx**2 - risk_free_rate * space_idx)
                b_coeff = 1 - time_step * (vol_sq * space_idx**2 + risk_free_rate)
                c_coeff = 0.5 * time_step * (vol_sq * space_idx**2 + risk_free_rate * space_idx)

                grid[time_idx + 1, space_idx] = (
                    a_coeff * grid[time_idx, space_idx - 1]
                    + b_coeff * grid[time_idx, space_idx]
                    + c_coeff * grid[time_idx, space_idx + 1]
                )

            # Boundary conditions
            if params.option_type == "call":
                grid[time_idx + 1, 0] = 0
                grid[time_idx + 1, num_spatial] = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
            else:
                grid[time_idx + 1, 0] = strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                grid[time_idx + 1, num_spatial] = 0

        price = np.interp(params.underlying_price, underlying_values, grid[num_time, :])
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="explicit_fdm",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_spatial": num_spatial, "num_time": num_time},
        )
