"""Router for option pricing computations."""

import time
from typing import Any

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.methods import get_method_instance
from src.methods.base import MethodType, OptionParams
from src.metrics import PRICE_COMPUTATIONS_TOTAL, PRICE_DURATION_SECONDS

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.post("/compute", response_model=dict)
async def compute_price(
    params: OptionParams,
    method: MethodType = MethodType.ANALYTICAL,
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Compute the price of an option using the specified method."""
    method_instance = get_method_instance(method)

    start_time = time.perf_counter()
    result = await method_instance.price(params)
    duration = time.perf_counter() - start_time

    # Update metrics
    PRICE_COMPUTATIONS_TOTAL.labels(
        method_type=method.value,
        option_type=params.option_type.value,
        converged=str(result.converged).lower(),
    ).inc()
    PRICE_DURATION_SECONDS.labels(method_type=method.value).observe(duration)

    return {
        "price": result.price,
        "exec_seconds": result.exec_seconds,
        "method": method.value,
        "params": params.model_dump(),
        "metadata": result.metadata,
    }
