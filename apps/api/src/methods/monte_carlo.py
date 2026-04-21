import time

import numpy as np
from scipy.stats import norm, qmc

from src.methods.base import OptionParams, PriceResult


class MonteCarloMethods:
    """Monte Carlo methods for option pricing."""

    def standard_mc(self, params: OptionParams, num_paths: int = 100000) -> PriceResult:
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

    def antithetic_mc(
        self, params: OptionParams, num_paths: int = 100000
    ) -> PriceResult:
        start_time = time.time()
        # Ensure num_paths is even for paired paths
        effective_paths = (num_paths + 1) // 2

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        random_shocks = np.random.standard_normal(effective_paths)

        def compute_payoff(noise):
            st_price = underlying_price * np.exp(
                (risk_free_rate - 0.5 * volatility**2) * maturity_years
                + volatility * np.sqrt(maturity_years) * noise
            )
            if params.option_type == "call":
                return np.maximum(st_price - strike_price, 0)
            return np.maximum(strike_price - st_price, 0)

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

    def control_variate_mc(
        self, params: OptionParams, num_paths: int = 100000
    ) -> PriceResult:
        """Uses terminal underlying price as Control Variate."""
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
            target_payoffs = np.maximum(terminal_prices - strike_price, 0)
        else:
            target_payoffs = np.maximum(strike_price - terminal_prices, 0)

        # Control variate: terminal underlying price (S_T)
        # E[S_T] = S * exp(r*T)
        control_mean = underlying_price * np.exp(risk_free_rate * maturity_years)

        cov_matrix = np.cov(target_payoffs, terminal_prices)
        beta_star = cov_matrix[0, 1] / cov_matrix[1, 1]

        cv_payoffs = target_payoffs - beta_star * (terminal_prices - control_mean)
        discount_factor = np.exp(-risk_free_rate * maturity_years)
        price = discount_factor * np.mean(cv_payoffs)
        std_error = np.std(cv_payoffs) / np.sqrt(num_paths)

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
            parameter_set={"num_paths": num_paths, "beta_star": float(beta_star)},
        )

    def quasi_mc(self, params: OptionParams, num_paths: int = 65536) -> PriceResult:
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
