import numpy as np
import time
from src.methods.base import OptionParams, PriceResult

class TreeMethods:
    """Binomial and Trinomial Lattice methods for option pricing."""

    def binomial_crr(self, params: OptionParams, n: int = 1000) -> PriceResult:
        start_time = time.time()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        dt = T / n
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp(r * dt) - d) / (u - d)
        df = np.exp(-r * dt)
        
        # In-place 1D backward induction to save memory
        prices = S * (u ** np.arange(n, -1, -1)) * (d ** np.arange(0, n + 1))
        
        if params.option_type == "call":
            values = np.maximum(prices - K, 0)
        else:
            values = np.maximum(K - prices, 0)
            
        for _ in range(n):
            values = df * (p * values[:-1] + (1 - p) * values[1:])
            if params.is_american:
                # Need to update prices for American exercise check
                n_curr = len(values) - 1
                prices = prices[1:] / u # simplified price update
                # Actually, more robustly:
                prices = S * (u ** np.arange(n_curr, -1, -1)) * (d ** np.arange(0, n_curr + 1))
                if params.option_type == "call":
                    values = np.maximum(values, prices - K)
                else:
                    values = np.maximum(values, K - prices)
                    
        price = values[0]
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="binomial_crr",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"n": n}
        )

    def trinomial(self, params: OptionParams, n: int = 500) -> PriceResult:
        """Trinomial tree implementation (Boyle 1988)."""
        start_time = time.time()
        
        S = params.underlying_price
        K = params.strike_price
        T = params.maturity_years
        r = params.risk_free_rate
        sigma = params.volatility
        
        dt = T / n
        dx = sigma * np.sqrt(3 * dt)
        
        u = np.exp(dx)
        d = 1 / u
        m = 1
        
        # Risk-neutral probabilities
        pu = 0.5 * (((sigma**2 * dt + (r - 0.5 * sigma**2)**2 * dt**2) / dx**2) + (r - 0.5 * sigma**2) * dt / dx)
        pd = 0.5 * (((sigma**2 * dt + (r - 0.5 * sigma**2)**2 * dt**2) / dx**2) - (r - 0.5 * sigma**2) * dt / dx)
        pm = 1 - pu - pd
        
        df = np.exp(-r * dt)
        
        # Terminal node prices
        prices = S * (u ** np.arange(n, -n - 1, -1))
        
        if params.option_type == "call":
            values = np.maximum(prices - K, 0)
        else:
            values = np.maximum(K - prices, 0)
            
        for i in range(n - 1, -1, -1):
            values = df * (pu * values[:-2] + pm * values[1:-1] + pd * values[2:])
            if params.is_american:
                prices = S * (u ** np.arange(i, -i - 1, -1))
                if params.option_type == "call":
                    values = np.maximum(values, prices - K)
                else:
                    values = np.maximum(values, K - prices)
                    
        price = values[0]
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="trinomial",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"n": n}
        )

    def binomial_crr_richardson(self, params: OptionParams, n: int = 1000) -> PriceResult:
        """Binomial CRR with Richardson extrapolation: 2*P(2n) - P(n)."""
        start_time = time.time()
        
        p1 = self.binomial_crr(params, n).computed_price
        p2 = self.binomial_crr(params, 2 * n).computed_price
        
        price = 2 * p2 - p1
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="binomial_crr_richardson",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"n": n}
        )

    def trinomial_richardson(self, params: OptionParams, n: int = 500) -> PriceResult:
        """Trinomial with Richardson extrapolation: 2*P(2n) - P(n)."""
        start_time = time.time()
        
        p1 = self.trinomial(params, n).computed_price
        p2 = self.trinomial(params, 2 * n).computed_price
        
        price = 2 * p2 - p1
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="trinomial_richardson",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"n": n}
        )
