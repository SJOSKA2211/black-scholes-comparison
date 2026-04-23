"""Binomial Cox-Ross-Rubinstein (CRR) tree method."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import MethodType, OptionParams, PriceResult


class BinomialCRR:
    """
    Binomial Tree method (Cox, Ross, and Rubinstein).
    Supports European and American options.
    Includes Richardson Extrapolation for faster convergence.
    """

    method_type: MethodType = "binomial_crr"

    def __init__(self, num_steps: int = 1000, use_richardson: bool = False) -> None:
        self.num_steps = num_steps
        self.use_richardson = use_richardson
        if use_richardson:
            self.method_type = "binomial_crr_richardson"

    def _tree_solve(self, params: OptionParams, steps: int) -> tuple[float, float, float]:
        """Internal CRR tree pricing engine. Returns (Price, Delta, Gamma)."""
        if steps < 1:
            return 0.0, 0.0, 0.0

        delta_t = params.maturity_years / steps
        up = np.exp(params.volatility * np.sqrt(delta_t))
        dn = 1.0 / up
        q_growth = np.exp(params.risk_free_rate * delta_t)
        p_u = (q_growth - dn) / (up - dn)
        p_d = 1.0 - p_u

        # Terminal payoffs
        indices = np.arange(steps + 1)
        st = params.underlying_price * (up**indices) * (dn ** (steps - indices))
        v = (
            np.maximum(st - params.strike_price, 0)
            if params.option_type == "call"
            else np.maximum(params.strike_price - st, 0)
        )

        # Backward induction
        v1 = np.zeros(2)
        v2 = np.zeros(3)
        for i in range(steps - 1, -1, -1):
            v = (p_u * v[1:] + p_d * v[:-1]) / q_growth
            if params.is_american:
                si = (
                    params.underlying_price
                    * (up ** np.arange(i + 1))
                    * (dn ** (i - np.arange(i + 1)))
                )
                v = np.maximum(
                    v,
                    (
                        si - params.strike_price
                        if params.option_type == "call"
                        else params.strike_price - si
                    ),
                )

            # Extract Delta/Gamma at step 1 and 2
            if i == 2:
                v2 = np.copy(v)
            if i == 1:
                v1 = np.copy(v)

        # Delta = (V_u - V_d) / (S_u - S_d)
        s_u = params.underlying_price * up
        s_d = params.underlying_price * dn
        delta = (v1[1] - v1[0]) / (s_u - s_d)

        # Gamma = [(V_uu - V_ud) / (S_uu - S_ud) - (V_ud - V_dd) / (S_ud - S_dd)]
        #         / [0.5 * (S_uu - S_dd)]
        s_uu = params.underlying_price * up**2
        s_ud = params.underlying_price
        s_dd = params.underlying_price * dn**2
        gamma = ((v2[2] - v2[1]) / (s_uu - s_ud) - (v2[1] - v2[0]) / (s_ud - s_dd)) / (
            0.5 * (s_uu - s_dd)
        )

        return float(v[0]), float(delta), float(gamma)

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks using CRR Binomial Tree."""
        start_time = time.time()

        def get_p(p: OptionParams) -> float:
            res, _, _ = self._tree_solve(p, self.num_steps)
            return res

        computed_price, delta, gamma = self._tree_solve(params, self.num_steps)

        # Richardson Extrapolation refinement
        if self.use_richardson:
            p_full, _d_full, _g_full = self._tree_solve(params, self.num_steps)
            p_half, _, _ = self._tree_solve(params, self.num_steps // 2)
            computed_price = 2 * p_full - p_half
            # Delta/Gamma from full tree are usually fine

        # Bumping for Vega, Theta, Rho
        h_v, h_t, h_r = 0.01, 1 / 365.0, 0.01
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
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            parameter_set={"num_steps": self.num_steps, "use_richardson": self.use_richardson},
        )
