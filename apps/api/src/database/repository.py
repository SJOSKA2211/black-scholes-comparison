"""Repository for database operations using Supabase."""
from __future__ import annotations
import time
from typing import Any, Callable, cast
from src.database.supabase_client import get_supabase
from src.metrics import SUPABASE_QUERY_DURATION, SUPABASE_ERRORS
from src.exceptions import SupabaseError
import structlog

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
        logger.error("supabase_operation_failed", table=table, operation=operation, error=str(error))
        raise SupabaseError(f"Database error in {table}.{operation}") from error

async def upsert_option_parameters(params: dict[str, Any]) -> dict[str, Any]:
    """Upsert option parameters."""
    client = get_supabase()
    response = await _execute_query(
        "option_parameters", "upsert",
        lambda: client.table("option_parameters").upsert(params).execute()
    )
    return cast(dict[str, Any], response)

async def get_option_parameters(option_id: str) -> dict[str, Any]:
    """Fetch option parameters by ID."""
    client = get_supabase()
    response = await _execute_query(
        "option_parameters", "select",
        lambda: client.table("option_parameters").select("*").eq("id", option_id).single().execute()
    )
    return cast(dict[str, Any], response)

async def upsert_method_result(result: dict[str, Any]) -> dict[str, Any]:
    """Upsert pricing method results."""
    client = get_supabase()
    response = await _execute_query(
        "method_results", "upsert",
        lambda: client.table("method_results").upsert(result).execute()
    )
    return cast(dict[str, Any], response)

async def get_method_results(option_id: str) -> list[dict[str, Any]]:
    """Fetch method results for an option."""
    client = get_supabase()
    response = await _execute_query(
        "method_results", "select",
        lambda: client.table("method_results").select("*").eq("option_id", option_id).execute()
    )
    return cast(list[dict[str, Any]], response)

async def upsert_market_data(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Upsert market data rows."""
    client = get_supabase()
    response = await _execute_query(
        "market_data", "upsert",
        lambda: client.table("market_data").upsert(data).execute()
    )
    return cast(dict[str, Any], response)

async def upsert_validation_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Upsert validation metrics."""
    client = get_supabase()
    response = await _execute_query(
        "validation_metrics", "upsert",
        lambda: client.table("validation_metrics").upsert(metrics).execute()
    )
    return cast(dict[str, Any], response)

async def create_scrape_run(run_data: dict[str, Any]) -> dict[str, Any]:
    """Create a new scrape run entry."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_runs", "insert",
        lambda: client.table("scrape_runs").insert(run_data).execute()
    )
    return cast(dict[str, Any], response)

async def update_scrape_run(run_id: str, update_data: dict[str, Any]) -> dict[str, Any]:
    """Update an existing scrape run."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_runs", "update",
        lambda: client.table("scrape_runs").update(update_data).eq("id", run_id).execute()
    )
    return cast(dict[str, Any], response)

async def create_audit_log(log_data: dict[str, Any]) -> dict[str, Any]:
    """Create an audit log entry."""
    client = get_supabase()
    response = await _execute_query(
        "audit_log", "insert",
        lambda: client.table("audit_log").insert(log_data).execute()
    )
    return cast(dict[str, Any], response)

async def create_scrape_error(error_data: dict[str, Any]) -> dict[str, Any]:
    """Create a scrape error entry."""
    client = get_supabase()
    response = await _execute_query(
        "scrape_errors", "insert",
        lambda: client.table("scrape_errors").insert(error_data).execute()
    )
    return cast(dict[str, Any], response)

async def get_notifications(user_id: str) -> list[dict[str, Any]]:
    """Fetch notifications for a user."""
    client = get_supabase()
    response = await _execute_query(
        "notifications", "select",
        lambda: client.table("notifications").select("*").eq("user_id", user_id).execute()
    )
    return cast(list[dict[str, Any]], response)

async def mark_notification_read(notification_id: str) -> dict[str, Any]:
    """Mark a notification as read."""
    client = get_supabase()
    response = await _execute_query(
        "notifications", "update",
        lambda: client.table("notifications").update({"read": True}).eq("id", notification_id).execute()
    )
    return cast(dict[str, Any], response)

async def get_user_profile(user_id: str) -> dict[str, Any]:
    """Fetch user profile."""
    client = get_supabase()
    response = await _execute_query(
        "user_profiles", "select",
        lambda: client.table("user_profiles").select("*").eq("id", user_id).single().execute()
    )
    return cast(dict[str, Any], response)

async def update_user_profile(user_id: str, profile_data: dict[str, Any]) -> dict[str, Any]:
    """Update user profile."""
    client = get_supabase()
    response = await _execute_query(
        "user_profiles", "update",
        lambda: client.table("user_profiles").update(profile_data).eq("id", user_id).execute()
    )
    return cast(dict[str, Any], response)
