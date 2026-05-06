"""Numerical pricing methods for the Black-Scholes Research Platform."""

from __future__ import annotations

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import MethodType, NumericalMethod, OptionParams, PriceResult
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson


def get_method_instance(method_type: MethodType) -> NumericalMethod:
    """Factory function to return an instance of the requested pricing method."""
    if method_type == MethodType.ANALYTICAL:
        return BlackScholesAnalytical()
    if method_type == MethodType.CRANK_NICOLSON:
        return CrankNicolson()
    if method_type == MethodType.QUASI_MC:
        return QuasiMC()
    if method_type == MethodType.BINOMIAL_CRR_RICHARDSON:
        return BinomialCRRRichardson()
    raise ValueError(f"Unknown method type: {method_type}")


__all__ = [
    "MethodType",
    "OptionParams",
    "PriceResult",
    "NumericalMethod",
    "BlackScholesAnalytical",
    "CrankNicolson",
    "QuasiMC",
    "BinomialCRRRichardson",
    "get_method_instance",
]
