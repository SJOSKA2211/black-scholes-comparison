"""API router for option pricing requests."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.cache.decorators import cache_response
from src.database.repository import OptionRepository
from src.methods import (
    BinomialCRRRichardson,
    BlackScholesAnalytical,
    CrankNicolson,
    MethodType,
    OptionParams,
    QuasiMC,
)

router = APIRouter(prefix="/pricing", tags=["pricing"])
logger = structlog.get_logger(__name__)


@router.post("/price", response_model=dict)
@cache_response("price", 3600)
async def price_option(
    params: OptionParams,
    method: MethodType = MethodType.ANALYTICAL,
    repository: OptionRepository = Depends(OptionRepository),
) -> dict:
    """
    Price an option using the specified method.
    Stores the result in the database.
    """
    method_impl = {
        MethodType.ANALYTICAL: BlackScholesAnalytical(),
        MethodType.CRANK_NICOLSON: CrankNicolson(),
        MethodType.QUASI_MC: QuasiMC(),
        MethodType.BINOMIAL_CRR_RICHARDSON: BinomialCRRRichardson(),
    }.get(method)

    if not method_impl:
        raise HTTPException(status_code=400, detail="Unsupported pricing method")

    try:
        result = await method_impl.price(params)

        # Upsert params and insert result
        option_id = await repository.upsert_option_params(params.model_dump())
        await repository.insert_method_result(
            {
                "option_id": option_id,
                "method_type": method,
                "computed_price": result.price,
                "exec_seconds": result.exec_seconds,
                "converged": result.converged,
                "parameter_set": result.metadata,
            }
        )

        return {
            "price": result.price,
            "exec_seconds": result.exec_seconds,
            "metadata": result.metadata,
            "method": method,
        }
    except Exception as e:
        logger.error("pricing_request_failed", method=method, error=str(e))
        raise HTTPException(status_code=500, detail="Internal pricing error") from e
