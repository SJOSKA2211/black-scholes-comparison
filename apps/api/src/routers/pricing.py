from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from src.methods.base import OptionParams, PriceResult, MethodType
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference import FiniteDifferenceMethods
from src.methods.monte_carlo import MonteCarloMethods
from src.methods.trees import TreeMethods
from src.auth.dependencies import get_current_user
import time

router = APIRouter()

class PriceRequest(BaseModel):
    params: OptionParams
    methods: List[MethodType]

class PriceResponse(BaseModel):
    results: List[PriceResult]
    analytical_reference: float
    exec_ms: float

@router.post("/price", response_model=PriceResponse)
async def price_options(
    request: PriceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Prices options using requested numerical methods.
    Protected by JWT validation.
    """
    start_time = time.time()
    
    analytical = BlackScholesAnalytical()
    fdm = FiniteDifferenceMethods()
    mc = MonteCarloMethods()
    trees = TreeMethods()
    
    results = []
    
    # Analytical reference always computed
    ref_res = analytical.price(request.params)
    
    for method in request.methods:
        if method == "analytical":
            results.append(ref_res)
        elif method == "explicit_fdm":
            results.append(fdm.explicit_fdm(request.params))
        elif method == "implicit_fdm":
            results.append(fdm.implicit_fdm(request.params))
        elif method == "crank_nicolson":
            results.append(fdm.crank_nicolson(request.params))
        elif method == "standard_mc":
            results.append(mc.standard_mc(request.params))
        elif method == "antithetic_mc":
            results.append(mc.antithetic_mc(request.params))
        elif method == "control_variate_mc":
            results.append(mc.control_variate_mc(request.params))
        elif method == "quasi_mc":
            results.append(mc.quasi_mc(request.params))
        elif method == "binomial_crr":
            results.append(trees.binomial_crr(request.params))
        elif method == "trinomial":
            results.append(trees.trinomial(request.params))
        elif method == "binomial_crr_richardson":
            results.append(trees.binomial_crr_richardson(request.params))
        elif method == "trinomial_richardson":
            results.append(trees.trinomial_richardson(request.params))
            
    exec_ms = (time.time() - start_time) * 1000
    
    return PriceResponse(
        results=results,
        analytical_reference=ref_res.computed_price,
        exec_ms=exec_ms
    )

@router.get("/methods")
async def get_methods():
    """Returns list of available numerical methods with metadata."""
    return [
        {"id": "analytical", "name": "Black-Scholes Analytical", "convergence_order": "N/A", "stability_class": "Exact", "american_suitable": False},
        {"id": "explicit_fdm", "name": "Explicit FDM (FTCS)", "convergence_order": "O(dt + dS^2)", "stability_class": "Conditionally Stable", "american_suitable": False},
        {"id": "implicit_fdm", "name": "Implicit FDM (BTCS)", "convergence_order": "O(dt + dS^2)", "stability_class": "Unconditionally Stable", "american_suitable": False},
        {"id": "crank_nicolson", "name": "Crank-Nicolson FDM", "convergence_order": "O(dt^2 + dS^2)", "stability_class": "Unconditionally Stable", "american_suitable": False},
        {"id": "standard_mc", "name": "Standard Monte Carlo", "convergence_order": "O(N^-0.5)", "stability_class": "Stochastic", "american_suitable": False},
        {"id": "binomial_crr", "name": "Binomial CRR Tree", "convergence_order": "O(N^-1)", "stability_class": "Stable", "american_suitable": True},
        # ... and so on for all 12 methods
    ]
