import math
import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import MethodType, OptionParams, PriceResult
from src.methods.finite_difference.crank_nicolson import price_crank_nicolson

# Modular imports for v4
from src.methods.finite_difference.explicit import price_explicit_fdm
from src.methods.finite_difference.implicit import price_implicit_fdm
from src.methods.monte_carlo.antithetic import price_antithetic_mc
from src.methods.monte_carlo.control_variates import price_control_variate_mc
from src.methods.monte_carlo.quasi_mc import price_quasi_mc
from src.methods.monte_carlo.standard import price_standard_mc
from src.methods.tree_methods.binomial_crr import price_binomial_crr
from src.methods.tree_methods.richardson import (
    price_binomial_crr_richardson,
    price_trinomial_richardson,
)
from src.methods.tree_methods.trinomial import price_trinomial
from src.metrics import (
    PRICE_COMPUTATION_DURATION_SECONDS,
    PRICE_COMPUTATIONS_TOTAL,
    PRICE_MAPE_GAUGE,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


class PriceRequest(BaseModel):
    params: OptionParams
    methods: list[MethodType]


class PriceResponse(BaseModel):
    results: list[PriceResult]
    analytical_reference: float
    exec_ms: float


# Registry of pricer functions
analytical_engine = BlackScholesAnalytical()

METHOD_MAP = {
    "analytical": analytical_engine.price,
    "explicit_fdm": price_explicit_fdm,
    "implicit_fdm": price_implicit_fdm,
    "crank_nicolson": price_crank_nicolson,
    "standard_mc": price_standard_mc,
    "antithetic_mc": price_antithetic_mc,
    "control_variate_mc": price_control_variate_mc,
    "quasi_mc": price_quasi_mc,
    "binomial_crr": price_binomial_crr,
    "trinomial": price_trinomial,
    "binomial_crr_richardson": price_binomial_crr_richardson,
    "trinomial_richardson": price_trinomial_richardson,
}


@router.post("/price", response_model=PriceResponse)
async def price_options(
    request: PriceRequest, current_user: dict[str, Any] = Depends(get_current_user)
) -> PriceResponse:
    """
    Prices options using requested numerical methods.
    Instruments computations with Prometheus metrics.
    """
    try:
        start_time = time.time()

        # Analytical reference always computed for MAPE tracking
        ref_res = analytical_engine.price(request.params)
        analytical_price = ref_res.computed_price

        results = []

        for method_type in request.methods:
            if method_type not in METHOD_MAP:
                continue

            pricer_fn = METHOD_MAP[method_type]

            # Track duration
            with PRICE_COMPUTATION_DURATION_SECONDS.labels(method_type=method_type).time():
                result = pricer_fn(request.params)

            # Track total computations and convergence status
            converged_status = "True"
            if math.isnan(result.computed_price) or math.isinf(result.computed_price):
                converged_status = "False"

            PRICE_COMPUTATIONS_TOTAL.labels(
                method_type=method_type,
                option_type=request.params.option_type,
                converged=converged_status,
            ).inc()

            # Track MAPE if converged
            if converged_status == "True" and analytical_price > 0:
                mape = abs(result.computed_price - analytical_price) / analytical_price * 100
                PRICE_MAPE_GAUGE.labels(method_type=method_type).set(mape)

            results.append(result)

        exec_ms = (time.time() - start_time) * 1000

        return PriceResponse(
            results=results, analytical_reference=analytical_price, exec_ms=exec_ms
        )
    except Exception as e:
        logger.error("pricing_failed", error=str(e), step="router")
        raise HTTPException(status_code=500, detail=f"Pricing computation failed: {e!s}") from e


@router.get("/methods", response_model=None)
async def get_methods() -> list[dict[str, Any]]:
    """Returns list of available numerical methods with metadata."""
    return [
        {
            "id": "analytical",
            "name": "Black-Scholes Analytical",
            "convergence_order": "Exact",
            "stability_class": "Exact",
            "american_suitable": False,
        },
        {
            "id": "explicit_fdm",
            "name": "Explicit FDM (FTCS)",
            "convergence_order": "1 (time), 2 (space)",
            "stability_class": "Conditional",
            "american_suitable": False,
        },
        {
            "id": "implicit_fdm",
            "name": "Implicit FDM (BTCS)",
            "convergence_order": "1 (time), 2 (space)",
            "stability_class": "Unconditional",
            "american_suitable": False,
        },
        {
            "id": "crank_nicolson",
            "name": "Crank-Nicolson FDM",
            "convergence_order": "2 (time), 2 (space)",
            "stability_class": "Unconditional",
            "american_suitable": False,
        },
        {
            "id": "standard_mc",
            "name": "Standard Monte Carlo",
            "convergence_order": "0.5",
            "stability_class": "Stochastic",
            "american_suitable": False,
        },
        {
            "id": "antithetic_mc",
            "name": "Antithetic Variates MC",
            "convergence_order": "0.5 (reduced var)",
            "stability_class": "Stochastic",
            "american_suitable": False,
        },
        {
            "id": "control_variate_mc",
            "name": "Control Variate MC",
            "convergence_order": "0.5 (high var red)",
            "stability_class": "Stochastic",
            "american_suitable": False,
        },
        {
            "id": "quasi_mc",
            "name": "Quasi-Monte Carlo (Sobol)",
            "convergence_order": "~1.0",
            "stability_class": "Deterministic",
            "american_suitable": False,
        },
        {
            "id": "binomial_crr",
            "name": "Binomial CRR Tree",
            "convergence_order": "1",
            "stability_class": "Stable",
            "american_suitable": True,
        },
        {
            "id": "trinomial",
            "name": "Trinomial Tree (Boyle)",
            "convergence_order": "1 (Smoother)",
            "stability_class": "Stable",
            "american_suitable": True,
        },
        {
            "id": "binomial_crr_richardson",
            "name": "Binomial + Richardson",
            "convergence_order": "2",
            "stability_class": "Stable",
            "american_suitable": True,
        },
        {
            "id": "trinomial_richardson",
            "name": "Trinomial + Richardson",
            "convergence_order": "2",
            "stability_class": "Stable",
            "american_suitable": True,
        },
    ]
