"""Repository for database operations using Supabase."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, cast

import structlog

from src.database.supabase_client import get_supabase
from src.exceptions import SupabaseError
from src.metrics import SUPABASE_ERRORS, SUPABASE_QUERY_DURATION

if TYPE_CHECKING:
    from collections.abc import Callable

logger = structlog.get_logger(__name__)


async def _execute_query(table: str, operation: str, query_fn: Callable[[], Any]) -> Any:
    """Helper to execute Supabase queries with metrics."""
    start_time = time.perf_counter()
    try:
        response = query_fn()
        duration = time.perf_counter() - start_time
        SUPABASE_QUERY_DURATION.labels(table=table, operation=operation).observe(duration)
        return response
    except Exception as error:
        SUPABASE_ERRORS.labels(table=table, operation=operation).inc()
        # Extract message from postgrest APIError if possible
        error_msg = str(error)
        if hasattr(error, "message"):
            error_msg = error.message
        elif hasattr(error, "args") and error.args:
            error_msg = str(error.args[0])

        logger.error("supabase_operation_failed", table=table, operation=operation, error=error_msg)
        raise SupabaseError(f"Database error in {table}.{operation}: {error_msg}") from error


async def upsert_option_parameters(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Upsert option parameters."""
    client = get_supabase()
    response = await _execute_query(
        "option_parameters",
        "upsert",
        lambda: client.table("option_parameters").upsert(params).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def get_option_parameters(option_id: str) -> dict[str, Any]:
    """Fetch option parameters by ID."""
    client = get_supabase()
    response = await _execute_query(
        "option_parameters",
        "select",
        lambda: client.table("option_parameters")
        .select("*")
        .eq("id", option_id)
        .single()
        .execute(),
    )
    return cast(dict[str, Any], response.data)


async def upsert_method_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Upsert pricing method results."""
    client = get_supabase()
    response = await _execute_query(
        "method_results",
        "upsert",
        lambda: client.table("method_results").upsert(result).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def get_method_results(option_id: str) -> list[dict[str, Any]]:
    """Fetch method results for an option."""
    client = get_supabase()
    response = await _execute_query(
        "method_results",
        "select",
        lambda: client.table("method_results").select("*").eq("option_id", option_id).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def upsert_market_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upsert market data rows."""
    client = get_supabase()
    response = await _execute_query(
        "market_data", "upsert", lambda: client.table("market_data").upsert(data).execute()
    )
    return cast(list[dict[str, Any]], response.data)


async def upsert_validation_metrics(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Upsert validation metrics."""
    client = get_supabase()
    response = await _execute_query(
        "validation_metrics",
        "upsert",
        lambda: client.table("validation_metrics").upsert(metrics).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def create_scrape_run(run_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create a new scrape run entry."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_runs", "insert", lambda: client.table("scrape_runs").insert(run_data).execute()
    )
    return cast(list[dict[str, Any]], response.data)


async def update_scrape_run(run_id: str, update_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Update an existing scrape run."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_runs",
        "update",
        lambda: client.table("scrape_runs").update(update_data).eq("id", run_id).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def list_scrape_runs(limit: int = 50) -> list[dict[str, Any]]:
    """List recent scrape runs."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_runs",
        "list",
        lambda: client.table("scrape_runs")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def create_audit_log(log_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create an audit log entry."""
    client = get_supabase()
    response = await _execute_query(
        "audit_log", "insert", lambda: client.table("audit_log").insert(log_data).execute()
    )
    return cast(list[dict[str, Any]], response.data)


async def create_scrape_error(error_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Create a scrape error entry."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_errors",
        "insert",
        lambda: client.table("scrape_errors").insert(error_data).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def get_notifications(user_id: str) -> list[dict[str, Any]]:
    """Fetch notifications for a user."""
    client = get_supabase()
    response = await _execute_query(
        "notifications",
        "select",
        lambda: client.table("notifications").select("*").eq("user_id", user_id).execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def mark_notification_read(notification_id: str) -> dict[str, Any]:
    """Mark a notification as read."""
    client = get_supabase()
    response = await _execute_query(
        "notifications",
        "update",
        lambda: client.table("notifications")
        .update({"read": True})
        .eq("id", notification_id)
        .execute(),
    )
    return cast(dict[str, Any], response.data)


async def get_user_profile(user_id: str) -> dict[str, Any]:
    """Fetch user profile."""
    client = get_supabase()
    response = await _execute_query(
        "user_profiles",
        "select",
        lambda: client.table("user_profiles").select("*").eq("id", user_id).single().execute(),
    )
    return cast(dict[str, Any], response.data)


async def list_option_parameters(
    limit: int = 100, market: str | None = None
) -> list[dict[str, Any]]:
    """List option parameters with optional market filtering."""
    client = get_supabase()
    query = (
        client.table("option_parameters").select("*").order("created_at", desc=True).limit(limit)
    )
    if market:
        query = query.eq("market_source", market)
    response = await _execute_query("option_parameters", "list", lambda: query.execute())
    return cast(list[dict[str, Any]], response.data)


async def list_method_results(limit: int = 100) -> list[dict[str, Any]]:
    """List recent pricing method results."""
    client = get_supabase()
    response = await _execute_query(
        "method_results",
        "list",
        lambda: client.table("method_results")
        .select("*, option_parameters(*)")
        .order("run_at", desc=True)
        .limit(limit)
        .execute(),
    )
    return cast(list[dict[str, Any]], response.data)


async def list_market_data(limit: int = 100, market: str | None = None) -> list[dict[str, Any]]:
    """List market data with optional filtering."""
    client = get_supabase()
    query = (
        client.table("market_data")
        .select("*, option_parameters(*)")
        .order("trade_date", desc=True)
        .limit(limit)
    )
    if market:
        # Assuming we filter by option_parameters.market_source via join
        query = query.eq("option_parameters.market_source", market)
    response = await _execute_query("market_data", "list", lambda: query.execute())
    return cast(list[dict[str, Any]], response.data)


async def update_user_profile(user_id: str, profile_data: dict[str, Any]) -> dict[str, Any]:
    """Update user profile."""
    client = get_supabase()
    response = await _execute_query(
        "user_profiles",
        "update",
        lambda: client.table("user_profiles").update(profile_data).eq("id", user_id).execute(),
    )
    return cast(dict[str, Any], response.data)
