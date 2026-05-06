"""Cox-Ross-Rubinstein binomial tree implementation."""

from __future__ import annotations

import numpy as np

from src.methods.base import OptionParams


class BinomialCRR:
    """Standard Cox-Ross-Rubinstein binomial tree implementation."""

    def price_tree(self, params: OptionParams, num_steps: int) -> float:
        """
        Compute the price using a CRR binomial tree with N steps.
        Uses descriptive variable names.
        """
        expiry = params.maturity_years
        rate = params.risk_free_rate
        sigma = params.volatility
        underlying = params.underlying_price
        strike = params.strike_price

        time_step = expiry / num_steps
        up_factor = np.exp(sigma * np.sqrt(time_step))
        down_factor = 1.0 / up_factor

        # Risk-neutral probability
        # prob = (exp(r*dt) - d) / (u - d)
        exp_rt = np.exp(rate * time_step)
        prob_up = (exp_rt - down_factor) / (up_factor - down_factor)
        prob_down = 1.0 - prob_up

        # Terminal payoffs
        # S_nj = S0 * u^j * d^(n-j)
        j_indices = np.arange(num_steps + 1)
        terminal_prices = (
            underlying * (up_factor**j_indices) * (down_factor ** (num_steps - j_indices))
        )

        if params.is_call:
            grid = np.maximum(terminal_prices - strike, 0.0)
        else:
            grid = np.maximum(strike - terminal_prices, 0.0)

        # Backward induction
        discount = np.exp(-rate * time_step)
        for _ in range(num_steps - 1, -1, -1):
            grid = discount * (prob_up * grid[1:] + prob_down * grid[:-1])

            # American exercise
            if params.is_american:
                # Need prices at this step
                step_prices = (
                    underlying
                    * (up_factor ** np.arange(_ + 1))
                    * (down_factor ** (_ - np.arange(_ + 1)))
                )
                if params.is_call:
                    grid = np.maximum(grid, step_prices - strike)
                else:
                    grid = np.maximum(grid, strike - step_prices)

        return float(grid[0])
