"""Repository layer for Supabase PostgreSQL operations."""

from __future__ import annotations

import datetime
import time
import uuid
from typing import Any

import pandas as pd
import structlog

from src.database.supabase_client import get_supabase
from src.exceptions import RepositoryError
from src.metrics import SUPABASE_ERRORS, SUPABASE_QUERY_DURATION

logger = structlog.get_logger(__name__)


class OptionRepository:
    """Handles all database interactions for option research data."""

    def __init__(self) -> None:
        self.client = get_supabase()

    async def upsert_option_params(self, params_dict: dict[str, Any]) -> str:
        """Manually upsert option parameters by checking existence first."""
        start_time = time.perf_counter()
        try:
            query = self.client.table("option_parameters").select("id")
            for key, val in params_dict.items():
                if key in [
                    "underlying_price",
                    "strike_price",
                    "maturity_years",
                    "volatility",
                    "risk_free_rate",
                    "option_type",
                    "is_american",
                    "market_source",
                ]:
                    query = query.eq(key, val)

            existing = query.execute()
            if existing.data:
                return str(existing.data[0]["id"])

            result = self.client.table("option_parameters").insert(params_dict).execute()
            SUPABASE_QUERY_DURATION.labels(table="option_parameters", operation="upsert").observe(
                time.perf_counter() - start_time
            )
            if not result.data:
                raise RepositoryError("Insert failed")
            return str(result.data[0]["id"])
        except Exception as e:
            SUPABASE_ERRORS.labels(table="option_parameters", operation="upsert").inc()
            logger.error("db_upsert_failed", table="option_parameters", error=str(e))
            raise RepositoryError(str(e)) from e

    async def insert_method_result(self, result_dict: dict[str, Any]) -> dict[str, Any]:
        """Insert a pricing method result."""
        start_time = time.perf_counter()
        try:
            if "run_by" in result_dict:
                del result_dict["run_by"]
            result = self.client.table("method_results").insert(result_dict).execute()
            SUPABASE_QUERY_DURATION.labels(table="method_results", operation="insert").observe(
                time.perf_counter() - start_time
            )
            return result.data[0]
        except Exception as e:
            SUPABASE_ERRORS.labels(table="method_results", operation="insert").inc()
            raise RepositoryError(str(e)) from e

    async def upsert_market_data(self, records: list[dict[str, Any]] | pd.DataFrame) -> int:
        """Upsert multiple market data rows."""
        start_time = time.perf_counter()
        if isinstance(records, pd.DataFrame):
            records = records.to_dict(orient="records")
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
            # Re-raise as RepositoryError for tests to catch
            raise RepositoryError(str(e)) from e

    async def log_audit(
        self,
        run_id: str | uuid.UUID,
        step: str,
        status: str,
        rows: int = 0,
        message: str | None = None,
    ) -> None:
        """Log an entry to the audit log table."""
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
        except Exception:
            pass

    async def get_experiments(
        self,
        page: int = 1,
        page_size: int = 50,
        method_type: str | None = None,
        market_source: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve paginated experiment results."""
        offset = (page - 1) * page_size
        query = self.client.table("method_results").select("*, option_parameters(*)")
        if method_type:
            query = query.eq("method_type", method_type)
        if market_source:
            query = query.eq("option_parameters.market_source", market_source)
        result = (
            query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()
        )
        return {"items": result.data, "page": page, "page_size": page_size}

    async def get_experiment_by_id(self, experiment_id: str) -> dict[str, Any]:
        """Retrieve a single experiment result by ID."""
        result = (
            self.client.table("method_results")
            .select("*, option_parameters(*)")
            .eq("id", experiment_id)
            .execute()
        )
        if not result.data:
            raise RepositoryError(f"Experiment {experiment_id} not found")
        return result.data[0]

    async def create_scrape_run(self, market: str, scraper_class: str = "default") -> str:
        """Initialize a scraper execution run record."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result = (
            self.client.table("scrape_runs")
            .insert(
                {
                    "market": market,
                    "scraper_class": scraper_class,
                    "status": "running",
                    "started_at": now,
                }
            )
            .execute()
        )
        return str(result.data[0]["id"])

    async def update_scrape_run(self, run_id: str, updates: dict[str, Any]) -> None:
        """Update a scraper execution run record."""
        self.client.table("scrape_runs").update(updates).eq("id", run_id).execute()

    async def get_scrape_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        """Retrieve recent scrape runs."""
        result = (
            self.client.table("scrape_runs")
            .select("*")
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data

    async def insert_notification(
        self, user_id: str, title: str, body: str, severity: str = "info", channel: str = "in_app"
    ) -> list[dict[str, Any]]:
        """Insert a new notification."""
        result = (
            self.client.table("notifications")
            .insert(
                {
                    "user_id": user_id,
                    "title": title,
                    "body": body,
                    "severity": severity,
                    "channel": channel,
                }
            )
            .execute()
        )
        return result.data

    async def get_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> list[dict[str, Any]]:
        """Retrieve notifications for a user."""
        query = (
            self.client.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if unread_only:
            query = query.eq("read", False)
        result = query.execute()
        return result.data

    async def mark_notification_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        self.client.table("notifications").update({"read": True}).eq(
            "id", notification_id
        ).execute()

    async def mark_all_notifications_read(self, user_id: str) -> None:
        """Mark all notifications for a user as read."""
        self.client.table("notifications").update({"read": True}).eq("user_id", user_id).eq(
            "read", False
        ).execute()

    async def upsert_user_profile(self, profile_dict: dict[str, Any]) -> None:
        """Upsert a user profile record."""
        self.client.table("user_profiles").upsert(profile_dict, on_conflict="id").execute()

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Retrieve a user profile record."""
        result = self.client.table("user_profiles").select("*").eq("id", user_id).execute()
        if not result.data:
            raise RepositoryError(f"User {user_id} not found")
        return result.data[0]

    async def check_db_health(self) -> str:
        """Check database connectivity."""
        try:
            self.client.table("user_profiles").select("id", count="exact").limit(1).execute()
            return "healthy"
        except Exception:
            return "unhealthy"

    async def get_validation_summary(self) -> list[dict[str, Any]]:
        """Retrieve a summary of validation metrics."""
        result = self.client.table("validation_metrics").select("*").limit(100).execute()
        return result.data

    async def get_push_subscriptions(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieve push subscriptions for a user."""
        result = (
            self.client.table("push_subscriptions").select("*").eq("user_id", user_id).execute()
        )
        return result.data

    async def delete_push_subscription(self, subscription_id: str) -> None:
        """Delete a push subscription record."""
        self.client.table("push_subscriptions").delete().eq("id", subscription_id).execute()

    async def get_market_data(
        self,
        source: str,
        trade_date: Any | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        page: int = 1,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve market data records with filters."""
        query = (
            self.client.table("market_data")
            .select("*, option_parameters(*)")
            .eq("data_source", source)
        )
        if trade_date:
            query = query.eq(
                "trade_date",
                trade_date.isoformat() if hasattr(trade_date, "isoformat") else trade_date,
            )
        if from_date:
            query = query.gte("trade_date", from_date)
        if to_date:
            query = query.lte("trade_date", to_date)
        offset = (page - 1) * limit
        result = query.order("trade_date", desc=True).range(offset, offset + limit - 1).execute()
        return result.data


# Singleton instance
_repo = OptionRepository()


# Wrapper functions
async def upsert_option_parameters(params: dict[str, Any]) -> str:
    return await _repo.upsert_option_params(params)


async def upsert_price_result(
    option_id: str, res: Any, user_id: str | None = None
) -> dict[str, Any]:
    res_data = res.model_dump() if hasattr(res, "model_dump") else res
    return await _repo.insert_method_result(
        {
            "option_id": option_id,
            "method_type": res_data.get("method_type"),
            "parameter_set": res_data.get("parameter_set"),
            "computed_price": res_data.get("computed_price"),
            "exec_seconds": res_data.get("exec_seconds"),
            "converged": True,
        }
    )


async def get_experiment_by_id(exp_id: str) -> dict[str, Any]:
    return await _repo.get_experiment_by_id(exp_id)


async def get_experiments_by_method(method: str) -> list[dict[str, Any]]:
    res = await _repo.get_experiments(method_type=method)
    return res["items"]


async def get_experiments(
    page: int = 1,
    page_size: int = 50,
    method_type: str | None = None,
    market_source: str | None = None,
) -> dict[str, Any]:
    return await _repo.get_experiments(page, page_size, method_type, market_source)


async def upsert_user_profile(profile: dict[str, Any]) -> None:
    return await _repo.upsert_user_profile(profile)


async def get_user_profile(user_id: str) -> dict[str, Any]:
    return await _repo.get_user_profile(user_id)


async def insert_notification(
    user_id: str, title: str, body: str, severity: str = "info", channel: str = "in_app"
) -> list[dict[str, Any]]:
    return await _repo.insert_notification(user_id, title, body, severity, channel)


async def get_notifications(
    user_id: str, limit: int = 50, unread_only: bool = False
) -> list[dict[str, Any]]:
    return await _repo.get_notifications(user_id, limit, unread_only)


async def mark_notification_read(notif_id: str) -> None:
    return await _repo.mark_notification_read(notif_id)


async def mark_all_notifications_read(user_id: str) -> None:
    return await _repo.mark_all_notifications_read(user_id)


async def insert_market_data(records: list[dict[str, Any]]) -> int:
    return await _repo.upsert_market_data(records)


async def get_market_data(
    source: str, from_date: str | None = None, to_date: str | None = None, limit: int = 100
) -> list[dict[str, Any]]:
    return await _repo.get_market_data(source, from_date=from_date, to_date=to_date, limit=limit)


async def create_scrape_run(market: str) -> str:
    return await _repo.create_scrape_run(market)


async def update_scrape_run(run_id: str, updates: dict[str, Any]) -> None:
    return await _repo.update_scrape_run(run_id, updates)


async def get_scrape_runs(limit: int = 20) -> list[dict[str, Any]]:
    return await _repo.get_scrape_runs(limit)


async def create_audit_log(run_id: str, step: str, status: str) -> None:
    return await _repo.log_audit(run_id, step, status)


async def check_db_health() -> str:
    return await _repo.check_db_health()


async def get_validation_summary() -> list[dict[str, Any]]:
    return await _repo.get_validation_summary()


async def get_push_subscriptions(user_id: str) -> list[dict[str, Any]]:
    return await _repo.get_push_subscriptions(user_id)


async def delete_push_subscription(sub_id: str) -> None:
    return await _repo.delete_push_subscription(sub_id)
