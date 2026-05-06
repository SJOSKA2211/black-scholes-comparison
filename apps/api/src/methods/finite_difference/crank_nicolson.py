"""Crank-Nicolson finite difference method implementation."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PricingMethod, PricingResult


class CrankNicolson(PricingMethod):
    """
    Crank-Nicolson FDM implementation (theta=0.5).
    Uses Thomas Algorithm for O(M) tridiagonal solving.
    Uses Projected Successive Over-Relaxation (PSOR) for American options.
    """

    async def price(self, params: OptionParams) -> PricingResult:
        """Compute the option price using Crank-Nicolson FDM."""
        start_time = time.perf_counter()

        # Grid configuration
        num_space_steps = 200
        num_time_steps = 100

        max_price = params.strike_price * 3.0
        time_step = params.maturity_years / num_time_steps

        prices = np.linspace(0, max_price, num_space_steps + 1)
        grid = self._initialize_payoff(prices, params)

        # Setup Tridiagonal Matrices (theta = 0.5)
        indices = np.arange(1, num_space_steps)
        vol_sq = params.volatility**2
        rate = params.risk_free_rate

        # Coefficients
        alpha = 0.25 * time_step * (vol_sq * (indices**2) - rate * indices)
        beta = -0.5 * time_step * (vol_sq * (indices**2) + rate)
        gamma = 0.25 * time_step * (vol_sq * (indices**2) + rate * indices)

        # LHS Matrix diagonals
        lower_lhs = -alpha
        main_lhs = 1.0 - beta
        upper_lhs = -gamma

        # RHS Matrix diagonals
        lower_rhs = alpha
        main_rhs = 1.0 + beta
        upper_rhs = gamma

        # Time Stepping
        for _ in range(num_time_steps):
            # Compute RHS vector
            rhs = lower_rhs * grid[:-2] + main_rhs * grid[1:-1] + upper_rhs * grid[2:]

            if params.is_american:
                grid[1:-1] = self._solve_psor(
                    lower_lhs, main_lhs, upper_lhs, rhs, grid[1:-1], params, prices[1:-1]
                )
            else:
                grid[1:-1] = self._solve_thomas(lower_lhs, main_lhs, upper_lhs, rhs)

        # Interpolate result
        final_price = np.interp(params.underlying_price, prices, grid)

        return PricingResult(
            price=float(final_price),
            exec_seconds=time.perf_counter() - start_time,
            metadata={"num_space_steps": num_space_steps, "num_time_steps": num_time_steps},
        )

    def _initialize_payoff(self, prices: np.ndarray, params: OptionParams) -> np.ndarray:
        """Initialize payoff grid at maturity."""
        if params.is_call:
            return np.maximum(prices - params.strike_price, 0.0)
        return np.maximum(params.strike_price - prices, 0.0)

    def _solve_thomas(
        self, lower: np.ndarray, main: np.ndarray, upper: np.ndarray, rhs: np.ndarray
    ) -> np.ndarray:
        """Thomas Algorithm for tridiagonal systems."""
        num_elements = len(rhs)
        cp = np.zeros(num_elements)
        dp = np.zeros(num_elements)

        cp[0] = upper[0] / main[0]
        dp[0] = rhs[0] / main[0]

        for i in range(1, num_elements):
            denominator = main[i] - lower[i - 1] * cp[i - 1]
            if i < num_elements - 1:
                cp[i] = upper[i] / denominator
            dp[i] = (rhs[i] - lower[i - 1] * dp[i - 1]) / denominator

        solution = np.zeros(num_elements)
        solution[-1] = dp[-1]
        for i in range(num_elements - 2, -1, -1):
            solution[i] = dp[i] - cp[i] * solution[i + 1]

        return solution

    def _solve_psor(
        self,
        lower: np.ndarray,
        main: np.ndarray,
        upper: np.ndarray,
        rhs: np.ndarray,
        initial_guess: np.ndarray,
        params: OptionParams,
        prices: np.ndarray,
    ) -> np.ndarray:
        """Projected Successive Over-Relaxation for American options."""
        num_elements = len(rhs)
        solution = initial_guess.copy()
        omega = 1.2
        max_iter = 100
        tol = 1e-6

        if params.is_call:
            intrinsic = np.maximum(prices - params.strike_price, 0.0)
        else:
            intrinsic = np.maximum(params.strike_price - prices, 0.0)

        for _ in range(max_iter):
            old_sol = solution.copy()
            for i in range(num_elements):
                sigma_val = 0.0
                if i > 0:
                    sigma_val += lower[i - 1] * solution[i - 1]
                if i < num_elements - 1:
                    sigma_val += upper[i] * solution[i + 1]

                new_val = (rhs[i] - sigma_val) / main[i]
                solution[i] = np.maximum(
                    intrinsic[i], (1.0 - omega) * solution[i] + omega * new_val
                )

            if np.linalg.norm(solution - old_sol) < tol:
                break
        return solution
