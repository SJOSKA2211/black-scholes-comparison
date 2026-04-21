import asyncio
import structlog
import numpy as np
from joblib import Parallel, delayed
from src.methods.base import OptionParams
from src.methods.analytical import BlackScholesAnalytical
from src.methods.finite_difference import ExplicitFDM, ImplicitFDM, CrankNicolsonFDM
from src.methods.monte_carlo import MonteCarloMethods
from src.methods.trees import TreeMethods
from src.database import repository

logger = structlog.get_logger(__name__)

def compute_single_experiment(method_name, params):
    """
    Worker function for parallel execution.
    Instantiates the appropriate pricer family and executes the specific method.
    """
    try:
        if method_name == "analytical":
            return BlackScholesAnalytical().price(params)
        
        # FDM Family
        if method_name == "explicit_fdm":
            return ExplicitFDM().price(params)
        if method_name == "implicit_fdm":
            return ImplicitFDM().price(params)
        if method_name == "crank_nicolson":
            return CrankNicolsonFDM().price(params)
            
        # Monte Carlo Family
        mc = MonteCarloMethods()
        if method_name == "standard_mc":
            return mc.standard_mc(params)
        if method_name == "antithetic_mc":
            return mc.antithetic_mc(params)
        if method_name == "control_variate_mc":
            return mc.control_variate_mc(params)
        if method_name == "quasi_mc":
            return mc.quasi_mc(params)
            
        # Tree Family
        trees = TreeMethods()
        if method_name == "binomial_crr":
            return trees.binomial_crr(params)
        if method_name == "trinomial":
            return trees.trinomial(params)
        if method_name == "binomial_crr_richardson":
            return trees.binomial_crr_richardson(params)
        if method_name == "trinomial_richardson":
            return trees.trinomial_richardson(params)
            
        raise ValueError(f"Unknown method type: {method_name}")
    except Exception as e:
        logger.warning("worker_task_failed", method=method_name, error=str(e))
        return {"method": method_name, "error": str(e)}

async def run_grid():
    """
    Main experiment grid runner.
    Generates a parameter space and executes all 12 methods in parallel.
    """
    logger.info("experiment_grid_started")
    
    # Define research parameter space
    underlying_prices = [90, 100, 110]
    volatilities = [0.1, 0.2, 0.3]
    maturities = [0.25, 0.5, 1.0]
    methods = [
        "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson",
        "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc",
        "binomial_crr", "trinomial", "binomial_crr_richardson", "trinomial_richardson"
    ]
    
    tasks = []
    for s in underlying_prices:
        for v in volatilities:
            for t in maturities:
                params = OptionParams(
                    underlying_price=s,
                    strike_price=100,
                    maturity_years=t,
                    volatility=v,
                    risk_free_rate=0.05,
                    option_type="call"
                )
                for m in methods:
                    tasks.append((m, params))
    
    # Run in parallel across all CPU cores
    results = Parallel(n_jobs=-1)(
        delayed(compute_single_experiment)(m, p) for m, p in tasks
    )
    
    # Persist successful results to Supabase
    success_count = 0
    for res in results:
        if not isinstance(res, dict) or "error" not in res:
            try:
                option_id = await repository.upsert_option_parameters(res.parameter_set)
                await repository.upsert_price_result(option_id, res)
                success_count += 1
            except Exception as db_err:
                logger.error("persistence_failed", error=str(db_err))
            
    logger.info("experiment_grid_completed", 
                total_tasks=len(results), 
                success_count=success_count)

if __name__ == "__main__":
    asyncio.run(run_grid())
