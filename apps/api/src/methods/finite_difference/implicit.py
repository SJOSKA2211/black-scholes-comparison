"""Implicit Finite Difference Method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PriceResult


def _thomas_algorithm(
    lower_diag: np.ndarray,
    main_diag: np.ndarray,
    upper_diag: np.ndarray,
    rhs: np.ndarray,
) -> np.ndarray:
    """Solves Ax = rhs where A is a tridiagonal matrix. O(n) complexity."""
    num_elements = len(rhs)
    c_prime = np.zeros(num_elements)
    d_prime = np.zeros(num_elements)

    c_prime[0] = upper_diag[0] / main_diag[0]
    d_prime[0] = rhs[0] / main_diag[0]

    for idx in range(1, num_elements):
        denominator = main_diag[idx] - lower_diag[idx] * c_prime[idx - 1]
        c_prime[idx] = upper_diag[idx] / denominator
        d_prime[idx] = (rhs[idx] - lower_diag[idx] * d_prime[idx - 1]) / denominator

    solution = np.zeros(num_elements)
    solution[-1] = d_prime[-1]
    for idx in range(num_elements - 2, -1, -1):
        solution[idx] = d_prime[idx] - c_prime[idx] * solution[idx + 1]

    return solution


def price_implicit_fdm(
    params: OptionParams, num_spatial: int = 100, num_time: int = 100
) -> PriceResult:
    """BTCS Implicit FDM solver."""
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

    lower_diag = -0.5 * time_step * (vol_sq * space_indices**2 - risk_free_rate * space_indices)
    main_diag = 1 + time_step * (vol_sq * space_indices**2 + risk_free_rate)
    upper_diag = -0.5 * time_step * (vol_sq * space_indices**2 + risk_free_rate * space_indices)

    for time_idx in range(num_time):
        rhs_values = values[1:-1].copy()
        if params.option_type == "call":
            rhs_values[-1] -= upper_diag[-1] * (
                max_underlying - strike_price * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
            )
        else:
            rhs_values[0] -= lower_diag[0] * (
                strike_price * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
            )

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
        method_type="implicit_fdm",
        computed_price=float(price),
        exec_seconds=exec_seconds,
        parameter_set={"num_spatial": num_spatial, "num_time": num_time},
    )
