"""Crank-Nicolson Finite Difference Method (Theta=0.5)."""

from __future__ import annotations

import time
from typing import Any

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

        def _solve(p: OptionParams) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], float]:
            max_price = p.strike_price * 3.0
            time_step_size = p.maturity_years / self.num_time_steps
            spatial_step_size = max_price / self.num_price_steps
            spatial_grid_prices = np.linspace(0, max_price, self.num_price_steps + 1)
            option_value_grid = (
                np.maximum(spatial_grid_prices - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - spatial_grid_prices, 0)
            )

            indices = np.arange(1, self.num_price_steps)
            vol_sq = p.volatility**2
            risk_free_rate = p.risk_free_rate
            coeff_lower = 0.25 * time_step_size * (vol_sq * (indices**2) - risk_free_rate * indices)
            coeff_main = -0.5 * time_step_size * (vol_sq * (indices**2) + risk_free_rate)
            coeff_upper = 0.25 * time_step_size * (vol_sq * (indices**2) + risk_free_rate * indices)

            l_lhs, m_lhs, u_lhs = -coeff_lower[1:], 1 - coeff_main, -coeff_upper[:-1]

            for step in range(self.num_time_steps):
                rhs = (
                    coeff_lower * option_value_grid[:-2]
                    + (1 + coeff_main) * option_value_grid[1:-1]
                    + coeff_upper * option_value_grid[2:]
                )
                if p.option_type == "call":
                    rhs[-1] += coeff_upper[-1] * (
                        max_price - p.strike_price * np.exp(-risk_free_rate * time_step_size * step)
                    )
                else:
                    rhs[0] += coeff_lower[0] * (
                        p.strike_price * np.exp(-risk_free_rate * time_step_size * step)
                    )

                option_value_grid[1 : self.num_price_steps] = ImplicitFDM.thomas_algorithm(
                    l_lhs, m_lhs, u_lhs, rhs
                )
                if p.option_type == "call":
                    option_value_grid[0], option_value_grid[-1] = (
                        0,
                        max_price
                        - p.strike_price * np.exp(-risk_free_rate * time_step_size * (step + 1)),
                    )
                else:
                    option_value_grid[0], option_value_grid[-1] = (
                        p.strike_price * np.exp(-risk_free_rate * time_step_size * (step + 1)),
                        0,
                    )

            return spatial_grid_prices, option_value_grid, spatial_step_size

        prices, grid, spatial_step_size = _solve(params)
        computed_price = float(np.interp(params.underlying_price, prices, grid))

        target_index = int(np.searchsorted(prices, params.underlying_price))
        target_index = min(target_index, self.num_price_steps)
        if 0 < target_index < self.num_price_steps:
            delta = (grid[target_index + 1] - grid[target_index - 1]) / (2 * spatial_step_size)
            gamma = (grid[target_index + 1] - 2 * grid[target_index] + grid[target_index - 1]) / (
                spatial_step_size**2
            )
        else:
            delta = (
                (grid[target_index + 1] - grid[target_index]) / spatial_step_size
                if target_index < self.num_price_steps
                else (grid[target_index] - grid[target_index - 1]) / spatial_step_size
            )
            gamma = 0.0

        vol_bump, time_bump, rate_bump = 0.01, 1 / 365.0, 0.01

        def get_p(p: OptionParams) -> float:
            _, g, _ = _solve(p)
            return float(np.interp(p.underlying_price, prices, g))

        vega = (
            get_p(params.model_copy(update={"volatility": params.volatility + vol_bump}))
            - computed_price
        ) / vol_bump
        theta = (
            -(
                computed_price
                - get_p(
                    params.model_copy(
                        update={"maturity_years": max(0.0001, params.maturity_years - time_bump)}
                    )
                )
            )
            / time_bump
            if params.maturity_years > time_bump
            else 0.0
        )
        rho = (
            get_p(params.model_copy(update={"risk_free_rate": params.risk_free_rate + rate_bump}))
            - computed_price
        ) / rate_bump

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
