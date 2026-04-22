"""Antithetic Monte Carlo method for option pricing."""

from __future__ import annotations

import time
from typing import cast

import numpy as np

from src.methods.base import OptionParams, PriceResult


def price_antithetic_mc(params: OptionParams, num_paths: int = 100000) -> PriceResult:
    """Antithetic Variates Monte Carlo."""
    start_time = time.time()
    # Ensure num_paths is even for paired paths
    effective_paths = (num_paths + 1) // 2

    underlying_price = params.underlying_price
    strike_price = params.strike_price
    maturity_years = params.maturity_years
    risk_free_rate = params.risk_free_rate
    volatility = params.volatility

    random_shocks = np.random.standard_normal(effective_paths)

    def compute_payoff(noise: np.ndarray) -> np.ndarray:
        st_price = underlying_price * np.exp(
            (risk_free_rate - 0.5 * volatility**2) * maturity_years
            + volatility * np.sqrt(maturity_years) * noise
        )
        if params.option_type == "call":
            return cast("np.ndarray", np.maximum(st_price - strike_price, 0))
        return cast("np.ndarray", np.maximum(strike_price - st_price, 0))

    payoffs_primary = compute_payoff(random_shocks)
    payoffs_antithetic = compute_payoff(-random_shocks)

    combined_payoffs = (payoffs_primary + payoffs_antithetic) / 2
    discount_factor = np.exp(-risk_free_rate * maturity_years)
    price = discount_factor * np.mean(combined_payoffs)
    std_error = np.std(combined_payoffs) / np.sqrt(effective_paths)

    exec_seconds = time.time() - start_time
    return PriceResult(
        method_type="antithetic_mc",
        computed_price=float(price),
        exec_seconds=exec_seconds,
        replications=effective_paths * 2,
        confidence_interval=(
            float(price - 1.96 * std_error),
            float(price + 1.96 * std_error),
        ),
        parameter_set={"num_paths": effective_paths * 2},
    )
