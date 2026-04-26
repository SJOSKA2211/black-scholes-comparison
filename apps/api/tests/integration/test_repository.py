"""Integration tests for the repository layer.
Covers all CRUD operations against real Supabase.
"""

import datetime
import uuid
import asyncio
import pytest
from src.database import repository
from src.exceptions import RepositoryError
from src.methods.base import PriceResult

@pytest.fixture
async def cleanup_ids():
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
    for table, ids in to_cleanup.items():
        if ids:
            try:
                id_list = [str(i) for i in ids]
                if table == "market_data":
                    supabase.table(table).delete().in_("option_id", id_list).execute()
                else:
                    supabase.table(table).delete().in_("id", id_list).execute()
            except Exception as e:
                print(f"Cleanup failed for {table}: {e}")

@pytest.fixture
async def test_user_id():
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    res = supabase.table("user_profiles").select("id").limit(1).execute()
    if res.data:
        return res.data[0]["id"]
    return "de34e0d4-ad52-4ffe-9f75-1d41c83a4fb2"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_option_parameters(sample_option_params, cleanup_ids) -> None:
    option_id = await repository.upsert_option_parameters(sample_option_params)
    assert uuid.UUID(option_id)
    cleanup_ids["option_parameters"].append(option_id)
    # Hit existing branch
    option_id_2 = await repository.upsert_option_parameters(sample_option_params)
    assert option_id == option_id_2

@pytest.mark.integration
@pytest.mark.asyncio
async def test_price_result_flow(sample_option_params, cleanup_ids) -> None:
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)
    # Include greek for line 97
    res = await repository.upsert_price_result(option_id, PriceResult(method_type="analytical", computed_price=10.5, exec_seconds=0.001, delta=0.5))
    cleanup_ids["method_results"].append(res["id"])
    assert (await repository.get_experiment_by_id(res["id"]))["id"] == res["id"]
    assert any(e["id"] == res["id"] for e in await repository.get_experiments_by_method("analytical"))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_profile_operations(cleanup_ids, test_user_id) -> None:
    user_id = test_user_id
    await repository.upsert_user_profile({"id": user_id, "display_name": "T"})
    assert (await repository.get_user_profile(user_id))["display_name"] == "T"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_notification_workflow(cleanup_ids, test_user_id) -> None:
    user_id = test_user_id
    notifs = await repository.insert_notification(user_id, "T", "B", "info", "in_app")
    notif_id = notifs[0]["id"]
    assert any(n["id"] == notif_id for n in await repository.get_notifications(user_id, unread_only=True))
    await repository.mark_notification_read(notif_id)
    await repository.mark_all_notifications_read(user_id)
    assert all(n["id"] != notif_id for n in await repository.get_notifications(user_id, unread_only=True))
    # Unread only = False
    assert any(n["id"] == notif_id for n in await repository.get_notifications(user_id, unread_only=False))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_operations(sample_option_params, cleanup_ids) -> None:
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)
    today = datetime.date.today()
    await repository.insert_market_data([{"option_id": option_id, "trade_date": today.isoformat(), "data_source": "spy"}])
    cleanup_ids["market_data"].append(option_id)
    assert any(d["option_id"] == option_id for d in await repository.get_market_data("spy", trade_date=today))

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_run_and_audit(cleanup_ids) -> None:
    run_id = await repository.create_scrape_run("spy")
    cleanup_ids["scrape_runs"].append(run_id)
    await repository.update_scrape_run(run_id, {"status": "success"})
    await repository.create_audit_log(run_id, "step", "status")
    # Audit fail mock
    from unittest.mock import MagicMock
    mock_sb = MagicMock()
    mock_sb.table.side_effect = Exception("Audit Fail")
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(repository, "get_supabase_client", lambda: mock_sb)
        await repository.create_audit_log(run_id, "f", "f")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_db_health_and_validation() -> None:
    assert (await repository.check_db_health()) == "healthy"
    assert isinstance(await repository.get_validation_summary(), list)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_filters(sample_option_params, cleanup_ids) -> None:
    params = sample_option_params.copy()
    params["market_source"] = "nse"
    option_id = await repository.upsert_option_parameters(params)
    cleanup_ids["option_parameters"].append(option_id)
    res = await repository.upsert_price_result(option_id, PriceResult(method_type="trinomial", computed_price=15.0, exec_seconds=0.1))
    cleanup_ids["method_results"].append(res["id"])
    
    # Method type filter
    f1 = await repository.get_experiments(method_type="trinomial")
    assert any(e["id"] == res["id"] for e in f1["items"])
    # Market source filter
    f2 = await repository.get_experiments(market_source="nse")
    assert any(e["id"] == res["id"] for e in f2["items"])
    
    # Market data filters
    today = datetime.date.today()
    await repository.insert_market_data([{"option_id": option_id, "trade_date": today.isoformat(), "data_source": "nse"}])
    cleanup_ids["market_data"].append(option_id)
    assert len(await repository.get_market_data("nse", from_date=today.isoformat())) >= 1
    assert len(await repository.get_market_data("nse", to_date=today.isoformat())) >= 1

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_listing(cleanup_ids) -> None:
    # Use a valid market name from the CHECK constraint
    run_id = await repository.create_scrape_run("spy")
    cleanup_ids["scrape_runs"].append(run_id)
    
    runs = await repository.get_scrape_runs(limit=100)
    assert any(str(r["id"]) == str(run_id) for r in runs)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_publish_user(sample_option_params, cleanup_ids, test_user_id) -> None:
    option_id = await repository.upsert_option_parameters(sample_option_params)
    cleanup_ids["option_parameters"].append(option_id)
    await repository.upsert_price_result(option_id, PriceResult(method_type="analytical", computed_price=10.0, exec_seconds=0.1), user_id=test_user_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_unhealthy(monkeypatch) -> None:
    monkeypatch.setattr(repository, "get_supabase_client", lambda: exec("raise(Exception('Down'))"))
    assert (await repository.check_db_health()) == "unhealthy"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_exceptions(monkeypatch) -> None:
    from unittest.mock import MagicMock
    mock_sb = MagicMock()
    mock_sb.table.side_effect = Exception("Err")
    monkeypatch.setattr(repository, "get_supabase_client", lambda: mock_sb)
    methods = [
        lambda: repository.insert_notification("u", "t", "b", "i", "c"),
        lambda: repository.get_user_profile("u"),
        lambda: repository.upsert_user_profile({"id": "u"}),
        lambda: repository.get_market_data("s"),
        lambda: repository.insert_market_data([{"o": "id"}]),
        lambda: repository.get_validation_summary(),
        lambda: repository.create_scrape_run("m"),
        lambda: repository.update_scrape_run("id", {}),
        lambda: repository.get_scrape_runs(),
        lambda: repository.get_notifications("u"),
        lambda: repository.mark_notification_read("id"),
        lambda: repository.mark_all_notifications_read("u"),
        lambda: repository.get_push_subscriptions("u"),
        lambda: repository.delete_push_subscription("id"),
        lambda: repository.get_experiments_by_method("m"),
        lambda: repository.get_experiment_by_id("id"),
        lambda: repository.get_experiments(),
        lambda: repository.upsert_option_parameters({"o": "p"}),
        lambda: repository.insert_method_result({"r": "es"})
    ]
    for m in methods:
        with pytest.raises(RepositoryError):
            await m()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_push_subs(cleanup_ids, test_user_id) -> None:
    user_id = test_user_id
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    sub_id = str(uuid.uuid4())
    supabase.table("push_subscriptions").insert({"id": sub_id, "user_id": user_id, "subscription_info": {"endpoint": "https://e.com", "keys": {"p": "k"}}}).execute()
    cleanup_ids["push_subscriptions"].append(sub_id)
    assert any(s["id"] == sub_id for s in await repository.get_push_subscriptions(user_id))
    await repository.delete_push_subscription(sub_id)
