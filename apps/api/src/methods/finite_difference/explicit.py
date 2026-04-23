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

        nx = num_spatial if num_spatial is not None else self.num_price_steps
        nt = num_time if num_time is not None else self.num_time_steps

        def _solve(p: OptionParams, local_nx: int, local_nt: int) -> tuple[float, float, float]:
            max_s = p.underlying_price * 3.0
            ds = max_s / local_nx
            dt = p.maturity_years / local_nt

            # CFL Stability Check
            stability_limit = 0.5 * ds**2 / ((p.volatility**2) * (max_s**2))
            if dt > stability_limit:
                # suggested_nt = p.maturity_years / stability_limit
                raise CFLViolationError(cfl_actual=float(dt), cfl_bound=float(stability_limit))

            s_vals = np.linspace(0, max_s, local_nx + 1)
            v = (
                np.maximum(s_vals - p.strike_price, 0)
                if p.option_type == "call"
                else np.maximum(p.strike_price - s_vals, 0)
            )

            # Pre-calculate constants for vectorization
            indices = np.arange(1, local_nx)
            s_j = s_vals[indices]
            vol_sq = p.volatility**2
            r = p.risk_free_rate

            for _ in range(local_nt):
                # Central difference for delta and gamma (vectorized)
                delta_fd = (v[indices + 1] - v[indices - 1]) / (2 * ds)
                gamma_fd = (v[indices + 1] - 2 * v[indices] + v[indices - 1]) / (ds**2)

                drift = r * s_j * delta_fd
                diffusion = 0.5 * vol_sq * (s_j**2) * gamma_fd

                # Update inner grid points
                v[1:local_nx] = v[1:local_nx] + dt * (diffusion + drift - r * v[1:local_nx])

                # Boundary conditions
                if p.option_type == "call":
                    v[0] = 0
                    v[local_nx] = max_s - p.strike_price * np.exp(-r * dt * (_ + 1))
                else:
                    v[0] = p.strike_price * np.exp(-r * dt * (_ + 1))
                    v[local_nx] = 0

            idx = np.searchsorted(s_vals, p.underlying_price)
            price = float(np.interp(p.underlying_price, s_vals, v))
            delta = float((v[idx] - v[idx - 1]) / ds)
            gamma = float((v[idx + 1] - 2 * v[idx] + v[idx - 1]) / (ds**2))
            return price, delta, gamma

        price_main, delta, gamma = _solve(params, nx, nt)

        # Bumping for sensitivities
        def get_p(p_mod: OptionParams) -> float:
            try:
                res, _, _ = _solve(p_mod, nx, nt)
                return res
            except CFLViolationError:
                return price_main

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
            parameter_set={"nx": nx, "nt": nt},
        )
