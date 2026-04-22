"""Richardson extrapolation for tree methods."""

from __future__ import annotations

from src.methods.base import OptionParams, PriceResult
from src.methods.tree_methods.binomial_crr import price_binomial_crr
from src.methods.tree_methods.trinomial import price_trinomial


def price_binomial_crr_richardson(params: OptionParams, num_steps: int = 500) -> PriceResult:
    """CRR with Richardson extrapolation: 2*V(2N) - V(N)."""
    res_n = price_binomial_crr(params, num_steps)
    res_2n = price_binomial_crr(params, 2 * num_steps)

    richardson_price = 2 * res_2n.computed_price - res_n.computed_price
    return PriceResult(
        method_type="binomial_crr_richardson",
        computed_price=float(richardson_price),
        exec_seconds=res_n.exec_seconds + res_2n.exec_seconds,
        parameter_set={
            "num_steps_base": num_steps,
            "price_n": res_n.computed_price,
            "price_2n": res_2n.computed_price,
        },
    )


def price_trinomial_richardson(params: OptionParams, num_steps: int = 500) -> PriceResult:
    """Trinomial with Richardson extrapolation: 2*V(2N) - V(N)."""
    res_n = price_trinomial(params, num_steps)
    res_2n = price_trinomial(params, 2 * num_steps)

    richardson_price = 2 * res_2n.computed_price - res_n.computed_price
    return PriceResult(
        method_type="trinomial_richardson",
        computed_price=float(richardson_price),
        exec_seconds=res_n.exec_seconds + res_2n.exec_seconds,
        parameter_set={
            "num_steps_base": num_steps,
            "price_n": res_n.computed_price,
            "price_2n": res_2n.computed_price,
        },
    )
