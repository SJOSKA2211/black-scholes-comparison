"""Grid experiment runner — executes numerical methods across a parameter space."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from joblib import Parallel, delayed

from src.database import repository
from src.methods import (
    MethodType,
    OptionParams,
    PriceResult,
    BlackScholesAnalytical,
    CrankNicolson,
    QuasiMC,
    BinomialCRRRichardson,
)
from src.metrics import (
    EXPERIMENT_ERRORS,
    EXPERIMENT_PROGRESS,
    EXPERIMENTS_TOTAL,
)

logger = structlog.get_logger(__name__)


def compute_single_experiment(method_type: MethodType, params: OptionParams) -> tuple[Any, OptionParams]:
    """
    Worker function for parallel execution.
    Returns (PriceResult or error_dict, OptionParams).
    """
    try:
        if method_type == MethodType.ANALYTICAL:
            engine = BlackScholesAnalytical()
        elif method_type == MethodType.CRANK_NICOLSON:
            engine = CrankNicolson()
        elif method_type == MethodType.QUASI_MC:
            engine = QuasiMC()
        elif method_type == MethodType.BINOMIAL_CRR_RICHARDSON:
            engine = BinomialCRRRichardson()
        else:
            raise ValueError(f"Unsupported method: {method_type}")

        res = engine.price(params)
        EXPERIMENTS_TOTAL.labels(method_type=method_type, market_source=params.market_source).inc()
        return res, params
    except Exception as error:
        logger.warning("worker_task_failed", method=method_type, error=str(error))
        EXPER_ERROR_TYPE = type(error).__name__
        EXPERIMENT_ERRORS.labels(method_type=method_type, error_type=EXPER_ERROR_TYPE).inc()
        return {"method": method_type, "error": str(error), "params": params.model_dump()}, params


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
        MethodType.ANALYTICAL,
        MethodType.CRANK_NICOLSON,
        MethodType.QUASI_MC,
        MethodType.BINOMIAL_CRR_RICHARDSON,
    ])

    tasks = []
    for price_val in underlying_prices:
        for vol_val in volatilities:
            for mat_val in maturities:
                params = OptionParams(
                    underlying_price=price_val,
                    strike_price=payload.get("strike_price", 100),
                    maturity_years=mat_val,
                    volatility=vol_val,
                    risk_free_rate=payload.get("risk_free_rate", 0.05),
                    option_type=payload.get("option_type", "call"),
                    market_source=payload.get("market_source", "synthetic")
                )
                for method_type in methods:
                    tasks.append((method_type, params))

    total_tasks = len(tasks)
    if total_tasks == 0:
        logger.warning("no_tasks_to_run")
        return

    EXPERIMENT_PROGRESS.set(0.0)

    # Run in parallel across CPU cores
    # We use threading backend to avoid issues with pickling pydantic models if they are complex
    results = Parallel(n_jobs=4, backend="threading")(
        delayed(compute_single_experiment)(m, p) for m, p in tasks
    )

    EXPERIMENT_PROGRESS.set(1.0)

    success_count = 0
    for i, (res, orig_params) in enumerate(results):
        if i % 20 == 0:
            logger.info("persistence_progress", current=i, total=total_tasks)
        
        if isinstance(res, PriceResult):
            try:
                # 1. Store option parameters
                option_id = await repository.upsert_option_params(orig_params.model_dump())
                
                # 2. Store method result
                result_dict = {
                    "option_id": option_id,
                    "method_type": res.method_type,
                    "parameter_set": res.parameter_set,
                    "computed_price": res.computed_price,
                    "exec_seconds": res.exec_seconds,
                    "converged": True,
                    "replications": res.parameter_set.get("num_paths", res.parameter_set.get("num_steps", 1)),
                    "run_by": payload.get("user_id")
                }
                await repository.insert_method_result(result_dict)
                success_count += 1
            except Exception as db_error:
                logger.error("persistence_failed", error=str(db_error))

    logger.info("experiment_run_completed",
                total_tasks=total_tasks,
                success_count=success_count)


if __name__ == "__main__":
    # Test run
    asyncio.run(run_experiments({}))
