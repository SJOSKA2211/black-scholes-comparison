import numpy as np
import time
from scipy.stats import qmc
from src.methods.base import OptionParams, PriceResult

class MonteCarloMethods:
    """Monte Carlo methods for option pricing."""

    def standard_mc(self, params: OptionParams, num_paths: int = 100000) -> PriceResult:
        start_time = time.time()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        z = np.random.standard_normal(num_paths)
        S_T = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
        
        if params.option_type == "call":
            payoffs = np.maximum(S_T - K, 0)
        else:
            payoffs = np.maximum(K - S_T, 0)
            
        price = np.exp(-r * T) * np.mean(payoffs)
        std_err = np.std(payoffs) / np.sqrt(num_paths)
        
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="standard_mc",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            replications=num_paths,
            confidence_interval=(float(price - 1.96 * std_err), float(price + 1.96 * std_err)),
            parameter_set={"num_paths": num_paths}
        )

    def antithetic_mc(self, params: OptionParams, num_paths: int = 100000) -> PriceResult:
        start_time = time.time()
        # Round up to even
        num_paths = (num_paths + 1) // 2
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        z = np.random.standard_normal(num_paths)
        
        def get_payoff(noise):
            ST = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * noise)
            if params.option_type == "call":
                return np.maximum(ST - K, 0)
            return np.maximum(K - ST, 0)
            
        payoffs_1 = get_payoff(z)
        payoffs_2 = get_payoff(-z)
        
        combined_payoffs = (payoffs_1 + payoffs_2) / 2
        price = np.exp(-r * T) * np.mean(combined_payoffs)
        std_err = np.std(combined_payoffs) / np.sqrt(num_paths)
        
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="antithetic_mc",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            replications=num_paths * 2,
            confidence_interval=(float(price - 1.96 * std_err), float(price + 1.96 * std_err)),
            parameter_set={"num_paths": num_paths * 2}
        )

    def control_variate_mc(self, params: OptionParams, num_paths: int = 100000) -> PriceResult:
        """Uses terminal underlying price as Control Variate."""
        start_time = time.time()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        z = np.random.standard_normal(num_paths)
        S_T = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
        
        if params.option_type == "call":
            target_payoffs = np.maximum(S_T - K, 0)
        else:
            target_payoffs = np.maximum(K - S_T, 0)
            
        # Control variate: S_T
        control_payoffs = S_T
        control_mean = S * np.exp(r * T)
        
        cov_matrix = np.cov(target_payoffs, control_payoffs)
        beta = cov_matrix[0, 1] / cov_matrix[1, 1]
        
        cv_payoffs = target_payoffs - beta * (control_payoffs - control_mean)
        price = np.exp(-r * T) * np.mean(cv_payoffs)
        std_err = np.std(cv_payoffs) / np.sqrt(num_paths)
        
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="control_variate_mc",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            replications=num_paths,
            confidence_interval=(float(price - 1.96 * std_err), float(price + 1.96 * std_err)),
            parameter_set={"num_paths": num_paths}
        )

    def quasi_mc(self, params: OptionParams, num_paths: int = 65536) -> PriceResult:
        """Quasi-Monte Carlo using Sobol sequence."""
        start_time = time.time()
        # Ensure num_paths is a power of 2 for Sobol efficiency
        num_paths = 2**int(np.round(np.log2(num_paths)))
        
        sampler = qmc.Sobol(d=1, scramble=True)
        sample = sampler.random(n=num_paths)
        z = np.sqrt(2) * np.vectorize(lambda x: 0)(sample) # placeholder for inverse transform
        # Proper inverse transform
        from scipy.stats import norm
        z = norm.ppf(sample).flatten()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        S_T = S * np.exp((r - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * z)
        
        if params.option_type == "call":
            payoffs = np.maximum(S_T - K, 0)
        else:
            payoffs = np.maximum(K - S_T, 0)
            
        price = np.exp(-r * T) * np.mean(payoffs)
        # Note: Standard error estimation for QMC is different, using sample mean here
        
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="quasi_mc",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            replications=num_paths,
            parameter_set={"num_paths": num_paths}
        )

def norm_cdf(x):
    from scipy.stats import norm
    return norm.cdf(x)
