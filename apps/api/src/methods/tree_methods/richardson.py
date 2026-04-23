"""Richardson extrapolation for tree methods."""

from __future__ import annotations

import time

from src.methods.base import MethodType, OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree


class BinomialCRRRichardson:
    """CRR with Richardson extrapolation wrapper."""

    def __init__(self, num_steps: int = 500) -> None:
        self.num_steps = num_steps
        self.method_type: MethodType = "binomial_crr_richardson"

    def price(self, params: OptionParams) -> PriceResult:
        """CRR with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()

        pricer_full = BinomialCRR(num_steps=self.num_steps)
        pricer_double = BinomialCRR(num_steps=2 * self.num_steps)

        result_full = pricer_full.price(params)
        result_double = pricer_double.price(params)

        richardson_price = 2 * result_double.computed_price - result_full.computed_price
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=float(richardson_price),
            exec_seconds=exec_seconds,
            parameter_set={
                "num_steps_base": self.num_steps,
                "price_base": result_full.computed_price,
                "price_double": result_double.computed_price,
            },
        )


class TrinomialRichardson:
    """Trinomial with Richardson extrapolation wrapper."""

    def __init__(self, num_steps: int = 500) -> None:
        self.num_steps = num_steps
        self.method_type: MethodType = "trinomial_richardson"

    def price(self, params: OptionParams) -> PriceResult:
        """Trinomial with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()

        pricer_full = TrinomialTree(num_steps=self.num_steps)
        pricer_double = TrinomialTree(num_steps=2 * self.num_steps)

        result_full = pricer_full.price(params)
        result_double = pricer_double.price(params)

        richardson_price = 2 * result_double.computed_price - result_full.computed_price
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=float(richardson_price),
            exec_seconds=exec_seconds,
            parameter_set={
                "num_steps_base": self.num_steps,
                "price_base": result_full.computed_price,
                "price_double": result_double.computed_price,
            },
        )
