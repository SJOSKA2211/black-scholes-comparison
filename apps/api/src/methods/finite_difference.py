import numpy as np
import time
from src.methods.base import OptionParams, PriceResult
from src.exceptions import CFLViolationError

class FiniteDifferenceMethods:
    """Finite Difference Methods for option pricing."""

    def _thomas_algorithm(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
        """
        Solves Ax = d where A is a tridiagonal matrix.
        a: lower diagonal, b: main diagonal, c: upper diagonal, d: right hand side.
        O(n) complexity.
        """
        n = len(d)
        c_prime = np.zeros(n)
        d_prime = np.zeros(n)
        
        c_prime[0] = c[0] / b[0]
        d_prime[0] = d[0] / b[0]
        
        for i in range(1, n):
            m = 1.0 / (b[i] - a[i] * c_prime[i-1])
            c_prime[i] = c[i] * m
            d_prime[i] = (d[i] - a[i] * d_prime[i-1]) * m
            
        x = np.zeros(n)
        x[-1] = d_prime[-1]
        for i in range(n-2, -1, -1):
            x[i] = d_prime[i] - c_prime[i] * x[i+1]
            
        return x

    def explicit_fdm(self, params: OptionParams, num_s: int = 100, num_t: int = 1000) -> PriceResult:
        start_time = time.time()
        S_max = 4 * params.strike_price
        dt = params.maturity_years / num_t
        dS = S_max / num_s
        
        # CFL Condition check: dt < 1 / (sigma^2 * num_s + r)
        # More accurately for BS: dt < (dS^2) / (sigma^2 * S^2)
        # Simplified conservative check:
        cfl_threshold = 0.5 * (dS**2) / (params.volatility**2 * S_max**2)
        if dt > cfl_threshold:
            suggested_num_t = int(params.maturity_years / (0.9 * cfl_threshold)) + 1
            raise CFLViolationError(
                f"CFL condition violated. dt ({dt:.6f}) > threshold ({cfl_threshold:.6f}).",
                suggested_dt=params.maturity_years / suggested_num_t
            )

        S_values = np.linspace(0, S_max, num_s + 1)
        grid = np.zeros((num_t + 1, num_s + 1))
        
        # Terminal condition
        if params.option_type == "call":
            grid[0, :] = np.maximum(S_values - params.strike_price, 0)
        else:
            grid[0, :] = np.maximum(params.strike_price - S_values, 0)
            
        # Time stepping
        for j in range(0, num_t):
            for i in range(1, num_s):
                sigma2 = params.volatility**2
                r = params.risk_free_rate
                
                a = 0.5 * dt * (sigma2 * i**2 - r * i)
                b = 1 - dt * (sigma2 * i**2 + r)
                c = 0.5 * dt * (sigma2 * i**2 + r * i)
                
                grid[j+1, i] = a * grid[j, i-1] + b * grid[j, i] + c * grid[j, i+1]
            
            # Boundary conditions
            if params.option_type == "call":
                grid[j+1, 0] = 0
                grid[j+1, num_s] = S_max - params.strike_price * np.exp(-r * (j+1) * dt)
            else:
                grid[j+1, 0] = params.strike_price * np.exp(-r * (j+1) * dt)
                grid[j+1, num_s] = 0
                
        price = np.interp(params.underlying_price, S_values, grid[num_t, :])
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="explicit_fdm",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_s": num_s, "num_t": num_t}
        )

    def implicit_fdm(self, params: OptionParams, num_s: int = 100, num_t: int = 100) -> PriceResult:
        start_time = time.time()
        S_max = 4 * params.strike_price
        dt = params.maturity_years / num_t
        dS = S_max / num_s
        S_values = np.linspace(0, S_max, num_s + 1)
        
        # Payoff at maturity
        if params.option_type == "call":
            V = np.maximum(S_values - params.strike_price, 0)
        else:
            V = np.maximum(params.strike_price - S_values, 0)
            
        sigma2 = params.volatility**2
        r = params.risk_free_rate
        
        # Tridiagonal matrix coefficients
        idx = np.arange(1, num_s)
        a = -0.5 * dt * (sigma2 * idx**2 - r * idx)
        b = 1 + dt * (sigma2 * idx**2 + r)
        c = -0.5 * dt * (sigma2 * idx**2 + r * idx)
        
        for j in range(num_t):
            d = V[1:-1].copy()
            # Boundary adjustments to right-hand side
            if params.option_type == "call":
                # V[0] = 0, V[num_s] = S_max - K*exp(-r*t)
                d[-1] -= c[-1] * (S_max - params.strike_price * np.exp(-r * (j+1) * dt))
            else:
                d[0] -= a[0] * (params.strike_price * np.exp(-r * (j+1) * dt))
            
            V[1:-1] = self._thomas_algorithm(a, b, c, d)
            
            # Boundary conditions
            if params.option_type == "call":
                V[0] = 0
                V[num_s] = S_max - params.strike_price * np.exp(-r * (j+1) * dt)
            else:
                V[0] = params.strike_price * np.exp(-r * (j+1) * dt)
                V[num_s] = 0
                
        price = np.interp(params.underlying_price, S_values, V)
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="implicit_fdm",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_s": num_s, "num_t": num_t}
        )

    def crank_nicolson(self, params: OptionParams, num_s: int = 100, num_t: int = 100) -> PriceResult:
        start_time = time.time()
        S_max = 4 * params.strike_price
        dt = params.maturity_years / num_t
        dS = S_max / num_s
        S_values = np.linspace(0, S_max, num_s + 1)
        
        if params.option_type == "call":
            V = np.maximum(S_values - params.strike_price, 0)
        else:
            V = np.maximum(params.strike_price - S_values, 0)
            
        sigma2 = params.volatility**2
        r = params.risk_free_rate
        idx = np.arange(1, num_s)
        
        # Coefficients for (I - theta*dt*L)V^{n+1} = (I + (1-theta)*dt*L)V^n
        # Here theta = 0.5
        alpha = 0.25 * dt * (sigma2 * idx**2 - r * idx)
        beta = 0.5 * dt * (sigma2 * idx**2 + r)
        gamma = 0.25 * dt * (sigma2 * idx**2 + r * idx)
        
        # Matrix A (Implicit part)
        a_mat = -alpha
        b_mat = 1 + beta
        c_mat = -gamma
        
        for j in range(num_t):
            # Right hand side (Explicit part)
            d = (alpha * V[:-2] + (1 - beta) * V[1:-1] + gamma * V[2:])
            
            # Boundary adjustments
            if params.option_type == "call":
                boundary_prev = S_max - params.strike_price * np.exp(-r * j * dt)
                boundary_curr = S_max - params.strike_price * np.exp(-r * (j+1) * dt)
                d[-1] += gamma[-1] * (boundary_curr + boundary_prev)
            else:
                boundary_prev = params.strike_price * np.exp(-r * j * dt)
                boundary_curr = params.strike_price * np.exp(-r * (j+1) * dt)
                d[0] += alpha[0] * (boundary_curr + boundary_prev)
                
            V[1:-1] = self._thomas_algorithm(a_mat, b_mat, c_mat, d)
            
            # Update boundaries
            if params.option_type == "call":
                V[0] = 0
                V[num_s] = S_max - params.strike_price * np.exp(-r * (j+1) * dt)
            else:
                V[0] = params.strike_price * np.exp(-r * (j+1) * dt)
                V[num_s] = 0
                
        price = np.interp(params.underlying_price, S_values, V)
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="crank_nicolson",
            computed_price=float(price),
            exec_seconds=exec_seconds,
            parameter_set={"num_s": num_s, "num_t": num_t}
        )
