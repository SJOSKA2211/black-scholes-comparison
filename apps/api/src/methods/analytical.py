"""Analytical Black-Scholes-Merton solution with Greeks."""

from __future__ import annotations

import time

import numpy as np
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
        return res.delta

    def gamma(self, params: OptionParams) -> float:
        """Analytical Gamma."""
        res = self.price(params)
        return res.gamma

    def vega(self, params: OptionParams) -> float:
        """Analytical Vega."""
        res = self.price(params)
        return res.vega

    def geometric_asian_price(self, params: OptionParams) -> PriceResult:
        """
        Analytical solution for Geometric Asian Option.
        Used as control variate in MC methods.
        """
        start_time = time.time()
        # Adjusted volatility and interest rate for geometric Asian
        sig_sq = params.volatility**2
        v_adj = params.volatility / np.sqrt(3.0)
        r_adj = 0.5 * (
            params.risk_free_rate
            - 0.5 * sig_sq
            + (1.0 / 3.0) * (params.risk_free_rate - 0.5 * sig_sq + 0.5 * v_adj**2)
        )
        # Simplification for T=maturity
        r_adj = 0.5 * (params.risk_free_rate - 0.5 * sig_sq + sig_sq / 6.0)

        # More precise Kemna-Vorst adjustment
        b = params.risk_free_rate - 0.5 * params.volatility**2
        sigma_a = params.volatility / np.sqrt(3.0)
        mu_a = 0.5 * (b + 0.5 * sigma_a**2)

        adj_params = params.model_copy(
            update={
                "volatility": sigma_a,
                "risk_free_rate": params.risk_free_rate,  # We use the effective discount rate r, but adjusted drift
            }
        )
        # Standard BS with adjusted mu
        d1 = (
            np.log(params.underlying_price / params.strike_price)
            + (mu_a + 0.5 * sigma_a**2) * params.maturity_years
        ) / (sigma_a * np.sqrt(params.maturity_years))
        d2 = d1 - sigma_a * np.sqrt(params.maturity_years)

        exp_rt = np.exp(-params.risk_free_rate * params.maturity_years)
        if params.option_type == "call":
            price = params.underlying_price * np.exp(
                (mu_a - params.risk_free_rate) * params.maturity_years
            ) * norm.cdf(d1) - params.strike_price * exp_rt * norm.cdf(d2)
        else:
            price = params.strike_price * exp_rt * norm.cdf(-d2) - params.underlying_price * np.exp(
                (mu_a - params.risk_free_rate) * params.maturity_years
            ) * norm.cdf(-d1)

        return PriceResult(
            method_type="analytical_asian",
            computed_price=float(price),
            exec_seconds=time.time() - start_time,
        )

    def implied_volatility(
        self, target_price: float, params: OptionParams, max_iter: int = 100, tol: float = 1e-6
    ) -> float:
        """Newton-Raphson for Implied Volatility."""
        if target_price <= 0:
            return 0.0

        # Initial guess (Brenner-Subrahmanyam)
        sigma = np.sqrt(2 * np.pi / params.maturity_years) * (
            target_price / params.underlying_price
        )

        for _ in range(max_iter):
            curr_params = params.model_copy(update={"volatility": max(0.0001, sigma)})
            res = self.price(curr_params)
            diff = res.computed_price - target_price
            if abs(diff) < tol:
                return sigma
            if abs(res.vega) < 1e-8:
                break
            sigma -= diff / res.vega

        return sigma if sigma > 0 else 0.0

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
