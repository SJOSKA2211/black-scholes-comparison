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
        return cast(list[dict[str, Any]], result.data or [])

    async def get_notifications(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch unread notifications for a user."""
        query = (
            self.client.table("notifications").select("*").eq("user_id", user_id).eq("read", False)
        )
        result = await self._execute("notifications", "select", query)
        return cast(list[dict[str, Any]], result.data or [])

    async def mark_notification_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        query = self.client.table("notifications").update({"read": True}).eq("id", notification_id)
        await self._execute("notifications", "update", query)

    async def mark_all_notifications_read(self, user_id: str) -> None:
        """Mark all notifications as read for a user."""
        query = self.client.table("notifications").update({"read": True}).eq("user_id", user_id)
        await self._execute("notifications", "update", query)

    async def insert_notification(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new notification."""
        query = self.client.table("notifications").insert(data)
        result = await self._execute("notifications", "insert", query)
        return cast(dict[str, Any], result.data[0] if result.data else {})

    async def get_experiments(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch all experiments for a user."""
        query = (
            self.client.table("method_results")
            .select("*, option_parameters(*)")
            .eq("run_by", user_id)
        )
        result = await self._execute("method_results", "select", query)
        return cast(list[dict[str, Any]], result.data or [])

    async def get_experiment_by_id(self, experiment_id: str) -> dict[str, Any]:
        """Fetch a specific experiment by ID."""
        query = (
            self.client.table("method_results")
            .select("*, option_parameters(*)")
            .eq("id", experiment_id)
        )
        result = await self._execute("method_results", "select", query)
        return cast(dict[str, Any], result.data[0] if result.data else {})

    async def get_scrape_runs(self) -> list[dict[str, Any]]:
        """Fetch all scrape runs."""
        query = self.client.table("scrape_runs").select("*").order("started_at", desc=True)
        result = await self._execute("scrape_runs", "select", query)
        return cast(list[dict[str, Any]], result.data or [])

    async def get_push_subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch all push subscriptions for a user."""
        query = (
            self.client.table("user_profiles").select("notification_preferences").eq("id", user_id)
        )
        result = await self._execute("user_profiles", "select", query)
        if result.data:
            prefs = result.data[0].get("notification_preferences", {})
            return cast(list[dict[str, Any]], prefs.get("push_subscriptions", []))
        return []

    async def insert_scrape_run(self, data: dict[str, Any]) -> dict[str, Any]:
        """Insert a new scrape run record."""
        query = self.client.table("scrape_runs").insert(data)
        result = await self._execute("scrape_runs", "insert", query)
        return cast(dict[str, Any], result.data[0] if result.data else {})

    async def update_scrape_run(self, run_id: str, data: dict[str, Any]) -> None:
        """Update an existing scrape run record."""
        query = self.client.table("scrape_runs").update(data).eq("id", run_id)
        await self._execute("scrape_runs", "update", query)

    async def insert_audit_log(self, data: dict[str, Any]) -> None:
        """Insert an audit log entry."""
        query = self.client.table("audit_log").insert(data)
        await self._execute("audit_log", "insert", query)

    async def insert_scrape_error(self, data: dict[str, Any]) -> None:
        """Insert a scrape error record."""
        query = self.client.table("scrape_errors").insert(data)
        await self._execute("scrape_errors", "insert", query)

    async def delete_test_data(self, table: str, column: str, value: Any) -> None:  # noqa: ANN401
        """Helper to clean up test data."""
        query = self.client.table(table).delete().eq(column, value)
        await self._execute(table, "delete", query)
