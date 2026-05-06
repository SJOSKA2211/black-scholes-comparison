"""CRR Binomial Tree with Richardson Extrapolation."""

import time

from src.methods.base import NumericalMethod, OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import price_binomial_crr


class BinomialCRRRichardson(NumericalMethod):
    """
    CRR Binomial Tree with Richardson Extrapolation.
    Formula: 2 * price(2N) - price(N).
    Achieves O(N^-2) convergence.
    """

    async def price(self, params: OptionParams) -> PriceResult:
        start_time = time.perf_counter()

        num_steps_n = 500
        num_steps_2n = 1000

        price_n = price_binomial_crr(params, num_steps_n)
        price_2n = price_binomial_crr(params, num_steps_2n)

        # Richardson Extrapolation
        final_price = 2 * price_2n - price_n

        exec_time = time.perf_counter() - start_time
        return PriceResult(
            price=float(final_price),
            exec_seconds=exec_time,
            metadata={
                "price_n": price_n,
                "price_2n": price_2n,
                "n": num_steps_n,
                "two_n": num_steps_2n,
            },
        )
