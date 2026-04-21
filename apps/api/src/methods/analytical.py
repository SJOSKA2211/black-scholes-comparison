import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
import time
from src.methods.base import OptionParams, PriceResult

class BlackScholesAnalytical:
    """Closed-form Black-Scholes model for European options."""
    
    def price(self, params: OptionParams) -> PriceResult:
        start_time = time.time()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if params.option_type == "call":
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="analytical",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={}
        )

    def delta(self, params: OptionParams) -> float:
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        if params.option_type == "call":
            return float(norm.cdf(d1))
        else:
            return float(norm.cdf(d1) - 1)

    def gamma(self, params: OptionParams) -> float:
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        return float(gamma)

    def vega(self, params: OptionParams) -> float:
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        vega = S * norm.pdf(d1) * np.sqrt(T)
        return float(vega)

    def implied_volatility(self, market_price: float, params: OptionParams) -> float:
        def objective(sigma):
            test_params = params.model_copy(update={"volatility": sigma})
            return self.price(test_params).computed_price - market_price
        
        try:
            return float(brentq(objective, 1e-6, 5.0))
        except ValueError:
            return 0.0
