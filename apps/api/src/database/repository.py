import datetime
import json
import time
from typing import Any, cast

import structlog

from src.database.supabase_client import get_supabase_client
from src.exceptions import RepositoryError
from src.metrics import SUPABASE_ERRORS_TOTAL, SUPABASE_QUERY_DURATION_SECONDS

logger = structlog.get_logger(__name__)


async def upsert_option_parameters(params: dict[str, Any]) -> str:
    """
    Finds existing option parameters or inserts new ones.
    Returns the ID of the record.
    """
    supabase = get_supabase_client()
    table = "option_parameters"
    op = "upsert"
    start = time.time()
    try:
        # Check for existing parameters to ensure idempotency
        query = supabase.table(table).select("id")
        for key, value in params.items():
            query = query.eq(key, value)

        existing = query.execute()

        if existing.data:
            SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation="select").observe(
                time.time() - start
            )
            data_list = cast("list[dict[str, Any]]", existing.data)
            return str(data_list[0]["id"])

        # If not found, insert
        response = supabase.table(table).insert(params).execute()

        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation="insert").observe(
            time.time() - start
        )

        data_list = cast("list[dict[str, Any]]", response.data)
        return str(data_list[0]["id"])
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="upsert_option_parameters", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def insert_method_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "method_results"
    op = "insert"
    start = time.time()
    try:
        response = supabase.table(table).insert(result).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )

        # Publish to Redis for WebSocket real-time push
        from src.cache.redis_client import get_redis

        redis = get_redis()
        await redis.publish("ws:experiments", json.dumps(response.data[0]))

        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="insert_method_result", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def get_experiments(
    method_type: str | None = None,
    market_source: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    supabase = get_supabase_client()
    table = "method_results"
    op = "select"
    start = time.time()

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size - 1

    query = supabase.table(table).select("*, option_parameters(*)", count=cast("Any", "exact"))

    if method_type:
        query = query.eq("method_type", method_type)
    if market_source:
        query = query.eq("option_parameters.market_source", market_source)

    try:
        response = query.range(start_idx, end_idx).order("run_at", desc=True).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )

        total = response.count
        return {
            "items": cast("list[dict[str, Any]]", response.data),
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": (start_idx + page_size) < total if total else False,
            "has_prev": page > 1,
        }
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="get_experiments", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def insert_notification(
    user_id: str,
    title: str,
    body: str,
    severity: str,
    channel: str,
    action_url: str | None = None,
) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "notifications"
    op = "insert"
    start = time.time()
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "body": body,
            "severity": severity,
            "channel": channel,
            "action_url": action_url,
            "read": False,
        }
        response = supabase.table(table).insert(data).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="insert_notification", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def get_user_profile(user_id: str) -> dict[str, Any] | None:
    supabase = get_supabase_client()
    table = "user_profiles"
    op = "select"
    start = time.time()
    try:
        response = supabase.table(table).select("*").eq("id", user_id).single().execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("dict[str, Any] | None", response.data)
    except Exception:
        logger.debug("user_profile_not_found", user_id=user_id)
        return None


async def upsert_user_profile(profile: dict[str, Any]) -> dict[str, Any]:
    supabase = get_supabase_client()
    table = "user_profiles"
    op = "upsert"
    start = time.time()
    try:
        response = supabase.table(table).upsert(profile).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("dict[str, Any]", response.data[0])
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="upsert_user_profile", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def get_market_data(
    source: str,
    trade_date: datetime.date | None = None,
    limit: int = 100,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "market_data"
    op = "select"
    start = time.time()
    try:
        query = supabase.table(table).select("*, option_parameters(*)").eq("data_source", source)
        if trade_date:
            query = query.eq("trade_date", trade_date.isoformat())
        if from_date:
            query = query.gte("trade_date", from_date)
        if to_date:
            query = query.lte("trade_date", to_date)

        response = query.order("trade_date", desc=True).limit(limit).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="get_market_data", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def insert_market_data(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "market_data"
    op = "upsert"
    start = time.time()
    try:
        response = supabase.table(table).upsert(data, on_conflict="option_id, trade_date").execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="insert_market_data", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def get_validation_summary() -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "validation_metrics"
    op = "select"
    start = time.time()
    try:
        response = (
            supabase.table(table)
            .select("method_result_id, method_results(method_type), mape, market_deviation")
            .execute()
        )
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="get_validation_summary", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def create_scrape_run(market: str, triggered_by: str | None = None) -> str:
    supabase = get_supabase_client()
    table = "scrape_runs"
    op = "insert"
    start = time.time()
    try:
        data = {"market": market, "status": "running", "triggered_by": triggered_by}
        response = supabase.table(table).insert(data).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        data_list = cast("list[dict[str, Any]]", response.data)
        return str(data_list[0]["id"])
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="create_scrape_run", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def update_scrape_run(run_id: str, data: dict[str, Any]) -> dict[str, Any]:
    supabase = get_supabase_client()
    table = "scrape_runs"
    op = "update"
    start = time.time()
    try:
        response = supabase.table(table).update(data).eq("id", run_id).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("dict[str, Any]", response.data[0])
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="update_scrape_run", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def create_audit_log(
    pipeline_run_id: str,
    step_name: str,
    status: str,
    rows_affected: int = 0,
    message: str | None = None,
) -> None:
    supabase = get_supabase_client()
    table = "audit_log"
    op = "insert"
    start = time.time()
    try:
        data: dict[str, Any] = {
            "pipeline_run_id": pipeline_run_id,
            "step_name": step_name,
            "status": status,
            "rows_affected": rows_affected,
            "message": message,
        }
        supabase.table(table).insert(data).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="create_audit_log", error=str(e))


async def get_scrape_runs(limit: int = 20) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "scrape_runs"
    op = "select"
    start = time.time()
    try:
        response = (
            supabase.table(table).select("*").order("started_at", desc=True).limit(limit).execute()
        )
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="get_scrape_runs", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def insert_audit_log(
    pipeline_run_id: str | None,
    step_name: str,
    status: str,
    rows_affected: int,
    message: str,
) -> None:
    supabase = get_supabase_client()
    table = "audit_log"
    op = "insert"
    start = time.time()
    try:
        data: dict[str, Any] = {
            "pipeline_run_id": pipeline_run_id,
            "step_name": step_name,
            "status": status,
            "rows_affected": rows_affected,
            "message": message,
        }
        supabase.table(table).insert(data).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="insert_audit_log", error=str(e))


async def get_notifications(
    user_id: str, unread_only: bool = True, limit: int = 50
) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "notifications"
    op = "select"
    start = time.time()
    try:
        query = supabase.table(table).select("*").eq("user_id", user_id)
        if unread_only:
            query = query.eq("read", False)
        query = query.order("created_at", desc=True).limit(limit)
        response = query.execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="get_notifications", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def mark_notification_read(notification_id: str) -> None:
    supabase = get_supabase_client()
    table = "notifications"
    op = "update"
    start = time.time()
    try:
        supabase.table(table).update({"read": True}).eq("id", notification_id).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="mark_notification_read", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def mark_all_notifications_read(user_id: str) -> None:
    supabase = get_supabase_client()
    table = "notifications"
    op = "update"
    start = time.time()
    try:
        supabase.table(table).update({"read": True}).eq("user_id", user_id).eq(
            "read", False
        ).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
    except Exception as e:
        SUPABASE_ERRORS_TOTAL.labels(table=table, operation=op).inc()
        logger.error("repository_error", operation="mark_all_notifications_read", error=str(e))
        raise RepositoryError(f"Database operation failed: {e!s}") from e


async def get_experiment_by_id(experiment_id: str) -> dict[str, Any] | None:
    supabase = get_supabase_client()
    table = "method_results"
    op = "select"
    start = time.time()
    try:
        response = (
            supabase.table(table)
            .select("*, option_parameters(*)")
            .eq("id", experiment_id)
            .single()
            .execute()
        )
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("dict[str, Any] | None", response.data)
    except Exception:
        logger.debug("experiment_not_found", experiment_id=experiment_id)
        return None


async def get_push_subscriptions(user_id: str) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "push_subscriptions"
    op = "select"
    start = time.time()
    try:
        response = supabase.table(table).select("*").eq("user_id", user_id).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        logger.error("repository_error", operation="get_push_subscriptions", error=str(e))
        return []


async def delete_push_subscription(subscription_id: str) -> None:
    supabase = get_supabase_client()
    table = "push_subscriptions"
    op = "delete"
    start = time.time()
    try:
        supabase.table(table).delete().eq("id", subscription_id).execute()
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
    except Exception as e:
        logger.error("repository_error", operation="delete_push_subscription", error=str(e))


async def get_experiments_by_method(method_type: str) -> list[dict[str, Any]]:
    supabase = get_supabase_client()
    table = "method_results"
    op = "select"
    start = time.time()
    try:
        response = (
            supabase.table(table)
            .select("*, option_parameters(*)")
            .eq("method_type", method_type)
            .execute()
        )
        SUPABASE_QUERY_DURATION_SECONDS.labels(table=table, operation=op).observe(
            time.time() - start
        )
        return cast("list[dict[str, Any]]", response.data)
    except Exception as e:
        logger.error("repository_error", operation="get_experiments_by_method", error=str(e))
        return []
