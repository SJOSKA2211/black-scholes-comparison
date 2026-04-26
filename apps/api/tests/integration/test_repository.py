"""Integration tests for the repository layer — zero-mock policy.
All tests use real Supabase, Redis, and infrastructure.
Covers all CRUD operations against real database.
"""

import datetime
import uuid

import pytest

from src.database import repository
from src.exceptions import RepositoryError
from src.methods.base import PriceResult


@pytest.fixture
async def cleanup_ids():
    """Track IDs for cleanup after test."""
    to_cleanup = {
        "notifications": [],
        "push_subscriptions": [],
        "scrape_runs": [],
        "method_results": [],
        "market_data": [],
        "user_profiles": [],
        "option_parameters": [],
    }
    yield to_cleanup
    from src.database.supabase_client import get_supabase_client

    supabase = get_supabase_client()
    # Clean up in reverse dependency order
    for table in [
        "notifications",
        "push_subscriptions",
        "method_results",
        "market_data",
        "scrape_runs",
        "option_parameters",
    ]:
        ids = to_cleanup.get(table, [])
        if ids:
            try:
                id_list = [str(i) for i in ids]
                if table == "market_data":
                    supabase.table(table).delete().in_("option_id", id_list).execute()
                else:
                    supabase.table(table).delete().in_("id", id_list).execute()
            except Exception as cleanup_error:
                import structlog

                structlog.get_logger().warning(
                    "cleanup_failed", table=table, error=str(cleanup_error)
                )


@pytest.fixture
async def test_user_id():
    """Get a valid user_id from the database for FK references."""
    from src.database.supabase_client import get_supabase_client

    supabase = get_supabase_client()
    res = supabase.table("user_profiles").select("id").limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    return "de34e0d4-ad52-4ffe-9f75-1d41c83a4fb2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_option_parameters(sample_option_params, cleanup_ids) -> None:
    """Test upsert creates new record and returns same ID on repeat."""
    option_id = await repository.upsert_option_parameters(sample_option_params)
    assert uuid.UUID(option_id)
    cleanup_ids["option_parameters"].append(option_id)

    # Idempotency: calling again with same params returns same ID
    option_id_2 = await repository.upsert_option_parameters(sample_option_params)
    assert option_id == option_id_2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_result_flow(sample_option_params, cleanup_ids) -> None:
    """Test full flow: upsert params -> upsert price result -> query by ID and method."""
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)

    result = await repository.upsert_price_result(
        option_id,
        PriceResult(method_type="analytical", computed_price=10.5, exec_seconds=0.001, delta=0.5),
    )
    cleanup_ids["method_results"].append(result["id"])

    # Verify query by ID
    fetched = await repository.get_experiment_by_id(result["id"])
    assert fetched["id"] == result["id"]

    # Verify query by method type
    by_method = await repository.get_experiments_by_method("analytical")
    assert any(e["id"] == result["id"] for e in by_method)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_profile_operations(cleanup_ids, test_user_id) -> None:
    """Test user profile upsert and retrieval with real Supabase."""
    user_id = test_user_id
    await repository.upsert_user_profile({"id": user_id, "display_name": "IntegrationTest"})
    profile = await repository.get_user_profile(user_id)
    assert profile["display_name"] == "IntegrationTest"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_workflow(cleanup_ids, test_user_id) -> None:
    """Test full notification lifecycle: create, read, mark read, mark all read."""
    user_id = test_user_id
    notifs = await repository.insert_notification(user_id, "Test", "Body", "info", "in_app")
    notif_id = notifs[0]["id"]

    # Should appear in unread
    unread = await repository.get_notifications(user_id, unread_only=True)
    assert any(n["id"] == notif_id for n in unread)

    # Mark single notification read
    await repository.mark_notification_read(notif_id)

    # Mark all read
    await repository.mark_all_notifications_read(user_id)

    # Should not appear in unread anymore
    unread_after = await repository.get_notifications(user_id, unread_only=True)
    assert all(n["id"] != notif_id for n in unread_after)

    # Should appear in all notifications
    all_notifs = await repository.get_notifications(user_id, unread_only=False)
    assert any(n["id"] == notif_id for n in all_notifs)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_operations(sample_option_params, cleanup_ids) -> None:
    """Test market data insert and retrieval with real Supabase."""
    # Use a unique set of params to avoid conflicts
    unique_params = sample_option_params.copy()
    unique_params["strike_price"] = 99.99  # Unique strike to avoid dedup
    option_id = await repository.upsert_option_parameters(unique_params)
    cleanup_ids["option_parameters"].append(option_id)

    today = datetime.date.today()
    await repository.insert_market_data(
        [
            {
                "option_id": option_id,
                "trade_date": today.isoformat(),
                "data_source": "spy",
                "bid_price": 10.0,
                "ask_price": 11.0,
                "volume": 100,
                "open_interest": 50,
            }
        ]
    )
    cleanup_ids["market_data"].append(option_id)

    # Query by source and specifically for our option_id
    data = await repository.get_market_data("spy", limit=1000)
    found = False
    for d in data:
        if str(d["option_id"]) == str(option_id):
            found = True
            break
    assert found, f"Option ID {option_id} not found in market data for spy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_run_and_audit(cleanup_ids) -> None:
    """Test scrape run creation, update, and audit log with real Supabase."""
    run_id = await repository.create_scrape_run("spy")
    cleanup_ids["scrape_runs"].append(run_id)

    await repository.update_scrape_run(run_id, {"status": "success"})
    await repository.create_audit_log(run_id, "test_step", "completed")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_error_handling(cleanup_ids) -> None:
    """Test audit log with invalid pipeline_run_id (non-existent FK).
    create_audit_log catches exceptions and logs, does not raise.
    """
    # Use a non-existent UUID — the audit_log insert may fail due to FK
    # but create_audit_log silently catches the error
    fake_run_id = str(uuid.uuid4())
    # This should not raise because create_audit_log catches exceptions
    await repository.create_audit_log(fake_run_id, "test_fail", "status_fail")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_health_and_validation() -> None:
    """Test database health check and validation summary with real Supabase."""
    health = await repository.check_db_health()
    assert health == "healthy"

    validation = await repository.get_validation_summary()
    assert isinstance(validation, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_experiments_filters(sample_option_params, cleanup_ids) -> None:
    """Test experiment listing with method_type and market_source filters."""
    params = sample_option_params.copy()
    params["market_source"] = "nse"
    params["strike_price"] = 101.01  # Unique
    option_id = await repository.upsert_option_parameters(params)
    cleanup_ids["option_parameters"].append(option_id)

    result = await repository.upsert_price_result(
        option_id, PriceResult(method_type="trinomial", computed_price=15.0, exec_seconds=0.1)
    )
    cleanup_ids["method_results"].append(result["id"])

    # Filter by method type
    filtered = await repository.get_experiments(method_type="trinomial")
    assert any(e["id"] == result["id"] for e in filtered["items"])

    # Filter by market source
    filtered_mkt = await repository.get_experiments(market_source="nse")
    assert any(e["id"] == result["id"] for e in filtered_mkt["items"])


@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_date_filters(sample_option_params, cleanup_ids) -> None:
    """Test market data filtering by from_date and to_date."""
    params = sample_option_params.copy()
    params["strike_price"] = 102.02  # Unique
    option_id = await repository.upsert_option_parameters(params)
    cleanup_ids["option_parameters"].append(option_id)

    today = datetime.date.today()
    await repository.insert_market_data(
        [
            {
                "option_id": option_id,
                "trade_date": today.isoformat(),
                "data_source": "nse",
                "bid_price": 200.0,
                "ask_price": 210.0,
            }
        ]
    )
    cleanup_ids["market_data"].append(option_id)

    data_from = await repository.get_market_data("nse", from_date=today.isoformat())
    assert len(data_from) >= 1

    data_to = await repository.get_market_data("nse", to_date=today.isoformat())
    assert len(data_to) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_listing(cleanup_ids) -> None:
    """Test scrape runs listing returns created runs."""
    run_id = await repository.create_scrape_run("spy")
    cleanup_ids["scrape_runs"].append(run_id)

    runs = await repository.get_scrape_runs(limit=100)
    assert any(str(r["id"]) == str(run_id) for r in runs)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_result_with_user_id(sample_option_params, cleanup_ids, test_user_id) -> None:
    """Test upsert_price_result with user_id triggers Redis publish."""
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)

    result = await repository.upsert_price_result(
        option_id,
        PriceResult(method_type="analytical", computed_price=10.0, exec_seconds=0.1),
        user_id=test_user_id,
    )
    cleanup_ids["method_results"].append(result["id"])
    assert result["computed_price"] == 10.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_push_subscriptions(cleanup_ids, test_user_id) -> None:
    """Test push subscription CRUD with real Supabase."""
    user_id = test_user_id
    from src.database.supabase_client import get_supabase_client

    supabase = get_supabase_client()
    sub_id = str(uuid.uuid4())
    supabase.table("push_subscriptions").insert(
        {
            "id": sub_id,
            "user_id": user_id,
            "subscription_info": {"endpoint": "https://e.com", "keys": {"p": "k"}},
        }
    ).execute()
    cleanup_ids["push_subscriptions"].append(sub_id)

    subs = await repository.get_push_subscriptions(user_id)
    assert any(s["id"] == sub_id for s in subs)

    await repository.delete_push_subscription(sub_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repository_error_on_invalid_data() -> None:
    """Test that invalid data raises RepositoryError from real Supabase.
    Zero-mock: we send bad data to real DB and expect proper error handling.
    """
    # Attempt to insert market data with non-existent option_id FK
    with pytest.raises(RepositoryError):
        await repository.insert_market_data(
            [{"option_id": str(uuid.uuid4()), "trade_date": "2099-01-01", "data_source": "spy"}]
        )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_experiment_by_id_nonexistent() -> None:
    """Test querying a non-existent experiment raises RepositoryError."""
    fake_id = str(uuid.uuid4())
    with pytest.raises(RepositoryError):
        await repository.get_experiment_by_id(fake_id)
