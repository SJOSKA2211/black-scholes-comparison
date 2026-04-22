"""Standard Monte Carlo method for option pricing."""

from __future__ import annotations

import time

import numpy as np

from src.methods.base import OptionParams, PriceResult


def price_standard_mc(params: OptionParams, num_paths: int = 100000) -> PriceResult:
    """Vectorized GBM Standard Monte Carlo."""
    start_time = time.time()

    underlying_price = params.underlying_price
    strike_price = params.strike_price
    maturity_years = params.maturity_years
    risk_free_rate = params.risk_free_rate
    volatility = params.volatility

    random_shocks = np.random.standard_normal(num_paths)
    terminal_prices = underlying_price * np.exp(
        (risk_free_rate - 0.5 * volatility**2) * maturity_years
        + volatility * np.sqrt(maturity_years) * random_shocks
    )

    if params.option_type == "call":
        payoffs = np.maximum(terminal_prices - strike_price, 0)
    else:
        payoffs = np.maximum(strike_price - terminal_prices, 0)

    discount_factor = np.exp(-risk_free_rate * maturity_years)
    price = discount_factor * np.mean(payoffs)
    std_error = np.std(payoffs) / np.sqrt(num_paths)

    exec_seconds = time.time() - start_time
    return PriceResult(
        method_type="standard_mc",
        computed_price=float(price),
        exec_seconds=exec_seconds,
        replications=num_paths,
        confidence_interval=(
            float(price - 1.96 * std_error),
            float(price + 1.96 * std_error),
        ),
        parameter_set={"num_paths": num_paths},
    )
