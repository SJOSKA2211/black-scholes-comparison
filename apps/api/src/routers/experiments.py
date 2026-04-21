from fastapi import APIRouter, Depends, Query
from typing import Optional
from src.database import repository
from src.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/experiments")
async def list_experiments(
    method_type: Optional[str] = None,
    market_source: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Returns a paginated list of experiment results."""
    return await repository.get_experiments(
        method_type=method_type,
        market_source=market_source,
        page=page,
        page_size=page_size
    )

@router.get("/experiments/{id}")
async def get_experiment(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """Returns a single experiment result with full parameter set."""
    # This would call a repo function get_experiment_by_id
    pass
