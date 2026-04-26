"""Explicit Finite Difference Method (FTCS)."""

from __future__ import annotations

import time

import numpy as np

from src.exceptions import CFLViolationError
from src.methods.base import MethodType, OptionParams, PriceResult


class ExplicitFDM:
    """
    Explicit Finite Difference Method (Forward-Time Central-Space).
    Stability condition: dt / dS^2 * volatility^2 * underlying^2 <= 0.5.
    """

    method_type: MethodType = "explicit_fdm"

    def __init__(self, num_time_steps: int = 1000, num_price_steps: int = 100) -> None:
        self.num_time_steps = num_time_steps
        self.num_price_steps = num_price_steps

    def price(
        self, params: OptionParams, num_spatial: int | None = None, num_time: int | None = None
    ) -> PriceResult:
        """Compute the option price and Greeks using Explicit FDM."""
        start_time = time.time()

        spatial_steps = num_spatial if num_spatial is not None else self.num_price_steps
        time_steps = num_time if num_time is not None else self.num_time_steps

        def _solve(p: OptionParams, local_nx: int, local_nt: int) -> tuple[float, float, float]:
            max_price = p.underlying_price * 3.0
            spatial_step_size = max_price / local_nx
            time_step_size = p.maturity_years / local_nt

            # CFL Stability Check
            stability_limit = 0.5 * spatial_step_size**2 / ((p.volatility**2) * (max_price**2))
            if time_step_size > stability_limit:
                raise CFLViolationError(cfl_actual=float(time_step_size), cfl_bound=float(stability_limit))

            spatial_values = np.linspace(0, max_price, local_nx + 1)
            option_values = (
                np.maximum(spatial_values - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - spatial_values, 0)
            )

            # Pre-calculate constants for vectorization
            indices = np.arange(1, local_nx)
            spatial_inner_values = spatial_values[indices]
            vol_sq = p.volatility**2
            risk_free = p.risk_free_rate

            for _ in range(local_nt):
                # Central difference for delta and gamma (vectorized)
                delta_fd = (option_values[indices + 1] - option_values[indices - 1]) / (2 * spatial_step_size)
                gamma_fd = (option_values[indices + 1] - 2 * option_values[indices] + option_values[indices - 1]) / (spatial_step_size**2)

                drift = risk_free * spatial_inner_values * delta_fd
                diffusion = 0.5 * vol_sq * (spatial_inner_values**2) * gamma_fd

                # Update inner grid points
                option_values[1:local_nx] = option_values[1:local_nx] + time_step_size * (diffusion + drift - risk_free * option_values[1:local_nx])

                # Boundary conditions
                if p.option_type == "call":
                    option_values[0] = 0
                    option_values[local_nx] = max_price - p.strike_price * np.exp(-risk_free * time_step_size * (_ + 1))
                else:
                    option_values[0] = p.strike_price * np.exp(-risk_free * time_step_size * (_ + 1))
                    option_values[local_nx] = 0

            idx = int(np.searchsorted(spatial_values, p.underlying_price))
            idx = max(1, min(idx, local_nx - 1))
            price = float(np.interp(p.underlying_price, spatial_values, option_values))
            delta = float((option_values[idx] - option_values[idx - 1]) / spatial_step_size)
            gamma = float((option_values[idx + 1] - 2 * option_values[idx] + option_values[idx - 1]) / (spatial_step_size**2))
            return price, delta, gamma

        price_main, delta, gamma = _solve(params, spatial_steps, time_steps)

        # Bumping for sensitivities
        def get_p(p_mod: OptionParams) -> float:
            try:
                res, _, _ = _solve(p_mod, spatial_steps, time_steps)
                return res
            except CFLViolationError:
                return price_main
        
        # ... rest of sensitivities ...
        h_v, h_r, h_t = 0.01, 0.01, 1 / 365.0
        vega = (
            get_p(params.model_copy(update={"volatility": params.volatility + h_v})) - price_main
        ) / h_v
        rho = (
            get_p(params.model_copy(update={"risk_free_rate": params.risk_free_rate + h_r}))
            - price_main
        ) / h_r
        theta = (
            -(
                price_main
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

        return PriceResult(
            method_type=self.method_type,
            computed_price=price_main,
            exec_seconds=time.time() - start_time,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            parameter_set={"spatial_steps": spatial_steps, "time_steps": time_steps},
        )
