"""API router for option pricing."""
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from src.methods.base import OptionParameters, PricingResult, BasePricingMethod
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson
from src.auth.dependencies import get_current_user
from src.cache.decorators import cache_response
import structlog

router = APIRouter(prefix="/api/v1/pricing", tags=["pricing"])
logger = structlog.get_logger(__name__)

@router.post("/compute", response_model=PricingResult)
@cache_response("price", ttl_seconds=300)
async def compute_price(
    params: OptionParameters,
    method: str = "analytical",
    current_user: dict[str, Any] = Depends(get_current_user)
) -> PricingResult:
    """Compute option price using the specified method."""
    logger.info("compute_price_request", method=method, user_id=current_user.get("id"))
    
    solver: BasePricingMethod
    if method == "analytical":
        solver = BlackScholesAnalytical()
    elif method == "crank_nicolson":
        solver = CrankNicolson()
    elif method == "quasi_mc":
        solver = QuasiMC()
    elif method == "binomial_crr_richardson":
        solver = BinomialCRRRichardson()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
    return solver.price(params)

# Force rebuild to resolve forward refs during collection
OptionParameters.model_rebuild()
PricingResult.model_rebuild()
