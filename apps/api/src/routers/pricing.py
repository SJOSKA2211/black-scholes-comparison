"""Router for real-time option pricing."""

from __future__ import annotations

import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_user
from src.cache.decorators import cache_response
from src.database.repository import upsert_option_parameters, upsert_price_result
from src.methods import (
    MethodType,
    OptionParams,
    get_method_instance,
)

router = APIRouter(prefix="/pricing", tags=["Pricing"])
logger = structlog.get_logger(__name__)


@router.get("/methods")
async def list_methods() -> list[str]:
    """Return a list of all supported pricing method types."""
    return [m.value for m in MethodType]


@router.post("/calculate")
@cache_response(key_prefix="price", ttl_seconds=300)
async def calculate_price(
    params: OptionParams,
    method_type: MethodType,
    persist: bool = False,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Compute option price using the specified numerical method.
    If persist=true, saves parameters and result to Supabase.
    """
    start_time = time.perf_counter()
    try:
        engine = get_method_instance(method_type)
        result = engine.price(params)
        exec_seconds = time.perf_counter() - start_time

        response_data = result.model_dump()
        response_data["exec_seconds"] = exec_seconds

        if persist:
            option_id = await upsert_option_parameters(params.model_dump())
            await upsert_price_result(option_id, response_data, user_id=current_user.get("id"))

        logger.info(
            "pricing_completed",
            method=method_type.value,
            price=result.computed_price,
            duration=exec_seconds,
            persist=persist,
        )
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("pricing_failed", method=method_type.value, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pricing calculation failed",
        )


@router.post("/compare")
async def compare_methods(
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Compare multiple pricing methods against the analytical reference.
    Payload: {"params": {...}, "methods": ["method1", "method2"]}
    """
    params_dict = payload.get("params")
    methods = payload.get("methods", [])
    
    if not params_dict or not methods:
        raise HTTPException(status_code=400, detail="Missing params or methods")
    
    params = OptionParams(**params_dict)
    
    # Get analytical reference first
    analytical_engine = get_method_instance(MethodType.ANALYTICAL)
    ref_result = analytical_engine.price(params)
    ref_price = ref_result.computed_price
    
    results = []
    for m_str in methods:
        try:
            m_type = MethodType(m_str)
            engine = get_method_instance(m_type)
            res = engine.price(params)
            
            res_dict = res.model_dump()
            res_dict["abs_error"] = abs(res.computed_price - ref_price)
            res_dict["pct_error"] = (res_dict["abs_error"] / ref_price) * 100 if ref_price != 0 else 0
            results.append(res_dict)
        except Exception as e:
            logger.warning("comparison_method_failed", method=m_str, error=str(e))
            
    return {
        "analytical_reference": ref_price,
        "results": results,
        "params": params.model_dump()
    }
