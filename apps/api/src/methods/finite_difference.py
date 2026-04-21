import time

import numpy as np

from src.exceptions import CFLViolationError
from src.methods.base import OptionParams, PriceResult


class FiniteDifferenceMethods:
    """Finite Difference Methods for option pricing."""

    def _thomas_algorithm(
        self,
        lower_diag: np.ndarray,
        main_diag: np.ndarray,
        upper_diag: np.ndarray,
        rhs: np.ndarray,
    ) -> np.ndarray:
        """
        Solves Ax = rhs where A is a tridiagonal matrix.
        O(n) complexity.
        """
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

    def explicit_fdm(
        self, params: OptionParams, num_spatial: int = 100, num_time: int = 1000
    ) -> PriceResult:
        start_time = time.time()
        strike_price = params.strike_price
        max_underlying = 4 * strike_price
        time_step = params.maturity_years / num_time
        spatial_step = max_underlying / num_spatial  # noqa: F841

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

                a_coeff = (
                    0.5
                    * time_step
                    * (vol_sq * space_idx**2 - risk_free_rate * space_idx)
                )
                b_coeff = 1 - time_step * (vol_sq * space_idx**2 + risk_free_rate)
                c_coeff = (
                    0.5
                    * time_step
                    * (vol_sq * space_idx**2 + risk_free_rate * space_idx)
                )

                grid[time_idx + 1, space_idx] = (
                    a_coeff * grid[time_idx, space_idx - 1]
                    + b_coeff * grid[time_idx, space_idx]
                    + c_coeff * grid[time_idx, space_idx + 1]
                )

            # Boundary conditions
            if params.option_type == "call":
                grid[time_idx + 1, 0] = 0
                grid[time_idx + 1, num_spatial] = (
                    max_underlying
                    - strike_price
                    * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
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

    def implicit_fdm(
        self, params: OptionParams, num_spatial: int = 100, num_time: int = 100
    ) -> PriceResult:
        start_time = time.time()
        strike_price = params.strike_price
        max_underlying = 4 * strike_price
        time_step = params.maturity_years / num_time
        spatial_step = max_underlying / num_spatial  # noqa: F841
        underlying_values = np.linspace(0, max_underlying, num_spatial + 1)

        # Payoff at maturity
        if params.option_type == "call":
            values = np.maximum(underlying_values - strike_price, 0)
        else:
            values = np.maximum(strike_price - underlying_values, 0)

        vol_sq = params.volatility**2
        risk_free_rate = params.risk_free_rate

        # Tridiagonal matrix coefficients
        space_indices = np.arange(1, num_spatial)
        lower_diag = (
            -0.5
            * time_step
            * (vol_sq * space_indices**2 - risk_free_rate * space_indices)
        )
        main_diag = 1 + time_step * (vol_sq * space_indices**2 + risk_free_rate)
        upper_diag = (
            -0.5
            * time_step
            * (vol_sq * space_indices**2 + risk_free_rate * space_indices)
        )

        for time_idx in range(num_time):
            rhs_values = values[1:-1].copy()
            # Boundary adjustments
            if params.option_type == "call":
                rhs_values[-1] -= upper_diag[-1] * (
                    max_underlying
                    - strike_price
                    * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
                )
            else:
                rhs_values[0] -= lower_diag[0] * (
                    strike_price * np.exp(-risk_free_rate * (time_idx + 1) * time_step)
                )

            values[1:-1] = self._thomas_algorithm(
                lower_diag, main_diag, upper_diag, rhs_values
            )

            # Boundary conditions
            if params.option_type == "call":
                values[0] = 0
                values[num_spatial] = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
            else:
                values[0] = strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                values[num_spatial] = 0

        price = np.interp(params.underlying_price, underlying_values, values)
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="implicit_fdm",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_spatial": num_spatial, "num_time": num_time},
        )

    def crank_nicolson(
        self, params: OptionParams, num_spatial: int = 100, num_time: int = 100
    ) -> PriceResult:
        start_time = time.time()
        strike_price = params.strike_price
        max_underlying = 4 * strike_price
        time_step = params.maturity_years / num_time
        spatial_step = max_underlying / num_spatial  # noqa: F841
        underlying_values = np.linspace(0, max_underlying, num_spatial + 1)

        if params.option_type == "call":
            values = np.maximum(underlying_values - strike_price, 0)
        else:
            values = np.maximum(strike_price - underlying_values, 0)

        vol_sq = params.volatility**2
        risk_free_rate = params.risk_free_rate
        space_indices = np.arange(1, num_spatial)

        alpha = (
            0.25
            * time_step
            * (vol_sq * space_indices**2 - risk_free_rate * space_indices)
        )
        beta = 0.5 * time_step * (vol_sq * space_indices**2 + risk_free_rate)
        gamma = (
            0.25
            * time_step
            * (vol_sq * space_indices**2 + risk_free_rate * space_indices)
        )

        lower_diag = -alpha
        main_diag = 1 + beta
        upper_diag = -gamma

        for time_idx in range(num_time):
            # Explicit part for RHS
            rhs_values = (
                alpha * values[:-2] + (1 - beta) * values[1:-1] + gamma * values[2:]
            )

            # Boundary adjustments
            if params.option_type == "call":
                bound_prev = max_underlying - strike_price * np.exp(
                    -risk_free_rate * time_idx * time_step
                )
                bound_curr = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                rhs_values[-1] += gamma[-1] * (bound_curr + bound_prev)
            else:
                bound_prev = strike_price * np.exp(
                    -risk_free_rate * time_idx * time_step
                )
                bound_curr = strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                rhs_values[0] += alpha[0] * (bound_curr + bound_prev)

            values[1:-1] = self._thomas_algorithm(
                lower_diag, main_diag, upper_diag, rhs_values
            )

            # Update boundaries
            if params.option_type == "call":
                values[0] = 0
                values[num_spatial] = max_underlying - strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
            else:
                values[0] = strike_price * np.exp(
                    -risk_free_rate * (time_idx + 1) * time_step
                )
                values[num_spatial] = 0

        price = np.interp(params.underlying_price, underlying_values, values)
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="crank_nicolson",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_spatial": num_spatial, "num_time": num_time},
        )
