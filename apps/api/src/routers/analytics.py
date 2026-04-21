import structlog
from fastapi import APIRouter, Depends, Query

from src.analysis.convergence import ConvergenceAnalyzer
from src.analysis.statistics import Statistics
from src.auth.dependencies import get_current_user
from src.database import repository

router = APIRouter()
logger = structlog.get_logger(__name__)

# Singletons for analysis
stats_engine = Statistics()
convergence_engine = ConvergenceAnalyzer()


@router.get("/analytics/statistics")
async def get_statistics(current_user: dict = Depends(get_current_user)):
    """
    Returns ANOVA and Tukey HSD results for all pricing methods.
    Results are cached in memory for 5 minutes.
    """
    results = await repository.get_experiments(page_size=2000)
    data = results["items"]

    if not data:
        return {"message": "No experiment data available for analysis"}

    analysis = stats_engine.get_full_analysis(data)
    return analysis


@router.get("/analytics/convergence")
async def get_convergence(
    method_type: str = Query(..., description="Method to analyze"),
    current_user: dict = Depends(get_current_user),
):
    """
    Returns log-log regression data for convergence order estimation.
    """
    results = await repository.get_experiments_by_method(method_type)

    if not results:
        return {"message": f"No data found for method: {method_type}"}

    order, regression_data = convergence_engine.estimate_convergence_order(results)

    return {
        "method_type": method_type,
        "estimated_order": order,
        "regression_data": regression_data,
    }
