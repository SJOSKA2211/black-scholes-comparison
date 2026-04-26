"""Analytical Black-Scholes-Merton solution with Greeks."""

from __future__ import annotations

import time

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from src.methods.base import MethodType, OptionParams, PriceResult


class BlackScholesAnalytical:
    """
    Standard Black-Scholes-Merton analytical solution.
    Provides the benchmark price and Greeks (Delta, Gamma, Theta, Vega, Rho).
    Adheres to Section 15 of the v4 mandate.
    """

    method_type: MethodType = "analytical"

    def __init__(self) -> None:
        pass

    def delta(self, params: OptionParams) -> float:
        """Analytical Delta."""
        res = self.price(params)
        return float(res.delta) if res.delta is not None else 0.0

    def gamma(self, params: OptionParams) -> float:
        """Analytical Gamma."""
        res = self.price(params)
        return float(res.gamma) if res.gamma is not None else 0.0

    def vega(self, params: OptionParams) -> float:
        """Analytical Vega."""
        res = self.price(params)
        return float(res.vega) if res.vega is not None else 0.0

    def theta(self, params: OptionParams) -> float:
        """Analytical Theta."""
        res = self.price(params)
        return float(res.theta) if res.theta is not None else 0.0

    def rho(self, params: OptionParams) -> float:
        """Analytical Rho."""
        res = self.price(params)
        return float(res.rho) if res.rho is not None else 0.0

    def geometric_asian_price(self, params: OptionParams, num_steps: int = 100) -> PriceResult:
        """
        Analytical solution for Geometric Asian Option (Discrete Monitoring).
        Used as control variate in MC methods.
        Ref: Vorst (1992).
        """
        start_time = time.time()

        sigma = params.volatility
        risk_free = params.risk_free_rate
        maturity = params.maturity_years
        underlying = params.underlying_price
        strike = params.strike_price
        num_discrete_steps = num_steps

        # Vorst (1992) discrete adjustment
        # sig_a^2 = sig^2 * (n+1)(2n+1) / (6n^2)
        sig_a = sigma * np.sqrt(
            (num_discrete_steps + 1) * (2 * num_discrete_steps + 1) / (6.0 * num_discrete_steps**2)
        )

        # mu_a = (r - 0.5*sig^2) * (n+1)/(2n) + 0.5*sig_a^2
        mu_a = (risk_free - 0.5 * sigma**2) * (num_discrete_steps + 1) / (
            2.0 * num_discrete_steps
        ) + 0.5 * sig_a**2

        d1 = (np.log(underlying / strike) + (mu_a + 0.5 * sig_a**2) * maturity) / (
            sig_a * np.sqrt(maturity)
        )
        d2 = d1 - sig_a * np.sqrt(maturity)

        exp_rt = np.exp(-risk_free * maturity)
        if params.option_type == "call":
            price = underlying * np.exp((mu_a - risk_free) * maturity) * norm.cdf(
                d1
            ) - strike * exp_rt * norm.cdf(d2)
        else:
            price = strike * exp_rt * norm.cdf(-d2) - underlying * np.exp(
                (mu_a - risk_free) * maturity
            ) * norm.cdf(-d1)

        return PriceResult(
            method_type="analytical_asian",
            computed_price=float(price),
            exec_seconds=time.time() - start_time,
        )

    def implied_volatility(
        self, target_price: float, params: OptionParams, max_iter: int = 100, tol: float = 1e-6
    ) -> float:
        """Brent's method for Implied Volatility inversion."""

        def objective(sigma: float) -> float:
            p = params.model_copy(update={"volatility": max(0.0001, sigma)})
            return self.price(p).computed_price - target_price

        # Check intrinsic value
        intrinsic = (
            max(params.underlying_price - params.strike_price, 0)
            if params.option_type == "call"
            else max(params.strike_price - params.underlying_price, 0)
        )
        if target_price <= intrinsic * np.exp(-params.risk_free_rate * params.maturity_years):
            return 0.0

        try:
            return float(brentq(objective, 1e-6, 5.0, xtol=tol, maxiter=max_iter))
        except (ValueError, RuntimeError):
            return 0.0

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price and Greeks analytically."""
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        # Avoid division by zero
        sqrt_t = np.sqrt(maturity_years)
        vol_sqrt_t = volatility * sqrt_t

        d_one = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / vol_sqrt_t
        d_two = d_one - vol_sqrt_t

        exp_rt = np.exp(-risk_free_rate * maturity_years)

        if params.option_type == "call":
            computed_price = underlying_price * norm.cdf(d_one) - strike_price * exp_rt * norm.cdf(
                d_two
            )
            delta = float(norm.cdf(d_one))
            theta = float(
                -(underlying_price * norm.pdf(d_one) * volatility) / (2 * sqrt_t)
                - risk_free_rate * strike_price * exp_rt * norm.cdf(d_two)
            )
            rho = float(strike_price * maturity_years * exp_rt * norm.cdf(d_two))
        else:
            computed_price = strike_price * exp_rt * norm.cdf(-d_two) - underlying_price * norm.cdf(
                -d_one
            )
            delta = float(norm.cdf(d_one) - 1)
            theta = float(
                -(underlying_price * norm.pdf(d_one) * volatility) / (2 * sqrt_t)
                + risk_free_rate * strike_price * exp_rt * norm.cdf(-d_two)
            )
            rho = float(-strike_price * maturity_years * exp_rt * norm.cdf(-d_two))

        gamma = float(norm.pdf(d_one) / (underlying_price * vol_sqrt_t))
        vega = float(underlying_price * sqrt_t * norm.pdf(d_one))

        return PriceResult(
            method_type=self.method_type,
            computed_price=float(computed_price),
            exec_seconds=time.time() - start_time,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            parameter_set={
                "d_one": float(d_one),
                "d_two": float(d_two),
            },
        )
