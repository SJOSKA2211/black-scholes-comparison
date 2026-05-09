"""Script to run grid experiments."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import structlog

from src.analysis.statistics import calculate_errors
from src.database.repository import (
    list_option_parameters,
    upsert_method_result,
    upsert_validation_metrics,
)
from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParameters, OptionType
from src.methods.finite_difference.crank_nicolson import CrankNicolson
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.tree_methods.richardson import BinomialCRRRichardson
from src.metrics import EXPERIMENT_PROGRESS, EXPERIMENTS_TOTAL, PRICE_MAPE_GAUGE
from src.queue.publisher import publish_experiment_task

logger = structlog.get_logger(__name__)


async def run_experiments(payload: dict[str, Any]) -> None:
    """Run experiments based on the payload (actual execution)."""
    logger.info("experiments_execution_started", payload=payload)

    market = payload.get("params", {}).get("market")

    # Fetch real scraped data from the database
    db_params = await list_option_parameters(limit=100, market=market)
    if not db_params:
        logger.warning("no_option_parameters_found_in_db")
        return

    engines = [
        BlackScholesAnalytical(),
        CrankNicolson(),
        QuasiMC(),
        BinomialCRRRichardson(),
    ]

    total_steps = len(db_params) * len(engines)
    completed_steps = 0

    for row in db_params:
        option_id = row["id"]
        try:
            params = OptionParameters(
                underlying_price=row["underlying_price"],
                strike_price=row["strike_price"],
                maturity_years=row["maturity_years"],
                volatility=row["volatility"],
                risk_free_rate=row["risk_free_rate"],
                option_type=OptionType(row["option_type"]),
                is_american=row.get("is_american", False),
            )
        except Exception as e:
            logger.error("invalid_option_parameters", option_id=option_id, error=str(e))
            continue

        analytical_price = None
        method_results_map = {}

        for engine in engines:
            try:
                price_result = engine.price(params)
                completed_steps += 1
                EXPERIMENT_PROGRESS.set(completed_steps / total_steps)
                EXPERIMENTS_TOTAL.labels(
                    method_type=engine.method_name, market_source=market or "all"
                ).inc()

                # Create a parameter hash to ensure uniqueness
                param_hash_str = json.dumps(price_result.parameter_set, sort_keys=True)
                param_hash = hashlib.md5(param_hash_str.encode()).hexdigest()  # noqa: S324

                result_row = {
                    "option_id": option_id,
                    "method_type": price_result.method_type,
                    "parameter_set": price_result.parameter_set,
                    "parameter_hash": param_hash,
                    "computed_price": price_result.computed_price,
                    "exec_seconds": price_result.exec_seconds,
                    "converged": price_result.converged,
                    "replications": price_result.replications,
                }

                # Save individual result to get the ID back for validation_metrics
                res = await upsert_method_result(result_row)
                method_result_id = res[0]["id"]
                method_results_map[engine.method_name] = {
                    "id": method_result_id,
                    "price": price_result.computed_price,
                }

                if engine.method_name == "analytical":
                    analytical_price = price_result.computed_price

                logger.info(
                    "experiment_step_completed",
                    option_id=option_id,
                    method=engine.method_name,
                    price=price_result.computed_price,
                )
            except Exception as e:
                logger.error(
                    "experiment_step_failed",
                    option_id=option_id,
                    method=engine.method_name,
                    error=str(e),
                )

        # ── Calculate and Save Validation Metrics ──────────────────────
        if analytical_price is not None:
            for method_name, result_info in method_results_map.items():
                if method_name == "analytical":
                    continue

                errors = calculate_errors(analytical_price, result_info["price"])
                val_metrics = {
                    "option_id": option_id,
                    "method_result_id": result_info["id"],
                    "absolute_error": errors["absolute_error"],
                    "relative_pct_error": errors["relative_pct_error"],
                    "mape": errors["relative_pct_error"],  # For single row, MAPE = Rel Error
                }
                try:
                    await upsert_validation_metrics(val_metrics)
                    PRICE_MAPE_GAUGE.labels(method_type=method_name).set(
                        errors["relative_pct_error"]
                    )
                except Exception as e:
                    logger.error("validation_metrics_save_failed", error=str(e))

    logger.info("experiments_execution_finished")


async def main() -> None:
    """CLI entry point for running a default experiment set."""
    # This matches the sample payload from the dashboard
    default_payload = {"user_id": None, "params": {"market": "spy"}}
    await run_experiments(default_payload)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
