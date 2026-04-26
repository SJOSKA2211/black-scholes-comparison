"""Pricing router — handles individual and grid pricing requests."""

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.auth.dependencies import get_current_user
from src.cache.decorators import cache_response
from src.database.repository import upsert_option_parameters, upsert_price_result
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import MethodMetadata, MethodType, NumericalMethod, OptionParams, PriceResult
from src.methods.finite_difference.crank_nicolson import CrankNicolsonFDM
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.finite_difference.implicit import ImplicitFDM
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.monte_carlo.standard import StandardMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson, TrinomialRichardson
from src.methods.tree_methods.trinomial import TrinomialTree

router = APIRouter(prefix="/pricing", tags=["Pricing"])
logger = structlog.get_logger(__name__)


class CompareRequest(BaseModel):
    params: OptionParams
    methods: list[MethodType]
    persist: bool = False


class CompareResponse(BaseModel):
    results: list[PriceResult]
    analytical_reference: float
    exec_ms: float


@router.get("/methods", response_model=list[MethodMetadata])
async def list_methods(user: dict[str, Any] = Depends(get_current_user)) -> list[MethodMetadata]:
    """Returns metadata for all supported numerical methods."""
    return [
        MethodMetadata(
            id="analytical",
            name="Black-Scholes Analytical",
            complexity="O(1)",
            type="Exact",
            convergence_rate="Infinite",
        ),
        MethodMetadata(
            id="explicit_fdm",
            name="Explicit Finite Difference",
            complexity="O(N_s * N_t)",
            type="FDM",
            convergence_rate="O(dt + dx^2)",
        ),
        MethodMetadata(
            id="implicit_fdm",
            name="Implicit Finite Difference",
            complexity="O(N_s * N_t)",
            type="FDM",
            convergence_rate="O(dt + dx^2)",
        ),
        MethodMetadata(
            id="crank_nicolson",
            name="Crank-Nicolson FDM",
            complexity="O(N_s * N_t)",
            type="FDM",
            convergence_rate="O(dt^2 + dx^2)",
        ),
        MethodMetadata(
            id="standard_mc",
            name="Standard Monte Carlo",
            complexity="O(N_sim)",
            type="Monte Carlo",
            convergence_rate="O(N^-0.5)",
        ),
        MethodMetadata(
            id="antithetic_mc",
            name="Antithetic Monte Carlo",
            complexity="O(N_sim)",
            type="Monte Carlo",
            convergence_rate="O(N^-0.5)",
        ),
        MethodMetadata(
            id="control_variate_mc",
            name="Control Variate MC",
            complexity="O(N_sim)",
            type="Monte Carlo",
            convergence_rate="O(N^-0.5)",
        ),
        MethodMetadata(
            id="quasi_mc",
            name="Quasi-Monte Carlo",
            complexity="O(N_sim)",
            type="Monte Carlo",
            convergence_rate="O(N^-1)",
        ),
        MethodMetadata(
            id="binomial_crr",
            name="Binomial CRR",
            complexity="O(N^2)",
            type="Tree",
            convergence_rate="O(N^-1)",
        ),
        MethodMetadata(
            id="binomial_crr_richardson",
            name="Binomial + Richardson",
            complexity="O(N^2)",
            type="Tree",
            convergence_rate="O(N^-2)",
        ),
        MethodMetadata(
            id="trinomial",
            name="Trinomial Tree",
            complexity="O(N^2)",
            type="Tree",
            convergence_rate="O(N^-2)",
        ),
        MethodMetadata(
            id="trinomial_richardson",
            name="Trinomial + Richardson",
            complexity="O(N^2)",
            type="Tree",
            convergence_rate="O(N^-4)",
        ),
    ]


def get_method_instance(method_type: MethodType) -> NumericalMethod:
    """Factory to return an instance of the requested numerical method."""
    if method_type == "analytical":
        return BlackScholesAnalytical()
    elif method_type == "explicit_fdm":
        return ExplicitFDM()
    elif method_type == "implicit_fdm":
        return ImplicitFDM()
    elif method_type == "crank_nicolson":
        return CrankNicolsonFDM()
    elif method_type == "standard_mc":
        return StandardMC()
    elif method_type == "antithetic_mc":
        return AntitheticMC()
    elif method_type == "control_variate_mc":
        return ControlVariateMC()
    elif method_type == "quasi_mc":
        return QuasiMC()
    elif method_type == "binomial_crr":
        return BinomialCRR()
    elif method_type == "binomial_crr_richardson":
        return BinomialCRRRichardson()
    elif method_type == "trinomial":
        return TrinomialTree()
    elif method_type == "trinomial_richardson":
        return TrinomialRichardson()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {method_type}")


@router.post("/calculate", response_model=PriceResult)
@cache_response(key_prefix="price", ttl_seconds=3600)
async def calculate_price(
    params: OptionParams,
    method_type: MethodType = Query(..., description="Numerical method to use"),
    persist: bool = Query(False, description="Whether to save the result to database"),
    user: dict[str, Any] = Depends(get_current_user),
) -> PriceResult:
    """
    Compute the price of an option using the specified numerical method.
    Optionally persists the parameters and result to Supabase.
    """
    try:
        method = get_method_instance(method_type)

        from src.metrics import PRICE_COMPUTATIONS_TOTAL, PRICE_DURATION_SECONDS

        start_time = asyncio.get_event_loop().time()
        # Run in thread pool to avoid blocking async loop for heavy computations
        result = await asyncio.to_thread(method.price, params)
        duration = asyncio.get_event_loop().time() - start_time

        # Metrics
        PRICE_COMPUTATIONS_TOTAL.labels(
            method_type=method_type,
            option_type=params.option_type,
            converged=str(result.converged),
        ).inc()
        PRICE_DURATION_SECONDS.labels(method_type=method_type).observe(duration)

        if persist:
            # Save params and result
            option_id = await upsert_option_parameters(params.model_dump(exclude={"market_source"}))
            await upsert_price_result(option_id, result)

        return result
    except Exception as error:
        logger.error(
            "pricing_calculation_failed", error=str(error), method=method_type, step="router"
        )
        raise HTTPException(status_code=500, detail="Pricing calculation failed") from error


@router.post("/compare", response_model=CompareResponse)
@router.post("/price", response_model=CompareResponse, include_in_schema=False)
@cache_response(key_prefix="compare", ttl_seconds=3600)
async def compare_methods(
    request: CompareRequest,
    user: dict[str, Any] = Depends(get_current_user),
) -> CompareResponse:
    """
    Compute prices using multiple methods for comparison.
    Analytical method is always included as a benchmark if not requested.
    """
    params = request.params
    methods = request.methods

    if "analytical" not in methods:
        methods.append("analytical")

    try:
        import time

        start_time = time.perf_counter()

        tasks = []
        for m_type in methods:
            method = get_method_instance(m_type)
            tasks.append(asyncio.to_thread(method.price, params))

        results_list = await asyncio.gather(*tasks)

        # Find analytical reference
        analytical_ref = 0.0
        for res in results_list:
            if res.method_type == "analytical":
                analytical_ref = res.computed_price
                break

        exec_ms = (time.perf_counter() - start_time) * 1000

        if request.persist:
            # Save parameters once
            option_id = await upsert_option_parameters(params.model_dump())
            # Save each result in the experiments table
            for res in results_list:
                await upsert_price_result(option_id, res, user_id=user.get("id"))

        return CompareResponse(
            results=results_list, analytical_reference=analytical_ref, exec_ms=exec_ms
        )
    except Exception as error:  # pragma: no cover
        logger.error("pricing_comparison_failed", error=str(error), step="router")
        raise HTTPException(status_code=500, detail="Pricing comparison failed") from error
