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
        up_factor = np.exp(params.volatility * np.sqrt(delta_t))
        down_factor = 1.0 / up_factor
        risk_free_growth = np.exp(params.risk_free_rate * delta_t)
        prob_up = (risk_free_growth - down_factor) / (up_factor - down_factor)
        prob_down = 1.0 - prob_up

        # Terminal payoffs
        indices = np.arange(steps + 1)
        terminal_stock_prices = params.underlying_price * (up_factor**indices) * (down_factor ** (steps - indices))
        option_values = (
            np.maximum(terminal_stock_prices - params.strike_price, 0)
            if params.option_type == "call"
            else np.maximum(params.strike_price - terminal_stock_prices, 0)
        )

        # Backward induction
        values_at_step_1 = np.zeros(2)
        values_at_step_2 = np.zeros(3)
        for i in range(steps - 1, -1, -1):
            option_values = (prob_up * option_values[1:] + prob_down * option_values[:-1]) / risk_free_growth
            if params.is_american:
                stock_prices_at_step = (
                    params.underlying_price
                    * (up_factor ** np.arange(i + 1))
                    * (down_factor ** (i - np.arange(i + 1)))
                )
                option_values = np.maximum(
                    option_values,
                    (
                        stock_prices_at_step - params.strike_price
                        if params.option_type == "call"
                        else params.strike_price - stock_prices_at_step
                    ),
                )

            # Extract Delta/Gamma at step 1 and 2
            if i == 2:
                values_at_step_2 = np.copy(option_values)
            if i == 1:
                values_at_step_1 = np.copy(option_values)

        # Delta = (V_u - V_d) / (S_u - S_d)
        spot_up = params.underlying_price * up_factor
        spot_down = params.underlying_price * down_factor
        delta = (values_at_step_1[1] - values_at_step_1[0]) / (spot_up - spot_down)

        # Gamma = [(V_uu - V_ud) / (S_uu - S_ud) - (V_ud - V_dd) / (S_ud - S_dd)]
        #         / [0.5 * (S_uu - S_dd)]
        spot_up_up = params.underlying_price * up_factor**2
        spot_up_down = params.underlying_price
        spot_down_down = params.underlying_price * down_factor**2
        gamma = ((values_at_step_2[2] - values_at_step_2[1]) / (spot_up_up - spot_up_down) - (values_at_step_2[1] - values_at_step_2[0]) / (spot_up_down - spot_down_down)) / (
            0.5 * (spot_up_up - spot_down_down)
        )

        return float(option_values[0]), float(delta), float(gamma)

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
        vol_bump, time_bump, rate_bump = 0.01, 1 / 365.0, 0.01
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
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            parameter_set={"num_steps": self.num_steps, "use_richardson": self.use_richardson},
        )
