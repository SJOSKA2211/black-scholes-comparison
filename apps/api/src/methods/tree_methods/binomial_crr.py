"""Cox-Ross-Rubinstein binomial tree method."""

from __future__ import annotations

import numpy as np

from src.methods.base import BasePricingMethod, OptionParameters, OptionType


class BinomialCRR(BasePricingMethod):
    """Cox-Ross-Rubinstein binomial tree solver."""

    def __init__(self, steps: int = 500) -> None:
        super().__init__("binomial_crr")
        self.steps = steps

    def _compute(self, params: OptionParameters) -> float:
        """Execute Binomial CRR computation."""
        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        volatility = params.volatility
        rate = params.risk_free_rate

        delta_t = maturity / self.steps
        up_factor = np.exp(volatility * np.sqrt(delta_t))
        down_factor = 1 / up_factor
        prob_up = (np.exp(rate * delta_t) - down_factor) / (up_factor - down_factor)
        discount_factor = np.exp(-rate * delta_t)

        # Terminal stock prices
        stock_prices = (
            underlying
            * (up_factor ** np.arange(self.steps, -1, -1))
            * (down_factor ** np.arange(0, self.steps + 1))
        )

        # Terminal option values
        if params.option_type == OptionType.CALL:
            option_values = np.maximum(stock_prices - strike, 0)
        else:
            option_values = np.maximum(strike - stock_prices, 0)

        # Backward induction
        for step_idx in range(self.steps - 1, -1, -1):
            option_values = discount_factor * (
                prob_up * option_values[:-1] + (1 - prob_up) * option_values[1:]
            )

            if params.is_american:
                # American exercise check
                current_stock_prices = (
                    underlying
                    * (up_factor ** np.arange(step_idx, -1, -1))
                    * (down_factor ** np.arange(0, step_idx + 1))
                )
                if params.option_type == OptionType.CALL:
                    option_values = np.maximum(option_values, current_stock_prices - strike)
                else:
                    option_values = np.maximum(option_values, strike - current_stock_prices)

        return float(option_values[0])
