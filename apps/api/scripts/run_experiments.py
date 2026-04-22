"""Grid experiment runner — executes numerical methods across a parameter space."""

from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
import structlog
from joblib import Parallel, delayed

from src.database import repository
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.finite_difference.implicit import ImplicitFDM
from src.methods.finite_difference.crank_nicolson import CrankNicolsonFDM
from src.methods.monte_carlo.standard import StandardMC
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.trinomial import TrinomialTree
from src.methods.tree_methods.richardson import BinomialCRRRickardson, TrinomialRichardson
from src.metrics import (
    EXPERIMENTS_RUN_TOTAL,
    EXPERIMENT_GRID_PROGRESS,
    EXPERIMENT_ERRORS_TOTAL,
)

logger = structlog.get_logger(__name__)


def compute_single_experiment(method_name: str, params: OptionParams) -> Any:
    """
    Worker function for parallel execution.
    Instantiates the appropriate pricer family and executes the specific method.
    """
    try:
        if method_name == "analytical":
            res = BlackScholesAnalytical().price(params)
        elif method_name == "explicit_fdm":
            res = ExplicitFDM().price(params)
        elif method_name == "implicit_fdm":
            res = ImplicitFDM().price(params)
        elif method_name == "crank_nicolson":
            res = CrankNicolsonFDM().price(params)
        elif method_name == "standard_mc":
            res = StandardMC().price(params)
        elif method_name == "antithetic_mc":
            res = AntitheticMC().price(params)
        elif method_name == "control_variate_mc":
            res = ControlVariateMC().price(params)
        elif method_name == "quasi_mc":
            res = QuasiMC().price(params)
        elif method_name == "binomial_crr":
            res = BinomialCRR().price(params)
        elif method_name == "trinomial":
            res = TrinomialTree().price(params)
        elif method_name == "binomial_crr_richardson":
            res = BinomialCRRRickardson().price(params)
        elif method_name == "trinomial_richardson":
            res = TrinomialRichardson().price(params)
        else:
            raise ValueError(f"Unknown method type: {method_name}")

        EXPERIMENTS_RUN_TOTAL.labels(method_type=method_name, market_source=params.market_source).inc()
        return res
    except Exception as e:
        logger.warning("worker_task_failed", method=method_name, error=str(e))
        EXPERIMENT_ERRORS_TOTAL.labels(method_type=method_name, error_type=type(e).__name__).inc()
        return {"method": method_name, "error": str(e), "params": params.__dict__}


async def run_experiments(payload: dict[str, Any]) -> None:
    """
    Main entry point for the consumer.
    Processes a payload and runs experiments in parallel.
    """
    logger.info("experiment_run_started", payload=payload)
    
    # Extract params from payload or use defaults
    underlying_prices = payload.get("underlying_prices", [90, 100, 110])
    volatilities = payload.get("volatilities", [0.1, 0.2, 0.3])
    maturities = payload.get("maturities", [0.25, 0.5, 1.0])
    methods = payload.get("methods", [
        "analytical", "explicit_fdm", "implicit_fdm", "crank_nicolson",
        "standard_mc", "antithetic_mc", "control_variate_mc", "quasi_mc",
        "binomial_crr", "trinomial", "binomial_crr_richardson", "trinomial_richardson"
    ])
    
    tasks = []
    for s in underlying_prices:
        for v in volatilities:
            for t in maturities:
                params = OptionParams(
                    underlying_price=s,
                    strike_price=payload.get("strike_price", 100),
                    maturity_years=t,
                    volatility=v,
                    risk_free_rate=payload.get("risk_free_rate", 0.05),
                    option_type=payload.get("option_type", "call"),
                    market_source=payload.get("market_source", "synthetic")
                )
                for m in methods:
                    tasks.append((m, params))
    
    total_tasks = len(tasks)
    EXPERIMENT_GRID_PROGRESS.set(0.0)

    # Run in parallel across all CPU cores
    # Note: Joblib handles the process pool
    results = Parallel(n_jobs=-1)(
        delayed(compute_single_experiment)(m, p) for m, p in tasks
    )
    
    EXPERIMENT_GRID_PROGRESS.set(1.0)

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
            
    logger.info("experiment_run_completed", 
                total_tasks=total_tasks, 
                success_count=success_count)


async def run_grid() -> None:
    """Legacy entry point for backward compatibility."""
    await run_experiments({})


if __name__ == "__main__":
    asyncio.run(run_grid())
