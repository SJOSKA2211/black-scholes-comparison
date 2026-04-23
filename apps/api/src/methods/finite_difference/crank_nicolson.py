"""Crank-Nicolson Finite Difference Method (Theta=0.5)."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult
from src.methods.finite_difference.implicit import ImplicitFDM


class CrankNicolsonFDM:
    """
    Crank-Nicolson Finite Difference Method (Theta=0.5).
    Reuses ImplicitFDM.thomas_algorithm for efficiency.
    Provides second-order convergence in both time and space: O(dt^2 + dS^2).
    """

    method_type: MethodType = "crank_nicolson"

    def __init__(self, num_time_steps: int = 100, num_price_steps: int = 100) -> None:
        self.num_time_steps = num_time_steps
        self.num_price_steps = num_price_steps

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using Crank-Nicolson FDM."""
        start_time = time.time()

        def _solve(p: OptionParams) -> tuple[np.ndarray, np.ndarray, float]:
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
            a = 0.25 * dt * (vol_sq * (indices**2) - r * indices)
            b = -0.5 * dt * (vol_sq * (indices**2) + r)
            c = 0.25 * dt * (vol_sq * (indices**2) + r * indices)

            l_lhs, m_lhs, u_lhs = -a[1:], 1 - b, -c[:-1]

            for step in range(self.num_time_steps):
                rhs = a * v_grid[:-2] + (1 + b) * v_grid[1:-1] + c * v_grid[2:]
                if p.option_type == "call":
                    rhs[-1] += c[-1] * (max_p - p.strike_price * np.exp(-r * dt * step))
                else:
                    rhs[0] += a[0] * (p.strike_price * np.exp(-r * dt * step))

                v_grid[1 : self.num_price_steps] = ImplicitFDM.thomas_algorithm(
                    l_lhs, m_lhs, u_lhs, rhs
                )
                if p.option_type == "call":
                    v_grid[0], v_grid[-1] = 0, max_p - p.strike_price * np.exp(-r * dt * (step + 1))
                else:
                    v_grid[0], v_grid[-1] = p.strike_price * np.exp(-r * dt * (step + 1)), 0

            return v_prices, v_grid, ds

        prices, grid, delta_s = _solve(params)
        computed_price = float(np.interp(params.underlying_price, prices, grid))

        idx = np.searchsorted(prices, params.underlying_price)
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
