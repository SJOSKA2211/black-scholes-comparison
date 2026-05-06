"""Repository for interacting with Supabase tables."""

import time
from typing import Any, cast

import structlog

from src.database.supabase_client import get_supabase
from src.metrics import SUPABASE_ERRORS, SUPABASE_QUERY_DURATION

logger = structlog.get_logger(__name__)


class Repository:
    """Data access layer for Supabase."""

    def __init__(self) -> None:
        self.client = get_supabase()

    async def _execute(self, table: str, operation: str, query: Any) -> Any:  # noqa: ANN401
        """Execute a Supabase query with metrics and logging."""
        start_time = time.perf_counter()
        try:
            result = query.execute()
            SUPABASE_QUERY_DURATION.labels(table=table, operation=operation).observe(
                time.perf_counter() - start_time
            )
            return result
        except Exception as e:
            SUPABASE_ERRORS.labels(table=table, operation=operation).inc()
            logger.error("supabase_error", table=table, operation=operation, error=str(e))
            raise

    async def upsert_option_parameters(self, data: dict[str, Any]) -> dict[str, Any]:
        """Upsert an option parameter record."""
        query = self.client.table("option_parameters").upsert(
            data,
            on_conflict="underlying_price,strike_price,maturity_years,volatility,risk_free_rate,option_type,market_source",
        )
        result = await self._execute("option_parameters", "upsert", query)
        return cast(dict[str, Any], result.data[0] if result.data else {})

    async def insert_method_result(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a pricing method result."""
        query = self.client.table("method_results").insert(data)
        result = await self._execute("method_results", "insert", query)
        return cast(dict[str, Any], result.data[0] if result.data else {})

    async def get_market_data(self, option_id: str) -> list[dict[str, Any]]:
        """Fetch market data for a specific option."""
        query = self.client.table("market_data").select("*").eq("option_id", option_id)
        result = await self._execute("market_data", "select", query)
        return result.data or []

    async def delete_test_data(self, table: str, column: str, value: Any) -> None:  # noqa: ANN401
        """Helper to clean up test data."""
        query = self.client.table(table).delete().eq(column, value)
        await self._execute(table, "delete", query)
