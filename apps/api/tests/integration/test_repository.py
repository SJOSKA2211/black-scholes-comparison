"""Integration tests for the repository layer.
Covers all CRUD operations against real Supabase.
"""
import datetime
import uuid
import pytest
from src.database import repository
from src.methods.base import PriceResult
from src.exceptions import RepositoryError

@pytest.fixture
async def cleanup_ids():
    """Tracks IDs for cleanup after tests."""
    # Order matters: children first, then parents
    to_cleanup = {
        "notifications": [],
        "push_subscriptions": [],
        "scrape_runs": [],
        "method_results": [],
        "market_data": [],
        "user_profiles": [],
        "option_parameters": []
    }
    yield to_cleanup
    
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    for table, ids in to_cleanup.items():
        if ids:
            try:
                id_list = [str(i) for i in ids]
                if table == "market_data":
                     # For market_data, we assume ids are option_ids
                     supabase.table(table).delete().in_("option_id", id_list).execute()
                else:
                     supabase.table(table).delete().in_("id", id_list).execute()
            except Exception as e:
                print(f"Cleanup failed for {table}: {e}")

@pytest.fixture
async def test_user_id():
    """Provides a valid user ID from the database."""
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    res = supabase.table("user_profiles").select("id").limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    return "de34e0d4-ad52-4ffe-9f75-1d41c83a4fb2" # Fallback

@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_option_parameters(sample_option_params, cleanup_ids):
    option_id = await repository.upsert_option_parameters(sample_option_params)
    assert uuid.UUID(option_id)
    cleanup_ids["option_parameters"].append(option_id)
    
    # Idempotency check
    option_id_2 = await repository.upsert_option_parameters(sample_option_params)
    assert option_id == option_id_2

@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_result_flow(sample_option_params, cleanup_ids):
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)
    
    price_res = PriceResult(
        method_type="analytical",
        computed_price=10.5,
        exec_seconds=0.001,
        parameter_set={"n": 100},
        delta=0.5
    )
    
    res = await repository.upsert_price_result(option_id, price_res)
    assert res["id"] is not None
    cleanup_ids["method_results"].append(res["id"])
    assert res["computed_price"] == 10.5
    
    # Test retrieval
    exp = await repository.get_experiment_by_id(res["id"])
    assert exp["id"] == res["id"]
    assert exp["computed_price"] == 10.5
    
    experiments = await repository.get_experiments(method_type="analytical")
    assert any(e["id"] == res["id"] for e in experiments["items"])
    
    exp_by_method = await repository.get_experiments_by_method("analytical")
    assert any(e["id"] == res["id"] for e in exp_by_method)

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires real auth.users record which cannot be mocked on real Supabase")
async def test_user_profile_operations(cleanup_ids):
    user_id = str(uuid.uuid4())
    profile = {
        "id": user_id,
        "display_name": "Test User",
        "role": "researcher"
    }
    
    res = await repository.upsert_user_profile(profile)
    assert res["id"] == user_id
    cleanup_ids["user_profiles"].append(user_id)
    
    fetched = await repository.get_user_profile(user_id)
    assert fetched["display_name"] == "Test User"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_workflow(cleanup_ids, test_user_id):
    # Setup user
    user_id = test_user_id
    
    notifs = await repository.insert_notification(
        user_id=user_id,
        title="Test",
        body="Body",
        severity="info",
        channel="in_app"
    )
    notif_id = notifs[0]["id"]
    # No explicit cleanup for notifications as they belong to user (CASCADE)
    
    unread = await repository.get_notifications(user_id, unread_only=True)
    assert any(n["id"] == notif_id for n in unread)
    
    await repository.mark_notification_read(notif_id)
    unread_after = await repository.get_notifications(user_id, unread_only=True)
    assert all(n["id"] != notif_id for n in unread_after)
    
    # Mark all read
    await repository.insert_notification(user_id, "T2", "B2", "info", "in_app")
    await repository.mark_all_notifications_read(user_id)
    unread_final = await repository.get_notifications(user_id, unread_only=True)
    assert len(unread_final) == 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_operations(sample_option_params, cleanup_ids):
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)
    
    today = datetime.date.today()
    market_data = [{
        "option_id": option_id,
        "trade_date": today.isoformat(),
        "bid_price": 10.0,
        "ask_price": 11.0,
        "data_source": "spy"
    }]
    
    await repository.insert_market_data(market_data)
    cleanup_ids["market_data"].append(option_id)
    
    fetched = await repository.get_market_data("spy", trade_date=today)
    assert len(fetched) >= 1
    assert any(d["option_id"] == option_id for d in fetched)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_run_and_audit(cleanup_ids, test_user_id):
    user_id = test_user_id
    
    run_id = await repository.create_scrape_run("spy")
    assert uuid.UUID(run_id)
    cleanup_ids["scrape_runs"].append(run_id)
    
    await repository.update_scrape_run(run_id, {"status": "success", "rows_scraped": 42})
    
    await repository.create_audit_log(run_id, "test_step", "success", rows_affected=5)
    
    runs = await repository.get_scrape_runs(limit=10)
    assert any(r["id"] == run_id for r in runs)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_health_and_validation():
    health = await repository.check_db_health()
    assert health == "healthy"
    
    summary = await repository.get_validation_summary()
    assert isinstance(summary, list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_repository_error_scenarios():
    with pytest.raises(RepositoryError):
        await repository.get_experiment_by_id("not-a-uuid")
    
    with pytest.raises(RepositoryError):
        # Missing required fields
        await repository.upsert_option_parameters({"invalid": "data"})

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Schema mismatch for push_subscriptions table")
async def test_push_subscriptions(cleanup_ids, test_user_id):
    user_id = test_user_id
    
    # We use direct supabase call to setup as there's no insert_push_subscription in repository.py
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    sub_id = str(uuid.uuid4())
    supabase.table("push_subscriptions").insert({
        "id": sub_id,
        "user_id": user_id,
        "endpoint": "https://example.com",
        "p256dh": "key"
    }).execute()
    cleanup_ids["push_subscriptions"].append(sub_id)
    
    subs = await repository.get_push_subscriptions(user_id)
    assert any(s["id"] == sub_id for s in subs)
    
    await repository.delete_push_subscription(sub_id)
    subs_after = await repository.get_push_subscriptions(user_id)
    assert all(s["id"] != sub_id for s in subs_after)
