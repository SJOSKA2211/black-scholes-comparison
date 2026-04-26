"""Richardson extrapolation for tree methods."""

from __future__ import annotations

import time

from src.methods.base import MethodType, OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree


class BinomialCRRRichardson:
    """CRR with Richardson extrapolation wrapper with Greeks."""

    def __init__(self, num_steps: int = 500) -> None:
        self.num_steps = num_steps
        self.method_type: MethodType = "binomial_crr_richardson"

    def price(self, params: OptionParams) -> PriceResult:
        """CRR with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()

        pricer_base = BinomialCRR(num_steps=self.num_steps)
        pricer_refined = BinomialCRR(num_steps=2 * self.num_steps)

        result_base = pricer_base.price(params)
        result_refined = pricer_refined.price(params)

        def extrapolate(value_base: float, value_refined: float) -> float:
            return 2 * value_refined - value_base

        def extrapolate_greek(
            greek_base: float | None, greek_refined: float | None
        ) -> float | None:
            if greek_base is None or greek_refined is None:
                return None
            return 2 * greek_refined - greek_base

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrapolate(result_base.computed_price, result_refined.computed_price),
            exec_seconds=exec_seconds,
            delta=extrapolate_greek(result_base.delta, result_refined.delta),
            gamma=extrapolate_greek(result_base.gamma, result_refined.gamma),
            vega=extrapolate_greek(result_base.vega, result_refined.vega),
            theta=extrapolate_greek(result_base.theta, result_refined.theta),
            rho=extrapolate_greek(result_base.rho, result_refined.rho),
            parameter_set={
                "num_steps_base": self.num_steps,
            },
        )


class TrinomialRichardson:
    """Trinomial with Richardson extrapolation wrapper with Greeks."""

    def __init__(self, num_steps: int = 500) -> None:
        self.num_steps = num_steps
        self.method_type: MethodType = "trinomial_richardson"

    def price(self, params: OptionParams) -> PriceResult:
        """Trinomial with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()

        pricer_base = TrinomialTree(num_steps=self.num_steps)
        pricer_refined = TrinomialTree(num_steps=2 * self.num_steps)

        result_base = pricer_base.price(params)
        result_refined = pricer_refined.price(params)

        def extrapolate(value_base: float, value_refined: float) -> float:
            return 2 * value_refined - value_base

        def extrapolate_greek(
            greek_base: float | None, greek_refined: float | None
        ) -> float | None:
            if greek_base is None or greek_refined is None:
                return None
            return 2 * greek_refined - greek_base

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrapolate(result_base.computed_price, result_refined.computed_price),
            exec_seconds=exec_seconds,
            delta=extrapolate_greek(result_base.delta, result_refined.delta),
            gamma=extrapolate_greek(result_base.gamma, result_refined.gamma),
            vega=extrapolate_greek(result_base.vega, result_refined.vega),
            theta=extrapolate_greek(result_base.theta, result_refined.theta),
            rho=extrapolate_greek(result_base.rho, result_refined.rho),
            parameter_set={
                "num_steps_base": self.num_steps,
            },
        )
