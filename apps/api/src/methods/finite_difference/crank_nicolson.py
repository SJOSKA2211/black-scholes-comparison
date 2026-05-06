"""Crank-Nicolson Finite Difference Method implementation."""

import time
from typing import Any

import numpy as np

from src.methods.base import NumericalMethod, OptionParams, OptionType, PriceResult


class CrankNicolson(NumericalMethod):
    """
    Crank-Nicolson FDM for European and American options.
    Uses Thomas algorithm for O(N) tridiagonal matrix inversion.
    """

    async def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        # Grid parameters
        num_time_steps = 1000
        num_space_steps = 200

        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        vol = params.volatility
        rate = params.risk_free_rate

        # Boundaries
        max_price = underlying * 3
        delta_time = maturity / num_time_steps

        # Grid initialization
        grid = np.linspace(0, max_price, num_space_steps + 1)
        if params.option_type == OptionType.CALL:
            values = np.maximum(grid - strike, 0)
        else:
            values = np.maximum(strike - grid, 0)

        # Matrix coefficients
        indices = np.arange(1, num_space_steps)
        alpha = 0.25 * delta_time * (vol**2 * indices**2 - rate * indices)
        beta = -0.5 * delta_time * (vol**2 * indices**2 + rate)
        gamma = 0.25 * delta_time * (vol**2 * indices**2 + rate * indices)

        # Explicit part matrix (M1) and Implicit part matrix (M2)
        # M2 * V_new = M1 * V_old
        # Diagonal (d), Lower diagonal (l), Upper diagonal (u) for M2
        d_m2 = 1 - beta
        l_m2 = -alpha
        u_m2 = -gamma

        for _ in range(num_time_steps):
            # RHS: M1 * V_old
            rhs = np.zeros(num_space_steps + 1)
            rhs[1:num_space_steps] = (
                alpha * values[0 : num_space_steps - 1]
                + (1 + beta) * values[1:num_space_steps]
                + gamma * values[2 : num_space_steps + 1]
            )

            # Boundary conditions (European)
            if params.option_type == OptionType.CALL:
                rhs[0] = 0
                rhs[num_space_steps] = max_price - strike * np.exp(-rate * delta_time)
            else:
                rhs[0] = strike * np.exp(-rate * delta_time)
                rhs[num_space_steps] = 0

            # Thomas Algorithm to solve M2 * values = rhs
            values = self._thomas_algorithm(l_m2, d_m2, u_m2, rhs[1:num_space_steps])

            # Boundary expansion
            if params.option_type == OptionType.CALL:
                values = np.concatenate([[0], values, [max_price - strike]])
            else:
                values = np.concatenate([[strike], values, [0]])

            if params.is_american:
                if params.option_type == OptionType.CALL:
                    values = np.maximum(values, grid - strike)
                else:
                    values = np.maximum(values, strike - grid)

        # Interpolate price at current underlying
        final_price = np.interp(underlying, grid, values)

        exec_time = time.perf_counter() - start_time
        return PriceResult(price=float(final_price), exec_seconds=exec_time)

    def _thomas_algorithm(
        self,
        lower: np.ndarray[Any, np.dtype[np.float64]],
        diag: np.ndarray[Any, np.dtype[np.float64]],
        upper: np.ndarray[Any, np.dtype[np.float64]],
        rhs: np.ndarray[Any, np.dtype[np.float64]],
    ) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Solves tridiagonal system Ax = b in O(N) time."""
        n = len(rhs)
        c_star = np.zeros(n)
        d_star = np.zeros(n)

        c_star[0] = upper[0] / diag[0]
        d_star[0] = rhs[0] / diag[0]

        for i in range(1, n):
            m = diag[i] - lower[i] * c_star[i - 1]
            if i < n - 1:
                c_star[i] = upper[i] / m
            d_star[i] = (rhs[i] - lower[i] * d_star[i - 1]) / m

        x = np.zeros(n)
        x[-1] = d_star[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_star[i] - c_star[i] * x[i + 1]

        return x
