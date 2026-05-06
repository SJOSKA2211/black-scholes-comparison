"""Numerical pricing methods for the Black-Scholes Research Platform."""
from __future__ import annotations
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import MethodType, OptionParams, NumericalMethod, PriceResult
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson

__all__ = [
    "MethodType",
    "OptionParams",
    "PriceResult",
    "NumericalMethod",
    "BlackScholesAnalytical",
    "CrankNicolson",
    "QuasiMC",
    "BinomialCRRRichardson",
]
