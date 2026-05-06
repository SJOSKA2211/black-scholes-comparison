"""Crank-Nicolson finite difference method implementation."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from src.methods.base import NumericalMethod, OptionParams, PriceResult


class CrankNicolson(NumericalMethod):
    """
    Crank-Nicolson FDM implementation (theta=0.5).
    Uses Thomas Algorithm for O(M) tridiagonal solving.
    Uses Projected Successive Over-Relaxation (PSOR) for American options.
    """

    def __init__(self, num_time_steps: int = 100, num_price_steps: int = 200):
        self.num_time_steps = num_time_steps
        self.num_space_steps = num_price_steps

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price using Crank-Nicolson FDM."""
        start_time = time.perf_counter()

        # Grid configuration
        num_space_steps = self.num_space_steps
        num_time_steps = self.num_time_steps

        max_price = params.strike_price * 3.0
        time_step = params.maturity_years / num_time_steps

        prices = np.linspace(0, max_price, num_space_steps + 1)
        grid = self._initialize_payoff(prices, params)

        # Setup Tridiagonal Matrices (theta = 0.5)
        indices = np.arange(1, num_space_steps)
        vol_sq = params.volatility**2
        rate = params.risk_free_rate

        # Coefficients for the PDE: dV/dt + 0.5*sigma^2*S^2*d2V/dS2 + r*S*dV/dS - r*V = 0
        alpha = 0.25 * time_step * (vol_sq * (indices**2) - rate * indices)
        beta = -0.5 * time_step * (vol_sq * (indices**2) + rate)
        gamma = 0.25 * time_step * (vol_sq * (indices**2) + rate * indices)

        # LHS Matrix diagonals (A * V_new = B * V_old)
        lower_lhs = -alpha
        main_lhs = 1.0 - beta
        upper_lhs = -gamma

        # RHS Matrix diagonals
        lower_rhs = alpha
        main_rhs = 1.0 + beta
        upper_rhs = gamma

        # Time Stepping (Backwards from T to 0)
        for t_idx in range(num_time_steps):
            t_remaining = (t_idx + 1) * time_step
            
            # 1. Update boundary conditions for the *next* step (V_new at boundaries)
            if params.is_call:
                boundary_low_new = 0.0
                boundary_high_new = max_price - params.strike_price * np.exp(-rate * t_remaining)
            else:
                boundary_low_new = params.strike_price * np.exp(-rate * t_remaining)
                boundary_high_new = 0.0

            # 2. Compute RHS vector for internal nodes
            rhs: np.ndarray[Any, np.dtype[np.float64]] = (
                lower_rhs * grid[:-2] + main_rhs * grid[1:-1] + upper_rhs * grid[2:]
            ).astype(np.float64)
            
            # Add boundary contributions to RHS
            rhs[0] += alpha[0] * boundary_low_new
            rhs[-1] += gamma[-1] * boundary_high_new

            # 3. Solve for internal nodes
            if params.is_american:
                grid[1:-1] = self._solve_psor(
                    lower_lhs, main_lhs, upper_lhs, rhs, grid[1:-1], params, prices[1:-1]
                )
            else:
                grid[1:-1] = self._solve_thomas(lower_lhs, main_lhs, upper_lhs, rhs)
            
            # 4. Apply boundaries to the grid
            grid[0] = boundary_low_new
            grid[-1] = boundary_high_new

        # Interpolate result
        final_price = np.interp(params.underlying_price, prices, grid)

        return PriceResult(
            method_type="crank_nicolson",
            computed_price=float(final_price),
            exec_seconds=time.perf_counter() - start_time,
            metadata={"num_space_steps": num_space_steps, "num_time_steps": num_time_steps},
        )

    def _initialize_payoff(
        self, prices: np.ndarray[Any, np.dtype[np.float64]], params: OptionParams
    ) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Initialize payoff grid at maturity."""
        if params.is_call:
            return np.maximum(prices - params.strike_price, 0.0)
        return np.maximum(params.strike_price - prices, 0.0)

    def _solve_thomas(
        self,
        lower: np.ndarray[Any, np.dtype[np.float64]],
        main: np.ndarray[Any, np.dtype[np.float64]],
        upper: np.ndarray[Any, np.dtype[np.float64]],
        rhs: np.ndarray[Any, np.dtype[np.float64]],
    ) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Thomas Algorithm for tridiagonal systems."""
        n = len(rhs)
        cp = np.zeros(n)
        dp = np.zeros(n)

        # Forward substitution
        cp[0] = upper[0] / main[0]
        dp[0] = rhs[0] / main[0]

        for i in range(1, n):
            # For row i, sub-diagonal is lower[i], main is main[i], super is upper[i]
            # (assuming lower[i] is the coeff of V_{i-1} in eq i)
            m = main[i] - lower[i] * cp[i - 1]
            if i < n - 1:
                cp[i] = upper[i] / m
            dp[i] = (rhs[i] - lower[i] * dp[i - 1]) / m

        # Backward substitution
        solution = np.zeros(n)
        solution[-1] = dp[-1]
        for i in range(n - 2, -1, -1):
            solution[i] = dp[i] - cp[i] * solution[i + 1]

        return solution

    def _solve_psor(
        self,
        lower: np.ndarray[Any, np.dtype[np.float64]],
        main: np.ndarray[Any, np.dtype[np.float64]],
        upper: np.ndarray[Any, np.dtype[np.float64]],
        rhs: np.ndarray[Any, np.dtype[np.float64]],
        initial_guess: np.ndarray[Any, np.dtype[np.float64]],
        params: OptionParams,
        prices: np.ndarray[Any, np.dtype[np.float64]],
    ) -> np.ndarray[Any, np.dtype[np.float64]]:
        """Projected Successive Over-Relaxation for American options."""
        n = len(rhs)
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
            for i in range(n):
                sigma_val = 0.0
                if i > 0:
                    sigma_val += lower[i] * solution[i - 1]
                if i < n - 1:
                    sigma_val += upper[i] * solution[i + 1]

                new_val = (rhs[i] - sigma_val) / main[i]
                solution[i] = np.maximum(
                    intrinsic[i], (1.0 - omega) * solution[i] + omega * new_val
                )

            if np.linalg.norm(solution - old_sol) < tol:
                break
        return solution
