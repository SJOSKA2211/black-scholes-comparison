"""Implicit Finite Difference Method (BTCS) with Thomas Algorithm."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class ImplicitFDM:
    """
    Implicit Finite Difference Method (Backward-Time Central-Space).
    Uses Thomas Algorithm (TDMA) for O(n) tridiagonal system resolution.
    """

    method_type: MethodType = "implicit_fdm"

    def __init__(self, num_time_steps: int = 100, num_price_steps: int = 100) -> None:
        self.num_time_steps = num_time_steps
        self.num_price_steps = num_price_steps

    @staticmethod
    def thomas_algorithm(
        lower: np.ndarray[Any, Any],
        main: np.ndarray[Any, Any],
        upper: np.ndarray[Any, Any],
        rhs: np.ndarray[Any, Any],
    ) -> np.ndarray[Any, Any]:
        """
        Solve a tridiagonal system Ax = rhs.
        lower: lower diagonal [1:num_elements]
        main: main diagonal [0:num_elements]
        upper: upper diagonal [0:num_elements-1]
        rhs: right hand side [0:num_elements]
        """
        num_elements = len(rhs)
        upper_prime = np.zeros(num_elements - 1)
        rhs_prime = np.zeros(num_elements)

        upper_prime[0] = upper[0] / main[0]
        rhs_prime[0] = rhs[0] / main[0]

        for index in range(1, num_elements - 1):
            denominator = main[index] - lower[index - 1] * upper_prime[index - 1]
            upper_prime[index] = upper[index] / denominator
            rhs_prime[index] = (rhs[index] - lower[index - 1] * rhs_prime[index - 1]) / denominator

        rhs_prime[num_elements - 1] = (
            rhs[num_elements - 1] - lower[num_elements - 2] * rhs_prime[num_elements - 2]
        ) / (main[num_elements - 1] - lower[num_elements - 2] * upper_prime[num_elements - 2])

        solution = np.zeros(num_elements)
        solution[num_elements - 1] = rhs_prime[num_elements - 1]
        for index in range(num_elements - 2, -1, -1):
            solution[index] = rhs_prime[index] - upper_prime[index] * solution[index + 1]

        return solution

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using Implicit FDM."""
        start_time = time.time()

        def _solve(p: OptionParams) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], float]:
            max_p = p.strike_price * 3.0
            dt = p.maturity_years / self.num_time_steps
            ds = max_p / self.num_price_steps
            v_prices = np.linspace(0, max_p, self.num_price_steps + 1)
            v_grid = (
                np.maximum(v_prices - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - v_prices, 0)
            )

            indices = np.arange(1, self.num_price_steps)
            vol_sq = p.volatility**2
            r = p.risk_free_rate
            lower = -0.5 * dt * (vol_sq * (indices[1:] ** 2) - r * indices[1:])
            main = 1 + dt * (vol_sq * (indices**2) + r)
            upper = -0.5 * dt * (vol_sq * (indices[:-1] ** 2) + r * indices[:-1])

            for step in range(self.num_time_steps):
                rhs = v_grid[1 : self.num_price_steps]
                if p.option_type == "call":
                    rhs[-1] -= upper[-1] * (max_p - p.strike_price * np.exp(-r * dt * step))
                else:
                    rhs[0] -= lower[0] * (p.strike_price * np.exp(-r * dt * step))

                v_grid[1 : self.num_price_steps] = self.thomas_algorithm(lower, main, upper, rhs)
                if p.option_type == "call":
                    v_grid[0], v_grid[-1] = 0, max_p - p.strike_price * np.exp(-r * dt * (step + 1))
                else:
                    v_grid[0], v_grid[-1] = p.strike_price * np.exp(-r * dt * (step + 1)), 0

            return v_prices, v_grid, ds

        prices, grid, delta_s = _solve(params)
        computed_price = float(np.interp(params.underlying_price, prices, grid))

        idx = int(np.searchsorted(prices, params.underlying_price))
        idx = min(idx, self.num_price_steps)
        if 0 < idx < self.num_price_steps:
            delta = (grid[idx + 1] - grid[idx - 1]) / (2 * delta_s)
            gamma = (grid[idx + 1] - 2 * grid[idx] + grid[idx - 1]) / (delta_s**2)
        else:
            delta = (
                (grid[idx + 1] - grid[idx]) / delta_s
                if idx < self.num_price_steps
                else (grid[idx] - grid[idx - 1]) / delta_s
            )
            gamma = 0.0

        h_v, h_t, h_r = 0.01, 1 / 365.0, 0.01

        def get_p(p: OptionParams) -> float:
            _, g, _ = _solve(p)
            return float(np.interp(p.underlying_price, prices, g))

        vega = (
            get_p(params.model_copy(update={"volatility": params.volatility + h_v}))
            - computed_price
        ) / h_v
        theta = (
            -(
                computed_price
                - get_p(
                    params.model_copy(
                        update={"maturity_years": max(0.0001, params.maturity_years - h_t)}
                    )
                )
            )
            / h_t
            if params.maturity_years > h_t
            else 0.0
        )
        rho = (
            get_p(params.model_copy(update={"risk_free_rate": params.risk_free_rate + h_r}))
            - computed_price
        ) / h_r

        return PriceResult(
            method_type=self.method_type,
            computed_price=computed_price,
            exec_seconds=time.time() - start_time,
            delta=float(delta),
            gamma=float(gamma),
            theta=float(theta),
            vega=float(vega),
            rho=float(rho),
            parameter_set={
                "num_time_steps": self.num_time_steps,
                "num_price_steps": self.num_price_steps,
            },
        )
