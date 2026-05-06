"""Black-Scholes analytical closed-form solution."""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from src.methods.base import BasePricingMethod, OptionParameters, OptionType


class BlackScholesAnalytical(BasePricingMethod):
    """Analytical Black-Scholes solver."""

    def __init__(self) -> None:
        super().__init__("analytical")

    def _compute(self, params: OptionParameters) -> float:
        """Standard Black-Scholes formula."""
        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        volatility = params.volatility
        risk_free_rate = params.risk_free_rate

        d1_term = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        d2_term = d1_term - volatility * np.sqrt(maturity_years)

        if params.option_type == OptionType.CALL:
            price = underlying_price * norm.cdf(d1_term) - strike_price * np.exp(
                -risk_free_rate * maturity_years
            ) * norm.cdf(d2_term)
        else:
            price = strike_price * np.exp(-risk_free_rate * maturity_years) * norm.cdf(
                -d2_term
            ) - underlying_price * norm.cdf(-d1_term)

        return float(price)

    def calculate_greeks(self, params: OptionParameters) -> dict[str, float]:
        """Calculate Delta, Gamma, Vega, Theta, Rho."""
        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        volatility = params.volatility
        risk_free_rate = params.risk_free_rate

        d1_term = (
            np.log(underlying_price / strike_price)
            + (risk_free_rate + 0.5 * volatility**2) * maturity_years
        ) / (volatility * np.sqrt(maturity_years))
        d2_term = d1_term - volatility * np.sqrt(maturity_years)

        pdf_d1 = norm.pdf(d1_term)
        cdf_d1 = norm.cdf(d1_term)
        cdf_d2 = norm.cdf(d2_term)

        if params.option_type == OptionType.CALL:
            delta = cdf_d1
            rho = strike_price * maturity_years * np.exp(-risk_free_rate * maturity_years) * cdf_d2
            theta = (
                -(underlying_price * pdf_d1 * volatility) / (2 * np.sqrt(maturity_years))
                - risk_free_rate * strike_price * np.exp(-risk_free_rate * maturity_years) * cdf_d2
            )
        else:
            delta = cdf_d1 - 1
            rho = (
                -strike_price
                * maturity_years
                * np.exp(-risk_free_rate * maturity_years)
                * norm.cdf(-d2_term)
            )
            theta = -(underlying_price * pdf_d1 * volatility) / (
                2 * np.sqrt(maturity_years)
            ) + risk_free_rate * strike_price * np.exp(-risk_free_rate * maturity_years) * norm.cdf(
                -d2_term
            )

        gamma = pdf_d1 / (underlying_price * volatility * np.sqrt(maturity_years))
        vega = underlying_price * pdf_d1 * np.sqrt(maturity_years)

        return {
            "delta": float(delta),
            "gamma": float(gamma),
            "vega": float(vega),
            "theta": float(theta),
            "rho": float(rho),
        }

    def implied_volatility(self, market_price: float, params: OptionParameters) -> float:
        """Invert Black-Scholes to find implied volatility using Brent's method."""

        def objective(vol_candidate: float) -> float:
            test_params = params.model_copy(update={"volatility": vol_candidate})
            return self._compute(test_params) - market_price

        try:
            return float(brentq(objective, 1e-6, 5.0))
        except ValueError:
            return 0.0
