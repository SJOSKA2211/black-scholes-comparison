"""Integration tests for Supabase repository.

Verifies all 14 repository functions against real Supabase infrastructure.
"""
from __future__ import annotations
import uuid
import pytest
from datetime import date, datetime, timezone
from src.database.repository import (
    upsert_option_parameters,
    get_option_parameters,
    upsert_method_result,
    get_method_results,
    upsert_market_data,
    upsert_validation_metrics,
    create_scrape_run,
    update_scrape_run,
    create_audit_log,
    create_scrape_error,
    get_notifications,
    mark_notification_read,
    get_user_profile,
    update_user_profile
)
from src.database.supabase_client import get_supabase

# Known test user ID from previous check
TEST_USER_ID = "a24fb1a2-700a-4590-8d43-2930596a14f2"

@pytest.fixture(scope="module")
def shared_option_id():
    return str(uuid.uuid4())

@pytest.fixture(scope="module")
def shared_run_id():
    return str(uuid.uuid4())

@pytest.mark.integration
@pytest.mark.asyncio
async def test_option_parameters_lifecycle(shared_option_id):
    """Test upsert and get for option_parameters."""
    test_params = {
        "id": shared_option_id,
        "underlying_price": 150.0,
        "strike_price": 155.0,
        "maturity_years": 0.5,
        "volatility": 0.25,
        "risk_free_rate": 0.04,
        "option_type": "put",
        "market_source": "spy",
    }
    
    # Create
    resp = await upsert_option_parameters(test_params)
    assert resp[0]["id"] == shared_option_id
    
    # Retrieve
    get_resp = await get_option_parameters(shared_option_id)
    assert get_resp["underlying_price"] == 150.0
    assert get_resp["option_type"] == "put"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_method_results_lifecycle(shared_option_id):
    """Test upsert and get for method_results."""
    result_data = {
        "option_id": shared_option_id,
        "method_type": "analytical",
        "parameter_set": {"steps": 100},
        "parameter_hash": str(uuid.uuid4()), # Ensure uniqueness
        "computed_price": 10.5,
        "exec_seconds": 0.001,
        "converged": True
    }
    
    resp = await upsert_method_result(result_data)
    assert resp[0]["option_id"] == shared_option_id
    
    results = await get_method_results(shared_option_id)
    assert len(results) >= 1
    assert results[0]["computed_price"] == 10.5

@pytest.mark.integration
@pytest.mark.asyncio
async def test_market_data_lifecycle(shared_option_id):
    """Test upsert for market_data."""
    market_data = [{
        "option_id": shared_option_id,
        "trade_date": date.today().isoformat(),
        "bid_price": 10.0,
        "ask_price": 11.0,
        "volume": 100,
        "open_interest": 500,
        "data_source": "spy"
    }]
    
    resp = await upsert_market_data(market_data)
    assert resp[0]["option_id"] == shared_option_id
    assert resp[0]["bid_price"] == 10.0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_validation_metrics_lifecycle(shared_option_id):
    """Test upsert for validation_metrics."""
    # First get a method result ID
    results = await get_method_results(shared_option_id)
    method_result_id = results[0]["id"]
    
    metrics = {
        "option_id": shared_option_id,
        "method_result_id": method_result_id,
        "absolute_error": 0.01,
        "relative_pct_error": 0.1,
        "mape": 0.05
    }
    
    resp = await upsert_validation_metrics(metrics)
    assert resp[0]["option_id"] == shared_option_id
    assert resp[0]["absolute_error"] == 0.01

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_run_lifecycle(shared_run_id):
    """Test create and update for scrape_runs."""
    run_data = {
        "id": shared_run_id,
        "market": "nse",
        "scraper_class": "NseScraper",
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = await create_scrape_run(run_data)
    assert resp[0]["id"] == shared_run_id
    
    update_data = {
        "status": "success",
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "rows_scraped": 100,
        "rows_validated": 95,
        "rows_inserted": 90
    }
    update_resp = await update_scrape_run(shared_run_id, update_data)
    assert update_resp[0]["status"] == "success"
    assert update_resp[0]["rows_scraped"] == 100

@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_and_errors(shared_run_id):
    """Test audit log and scrape error creation."""
    audit_data = {
        "pipeline_run_id": shared_run_id,
        "module_name": "test_module",
        "message": "test audit",
        "rows_affected": 50
    }
    audit_resp = await create_audit_log(audit_data)
    assert audit_resp[0]["message"] == "test audit"
    
    error_data = {
        "pipeline_run_id": shared_run_id,
        "error_message": "test error",
        "source": "test_source" # Discovered mandatory column
    }
    error_resp = await create_scrape_error(error_data)
    assert error_resp[0]["error_message"] == "test error"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_notifications_lifecycle():
    """Test notification retrieval and marking as read."""
    client = get_supabase()
    notif_data = {
        "user_id": TEST_USER_ID,
        "title": "Test Notification",
        "body": "This is a test notification",
        "severity": "info",
        "channel": "in_app"
    }
    client.table("notifications").insert(notif_data).execute()

    resp = await get_notifications(TEST_USER_ID)
    assert isinstance(resp, list)
    
    unread = [n for n in resp if not n["read"]]
    if unread:
        notif_id = unread[0]["id"]
        mark_resp = await mark_notification_read(notif_id)
        assert mark_resp[0]["read"] is True

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_profile_lifecycle():
    """Test user profile retrieval and update."""
    profile = await get_user_profile(TEST_USER_ID)
    assert profile["id"] == TEST_USER_ID
    
    original_name = profile["display_name"]
    new_name = f"Test_{uuid.uuid4().hex[:8]}"
    
    update_resp = await update_user_profile(TEST_USER_ID, {"display_name": new_name})
    assert update_resp[0]["display_name"] == new_name
    
    await update_user_profile(TEST_USER_ID, {"display_name": original_name})

@pytest.fixture(scope="module", autouse=True)
async def cleanup_database(shared_option_id, shared_run_id):
    """Cleanup test data after module tests."""
    yield
    client = get_supabase()
    try:
        client.table("option_parameters").delete().eq("id", shared_option_id).execute()
        client.table("scrape_runs").delete().eq("id", shared_run_id).execute()
        client.table("audit_log").delete().eq("pipeline_run_id", shared_run_id).execute()
        client.table("scrape_errors").delete().eq("pipeline_run_id", shared_run_id).execute()
        client.table("notifications").delete().eq("user_id", TEST_USER_ID).eq("title", "Test Notification").execute()
    except Exception:
        pass
