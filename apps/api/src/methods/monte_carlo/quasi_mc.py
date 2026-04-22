"""Quasi-Monte Carlo method for option pricing."""

from __future__ import annotations

import time

import numpy as np
from scipy.stats import norm, qmc  # type: ignore

from src.methods.base import OptionParams, PriceResult


def price_quasi_mc(params: OptionParams, num_paths: int = 65536) -> PriceResult:
    """Quasi-Monte Carlo using Sobol sequence."""
    start_time = time.time()
    # Enforce power of 2 for Sobol efficiency
    effective_num_paths = 2 ** int(np.round(np.log2(num_paths)))

    sampler = qmc.Sobol(d=1, scramble=True)
    uniform_samples = sampler.random(n=effective_num_paths)
    # Inverse transform to standard normal
    gaussian_samples = norm.ppf(uniform_samples).flatten()

    underlying_price = params.underlying_price
    strike_price = params.strike_price
    maturity_years = params.maturity_years
    risk_free_rate = params.risk_free_rate
    volatility = params.volatility

    terminal_prices = underlying_price * np.exp(
        (risk_free_rate - 0.5 * volatility**2) * maturity_years
        + volatility * np.sqrt(maturity_years) * gaussian_samples
    )

    if params.option_type == "call":
        payoffs = np.maximum(terminal_prices - strike_price, 0)
    else:
        payoffs = np.maximum(strike_price - terminal_prices, 0)

    discount_factor = np.exp(-risk_free_rate * maturity_years)
    price = discount_factor * np.mean(payoffs)

    exec_seconds = time.time() - start_time
    return PriceResult(
        method_type="quasi_mc",
        computed_price=float(price),
        exec_seconds=exec_seconds,
        replications=effective_num_paths,
        parameter_set={"num_paths": effective_num_paths},
    )
