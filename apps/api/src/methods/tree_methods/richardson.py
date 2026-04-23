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

        pricer_full = BinomialCRR(num_steps=self.num_steps)
        pricer_double = BinomialCRR(num_steps=2 * self.num_steps)

        res_f = pricer_full.price(params)
        res_d = pricer_double.price(params)

        def extrap(v_f: float, v_d: float) -> float:
            return 2 * v_d - v_f

        def extrap_g(v1: float | None, v2: float | None) -> float | None:
            if v1 is None or v2 is None:
                return None
            return 2 * v2 - v1

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrap(res_f.computed_price, res_d.computed_price),
            exec_seconds=exec_seconds,
            delta=extrap_g(res_f.delta, res_d.delta),
            gamma=extrap_g(res_f.gamma, res_d.gamma),
            vega=extrap_g(res_f.vega, res_d.vega),
            theta=extrap_g(res_f.theta, res_d.theta),
            rho=extrap_g(res_f.rho, res_d.rho),
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

        pricer_full = TrinomialTree(num_steps=self.num_steps)
        pricer_double = TrinomialTree(num_steps=2 * self.num_steps)

        res_f = pricer_full.price(params)
        res_d = pricer_double.price(params)

        def extrap(v_f: float, v_d: float) -> float:
            return 2 * v_d - v_f

        def extrap_g(v1: float | None, v2: float | None) -> float | None:
            if v1 is None or v2 is None:
                return None
            return 2 * v2 - v1

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrap(res_f.computed_price, res_d.computed_price),
            exec_seconds=exec_seconds,
            delta=extrap_g(res_f.delta, res_d.delta),
            gamma=extrap_g(res_f.gamma, res_d.gamma),
            vega=extrap_g(res_f.vega, res_d.vega),
            theta=extrap_g(res_f.theta, res_d.theta),
            rho=extrap_g(res_f.rho, res_d.rho),
            parameter_set={
                "num_steps_base": self.num_steps,
            },
        )
