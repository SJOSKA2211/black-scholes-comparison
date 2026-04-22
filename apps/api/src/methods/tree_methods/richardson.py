"""Richardson extrapolation for tree methods."""

from __future__ import annotations

import time

from src.methods.base import OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree


class BinomialCRRRickardson:
    """CRR with Richardson extrapolation wrapper."""

    def price(self, params: OptionParams, num_steps: int = 500) -> PriceResult:
        """CRR with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()
        pricer = BinomialCRR()
        res_n = pricer.price(params, num_steps)
        res_2n = pricer.price(params, 2 * num_steps)

        richardson_price = 2 * res_2n.computed_price - res_n.computed_price
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="binomial_crr_richardson",
            computed_price=float(richardson_price),
            exec_seconds=exec_seconds,
            parameter_set={
                "num_steps_base": num_steps,
                "price_n": res_n.computed_price,
                "price_2n": res_2n.computed_price,
            },
        )


class TrinomialRichardson:
    """Trinomial with Richardson extrapolation wrapper."""

    def price(self, params: OptionParams, num_steps: int = 500) -> PriceResult:
        """Trinomial with Richardson extrapolation: 2*V(2N) - V(N)."""
        start_time = time.time()
        pricer = TrinomialTree()
        res_n = pricer.price(params, num_steps)
        res_2n = pricer.price(params, 2 * num_steps)

        richardson_price = 2 * res_2n.computed_price - res_n.computed_price
        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="trinomial_richardson",
            computed_price=float(richardson_price),
            exec_seconds=exec_seconds,
            parameter_set={
                "num_steps_base": num_steps,
                "price_n": res_n.computed_price,
                "price_2n": res_2n.computed_price,
            },
        )
