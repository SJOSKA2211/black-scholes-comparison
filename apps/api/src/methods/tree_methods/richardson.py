"""Richardson extrapolation for Binomial CRR."""

from __future__ import annotations

import time

from src.methods.base import BasePricingMethod, OptionParameters, PricingResult
from src.methods.tree_methods.binomial_crr import BinomialCRR


class BinomialCRRRichardson(BasePricingMethod):
    """Richardson extrapolation on CRR binomial trees."""

    def __init__(self, steps: int = 500) -> None:
        super().__init__("binomial_crr_richardson")
        self.steps = steps

    def _compute(self, params: OptionParameters) -> float:
        """
        Execute Richardson extrapolation: 2 * price(2n) - price(n).
        Note: This method is a wrapper around two BinomialCRR runs.
        """
        # This will be called by price(), but we need to override price()
        # to handle the two steps and store metadata correctly.
        return 0.0

    def price(self, params: OptionParameters) -> PricingResult:
        """Override price to perform two-step extrapolation."""
        start_time = time.perf_counter()

        crr_n = BinomialCRR(steps=self.steps)
        crr_2n = BinomialCRR(steps=2 * self.steps)

        price_n = crr_n._compute(params)
        price_2n = crr_2n._compute(params)

        extrapolated_price = 2 * price_2n - price_n
        duration = time.perf_counter() - start_time

        # Metadata storage
        parameter_set = params.model_dump()
        parameter_set["price_n"] = price_n
        parameter_set["price_2n"] = price_2n
        parameter_set["steps"] = self.steps

        return PricingResult(
            computed_price=float(extrapolated_price),
            exec_seconds=duration,
            method_type=self.method_name,
            parameter_set=parameter_set,
        )
