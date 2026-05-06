"""Binomial CRR with Richardson Extrapolation."""

from __future__ import annotations

import time

from src.methods.base import NumericalMethod, OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import BinomialCRR


class BinomialCRRRichardson(NumericalMethod):
    """
    Combines CRR binomial tree with Richardson extrapolation.
    2 * Price(2N) - Price(N) improves convergence to O(N^-2).
    """

    def price(self, params: OptionParams) -> PriceResult:
        """Compute the price using Richardson Extrapolation."""
        start_time = time.perf_counter()

        # Standard steps as per mandate
        num_steps_n = 500
        num_steps_2n = 1000

        tree = BinomialCRR()

        price_n = tree.price_tree(params, num_steps_n)
        price_2n = tree.price_tree(params, num_steps_2n)

        # Richardson Extrapolation
        final_price = 2.0 * price_2n - price_n

        return PriceResult(
            method_type="binomial_crr_richardson",
            computed_price=float(final_price),
            exec_seconds=time.perf_counter() - start_time,
            metadata={
                "price_n": price_n,
                "price_2n": price_2n,
                "num_steps_n": num_steps_n,
                "num_steps_2n": num_steps_2n,
            },
        )
