"""Control Variate Monte Carlo method for option pricing."""
from __future__ import annotations
import time
import numpy as np
from src.methods.base import OptionParams, PriceResult
from src.methods.analytical import BlackScholesAnalytical
 
def price_control_variate_mc(
    params: OptionParams, num_paths: int = 100000, num_steps: int = 50
) -> PriceResult:
    """Monte Carlo with Geometric Asian Control Variate."""
    start_time = time.time()
 
    underlying_price = params.underlying_price
    strike_price = params.strike_price
    maturity_years = params.maturity_years
    risk_free_rate = params.risk_free_rate
    volatility = params.volatility
 
    dt = maturity_years / num_steps
    
    # Path simulation
    # S(t+dt) = S(t) * exp((r - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
    paths = np.zeros((num_paths, num_steps + 1))
    paths[:, 0] = underlying_price
    
    for t in range(1, num_steps + 1):
        z = np.random.standard_normal(num_paths)
        paths[:, t] = paths[:, t-1] * np.exp(
            (risk_free_rate - 0.5 * volatility**2) * dt 
            + volatility * np.sqrt(dt) * z
        )
 
    # Terminal payoffs (European)
    terminal_prices = paths[:, -1]
    if params.option_type == "call":
        target_payoffs = np.maximum(terminal_prices - strike_price, 0)
    else:
        target_payoffs = np.maximum(strike_price - terminal_prices, 0)
 
    # Control variate: Geometric Asian payoff
    # Geometric mean = exp( (1/N) * sum(log(S_i)) )
    geometric_means = np.exp(np.mean(np.log(paths[:, 1:]), axis=1))
    if params.option_type == "call":
        cv_payoffs = np.maximum(geometric_means - strike_price, 0)
    else:
        cv_payoffs = np.maximum(strike_price - geometric_means, 0)
 
    # Analytical Geometric Asian price
    analytical_cv = BlackScholesAnalytical().geometric_asian_price(params).computed_price
    # Optimal beta
    cov_matrix = np.cov(target_payoffs, cv_payoffs)
    beta_star = cov_matrix[0, 1] / cov_matrix[1, 1]
 
    # CV Adjusted payoffs
    discount_factor = np.exp(-risk_free_rate * maturity_years)
    adjusted_payoffs = target_payoffs - beta_star * (cv_payoffs - analytical_cv / discount_factor)
    
    price = discount_factor * np.mean(adjusted_payoffs)
    std_error = np.std(adjusted_payoffs) / np.sqrt(num_paths)
 
    exec_seconds = time.time() - start_time
    return PriceResult(
        method_type="control_variate_mc",
        computed_price=float(price),
        exec_seconds=exec_seconds,
        replications=num_paths,
        confidence_interval=(
            float(price - 1.96 * std_error),
            float(price + 1.96 * std_error),
        ),
        parameter_set={"num_paths": num_paths, "num_steps": num_steps, "beta_star": float(beta_star)},
    )
