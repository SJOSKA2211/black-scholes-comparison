"""Crank-Nicolson finite difference method for option pricing."""
from __future__ import annotations
from typing import Any
import numpy as np
from src.methods.base import BasePricingMethod, OptionParameters, OptionType

class CrankNicolson(BasePricingMethod):
    """Crank-Nicolson finite difference solver."""
    
    def __init__(self, mesh_points_s: int = 100, mesh_points_t: int = 100) -> None:
        super().__init__("crank_nicolson")
        self.mesh_points_s = mesh_points_s
        self.mesh_points_t = mesh_points_t

    def _compute(self, params: OptionParameters) -> float:
        """Execute Crank-Nicolson computation."""
        underlying = params.underlying_price
        strike = params.strike_price
        maturity = params.maturity_years
        volatility = params.volatility
        rate = params.risk_free_rate
        
        # Grid setup
        s_max = 3.0 * strike
        ds = s_max / self.mesh_points_s
        dt = maturity / self.mesh_points_t
        
        s_values = np.linspace(0, s_max, self.mesh_points_s + 1)
        v_grid = np.zeros(self.mesh_points_s + 1)
        
        # Payoff boundary condition at maturity
        if params.option_type == OptionType.CALL:
            v_grid = np.maximum(s_values - strike, 0)
        else:
            v_grid = np.maximum(strike - s_values, 0)
            
        # Crank-Nicolson coefficients
        # j = index from 0 to M
        j = np.arange(self.mesh_points_s + 1)
        alpha = 0.25 * dt * (volatility**2 * j**2 - rate * j)
        beta = -0.5 * dt * (volatility**2 * j**2 + rate)
        gamma = 0.25 * dt * (volatility**2 * j**2 + rate * j)
        
        # Matrices for inner points i = 1 to M-1
        # A * V_new = B * V_old + boundary_terms
        # A = [ -alpha, 1-beta, -gamma ]
        # B = [ alpha, 1+beta, gamma ]
        
        lower_a = -alpha[1:self.mesh_points_s]
        diag_a = 1.0 - beta[1:self.mesh_points_s]
        upper_a = -gamma[1:self.mesh_points_s]
        
        lower_b = alpha[1:self.mesh_points_s]
        diag_b = 1.0 + beta[1:self.mesh_points_s]
        upper_b = gamma[1:self.mesh_points_s]
        
        for step_idx in range(self.mesh_points_t):
            # Calculate explicit part (B * V_old)
            # rhs[i-1] = lower_b[i-1]*V[i-1] + diag_b[i-1]*V[i] + upper_b[i-1]*V[i+1]
            # for i = 1 to M-1
            rhs = (
                lower_b * v_grid[0 : self.mesh_points_s - 1] 
                + diag_b * v_grid[1 : self.mesh_points_s] 
                + upper_b * v_grid[2 : self.mesh_points_s + 1]
            )
            
            # Boundary conditions (Dirichlet) at new time step
            t_remaining = (step_idx + 1) * dt
            if params.option_type == OptionType.CALL:
                v_new_0 = 0.0
                v_new_m = s_max - strike * np.exp(-rate * t_remaining)
            else:
                v_new_0 = strike * np.exp(-rate * t_remaining)
                v_new_m = 0.0
                
            # Add implicit boundary terms to rhs
            rhs[0] += alpha[1] * v_new_0
            rhs[-1] += gamma[self.mesh_points_s - 1] * v_new_m
            
            # Solve A * V_new = rhs using Thomas Algorithm
            v_grid[1:self.mesh_points_s] = self._thomas_algorithm(lower_a[1:], diag_a, upper_a[:-1], rhs)
            v_grid[0] = v_new_0
            v_grid[-1] = v_new_m
            
            # American option early exercise constraint
            if params.is_american:
                if params.option_type == OptionType.CALL:
                    v_grid = np.maximum(v_grid, s_values - strike)
                else:
                    v_grid = np.maximum(v_grid, strike - s_values)
                    
        # Interpolate result
        return float(np.interp(underlying, s_values, v_grid))

    def _thomas_algorithm(
        self, 
        lower: np.ndarray[Any, np.dtype[np.float64]], 
        diag: np.ndarray[Any, np.dtype[np.float64]], 
        upper: np.ndarray[Any, np.dtype[np.float64]], 
        rhs: np.ndarray[Any, np.dtype[np.float64]]
    ) -> np.ndarray[Any, np.dtype[np.float64]]:
        """O(n) solver for tridiagonal systems."""
        n = len(diag)
        cp = np.zeros(n)
        dp = np.zeros(n)
        
        cp[0] = upper[0] / diag[0]
        dp[0] = rhs[0] / diag[0]
        
        for i in range(1, n):
            m = diag[i] - lower[i-1] * cp[i-1]
            if i < n - 1:
                cp[i] = upper[i] / m
            dp[i] = (rhs[i] - lower[i-1] * dp[i-1]) / m
            
        result = np.zeros(n)
        result[-1] = dp[-1]
        for i in range(n-2, -1, -1):
            result[i] = dp[i] - cp[i] * result[i+1]
            
        return result
