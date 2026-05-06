"""Repository layer for Supabase PostgreSQL operations."""

from __future__ import annotations

import time
import uuid
from typing import Any

import pandas as pd
import structlog

from src.database.supabase_client import get_supabase
from src.metrics import SUPABASE_ERRORS, SUPABASE_QUERY_DURATION

logger = structlog.get_logger(__name__)


class OptionRepository:
    """Handles all database interactions for option research data."""

    def __init__(self) -> None:
        self.client = get_supabase()

    async def upsert_option_params(self, params_dict: dict[str, Any]) -> str:
        """Upsert option parameters and return the record ID."""
        start_time = time.perf_counter()
        try:
            result = (
                self.client.table("option_parameters")
                .upsert(
                    params_dict,
                    on_conflict="underlying_price,strike_price,maturity_years,volatility,risk_free_rate,option_type,is_american",
                )
                .execute()
            )
            SUPABASE_QUERY_DURATION.labels(table="option_parameters", operation="upsert").observe(
                time.perf_counter() - start_time
            )
            return str(result.data[0]["id"])
        except Exception as e:
            SUPABASE_ERRORS.labels(table="option_parameters", operation="upsert").inc()
            logger.error("db_upsert_failed", table="option_parameters", error=str(e))
            raise

    async def insert_method_result(self, result_dict: dict[str, Any]) -> str:
        """Insert a pricing method result."""
        start_time = time.perf_counter()
        try:
            result = self.client.table("method_results").insert(result_dict).execute()
            SUPABASE_QUERY_DURATION.labels(table="method_results", operation="insert").observe(
                time.perf_counter() - start_time
            )
            return str(result.data[0]["id"])
        except Exception as e:
            SUPABASE_ERRORS.labels(table="method_results", operation="insert").inc()
            logger.error("db_insert_failed", table="method_results", error=str(e))
            raise

    async def upsert_market_data(self, df: pd.DataFrame, source: str) -> int:
        """Upsert multiple market data rows from a DataFrame."""
        start_time = time.perf_counter()
        records = df.to_dict(orient="records")
        try:
            result = (
                self.client.table("market_data")
                .upsert(records, on_conflict="option_id,trade_date")
                .execute()
            )
            SUPABASE_QUERY_DURATION.labels(table="market_data", operation="upsert_batch").observe(
                time.perf_counter() - start_time
            )
            return len(result.data)
        except Exception as e:
            SUPABASE_ERRORS.labels(table="market_data", operation="upsert_batch").inc()
            logger.error("db_upsert_batch_failed", table="market_data", error=str(e))
            raise

    async def log_audit(
        self, run_id: uuid.UUID, step: str, status: str, rows: int = 0, message: str | None = None
    ) -> None:
        """Log an entry to the audit log table."""
        start_time = time.perf_counter()
        try:
            self.client.table("audit_log").insert(
                {
                    "pipeline_run_id": str(run_id),
                    "step_name": step,
                    "status": status,
                    "rows_affected": rows,
                    "message": message,
                }
            ).execute()
            SUPABASE_QUERY_DURATION.labels(table="audit_log", operation="insert").observe(
                time.perf_counter() - start_time
            )
        except Exception as e:
            logger.error("audit_log_failed", error=str(e))

    async def get_experiments(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        """Retrieve paginated experiment results."""
        start_time = time.perf_counter()
        offset = (page - 1) * page_size
        try:
            result = self.client.table("method_results").select("*, option_parameters(*)").order("created_at", descending=True).range(offset, offset + page_size - 1).execute()
            SUPABASE_QUERY_DURATION.labels(table="method_results", operation="select_batch").observe(time.perf_counter() - start_time)
            return {"data": result.data, "page": page, "page_size": page_size}
        except Exception as e:
            SUPABASE_ERRORS.labels(table="method_results", operation="select_batch").inc()
            logger.error("db_query_failed", table="method_results", error=str(e))
            raise

    async def get_experiment_by_id(self, experiment_id: str) -> dict[str, Any] | None:
        """Retrieve a single experiment result by ID."""
        start_time = time.perf_counter()
        try:
            result = self.client.table("method_results").select("*, option_parameters(*)").eq("id", experiment_id).execute()
            SUPABASE_QUERY_DURATION.labels(table="method_results", operation="select_single").observe(time.perf_counter() - start_time)
            return result.data[0] if result.data else None
        except Exception as e:
            SUPABASE_ERRORS.labels(table="method_results", operation="select_single").inc()
            logger.error("db_query_failed", table="method_results", id=experiment_id, error=str(e))
            raise
