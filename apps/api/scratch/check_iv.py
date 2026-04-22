import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm
import time

class OptionParams:
    def __init__(self, underlying_price, strike_price, maturity_years, risk_free_rate, volatility, option_type, is_american=False):
        self.underlying_price = underlying_price
        self.strike_price = strike_price
        self.maturity_years = maturity_years
        self.risk_free_rate = risk_free_rate
        self.volatility = volatility
        self.option_type = option_type
        self.is_american = is_american
    def model_copy(self, update):
        for k, v in update.items():
            setattr(self, k, v)
        return self

def price(params):
    S = params.underlying_price
    K = params.strike_price
    T = params.maturity_years
    r = params.risk_free_rate
    sigma = params.volatility
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if params.option_type == "call":
        p = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        p = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return type('obj', (object,), {'computed_price': p})

def implied_volatility(market_price, params):
    def objective(sigma_test):
        test_params = params.model_copy({"volatility": sigma_test})
        return price(test_params).computed_price - market_price
    try:
        return float(brentq(objective, 1e-6, 5.0))
    except ValueError as e:
        print(f"Caught ValueError: {e}")
        return 0.0

params = OptionParams(100.0, 100.0, 1.0, 0.05, 0.2, "call")
print(f"Price for IV 1000: {implied_volatility(1000.0, params)}")
print(f"Price for IV 0.0001: {implied_volatility(0.0001, params)}")
