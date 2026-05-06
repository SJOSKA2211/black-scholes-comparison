"""Cox-Ross-Rubinstein Binomial Tree implementation."""

import time

import numpy as np

from src.methods.base import NumericalMethod, OptionParams, OptionType, PriceResult


def price_binomial_crr(params: OptionParams, num_steps: int) -> float:
    """Core CRR binomial tree logic."""
    underlying = params.underlying_price
    strike = params.strike_price
    maturity = params.maturity_years
    vol = params.volatility
    rate = params.risk_free_rate

    delta_time = maturity / num_steps
    up_factor = np.exp(vol * np.sqrt(delta_time))
    down_factor = 1 / up_factor
    risk_neutral_prob = (np.exp(rate * delta_time) - down_factor) / (up_factor - down_factor)
    discount = np.exp(-rate * delta_time)

    # Initialize asset prices at maturity
    asset_prices = (
        underlying
        * (up_factor ** np.arange(num_steps, -1, -1))
        * (down_factor ** np.arange(0, num_steps + 1))
    )

    # Initialize option values at maturity
    if params.option_type == OptionType.CALL:
        option_values = np.maximum(asset_prices - strike, 0)
    else:
        option_values = np.maximum(strike - asset_prices, 0)

    # Step back through the tree
    for step in range(num_steps - 1, -1, -1):
        option_values = discount * (
            risk_neutral_prob * option_values[:-1] + (1 - risk_neutral_prob) * option_values[1:]
        )

        if params.is_american:
            # Asset prices at the current step
            current_asset_prices = (
                underlying
                * (up_factor ** np.arange(step, -1, -1))
                * (down_factor ** np.arange(0, step + 1))
            )
            if params.option_type == OptionType.CALL:
                option_values = np.maximum(option_values, current_asset_prices - strike)
            else:
                option_values = np.maximum(option_values, strike - current_asset_prices)

    return float(option_values[0])


class BinomialCRR(NumericalMethod):
    """Standard Cox-Ross-Rubinstein Binomial Tree pricing."""

    async def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        # Default to 1000 steps for standard resolution
        num_steps = 1000
        price = price_binomial_crr(params, num_steps)

        exec_time = time.perf_counter() - start_time
        return PriceResult(
            price=float(price), exec_seconds=exec_time, metadata={"num_steps": num_steps}
        )
