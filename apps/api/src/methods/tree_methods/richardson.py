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

        def extrap(v_f, v_d):
            return 2 * v_d - v_f

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrap(res_f.computed_price, res_d.computed_price),
            exec_seconds=exec_seconds,
            delta=extrap(res_f.delta, res_d.delta) if res_f.delta is not None else None,
            gamma=extrap(res_f.gamma, res_d.gamma) if res_f.gamma is not None else None,
            vega=extrap(res_f.vega, res_d.vega) if res_f.vega is not None else None,
            theta=extrap(res_f.theta, res_d.theta) if res_f.theta is not None else None,
            rho=extrap(res_f.rho, res_d.rho) if res_f.rho is not None else None,
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

        def extrap(v_f, v_d):
            return 2 * v_d - v_f

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type=self.method_type,
            computed_price=extrap(res_f.computed_price, res_d.computed_price),
            exec_seconds=exec_seconds,
            delta=extrap(res_f.delta, res_d.delta) if res_f.delta is not None else None,
            gamma=extrap(res_f.gamma, res_d.gamma) if res_f.gamma is not None else None,
            vega=extrap(res_f.vega, res_d.vega) if res_f.vega is not None else None,
            theta=extrap(res_f.theta, res_d.theta) if res_f.theta is not None else None,
            rho=extrap(res_f.rho, res_d.rho) if res_f.rho is not None else None,
            parameter_set={
                "num_steps_base": self.num_steps,
            },
        )
