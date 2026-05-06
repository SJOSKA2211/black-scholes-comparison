"""Router for real-time option pricing."""
import time
from typing import Any
import structlog
from fastapi import APIRouter, HTTPException
from src.cache.decorators import cache_response
from src.methods import (
    MethodType,
    OptionParams,
    BlackScholesAnalytical,
    CrankNicolson,
    QuasiMC,
    BinomialCRRRichardson,
)

router = APIRouter(prefix="/pricing", tags=["Pricing"])
logger = structlog.get_logger(__name__)


@router.post("/price")
@cache_response(key_prefix="price", ttl_seconds=300)
async def price_option(params: OptionParams, method: MethodType) -> dict[str, Any]:
    """Compute option price using the specified numerical method."""
    start_time = time.perf_counter()
    try:
        engine = _get_method_engine(method)
        # NumericalMethod.price is sync in my current implementation to match tests
        result = engine.price(params)
        
        logger.info(
            "pricing_completed",
            method=method,
            price=result.computed_price,
            duration=time.perf_counter() - start_time,
        )
        return result.model_dump()
    except Exception as error:
        logger.error("pricing_failed", method=method, error=str(error))
        raise HTTPException(status_code=500, detail="Pricing calculation failed") from error


def _get_method_engine(method: MethodType) -> Any:
    """Factory to retrieve the implementation for a method type."""
    if method == MethodType.ANALYTICAL:
        return BlackScholesAnalytical()
    if method == MethodType.CRANK_NICOLSON:
        return CrankNicolson()
    if method == MethodType.QUASI_MC:
        return QuasiMC()
    if method == MethodType.BINOMIAL_CRR_RICHARDSON:
        return BinomialCRRRichardson()
    raise ValueError(f"Unsupported method: {method}")
