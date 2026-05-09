"""Extended unit tests for Supabase repository layer."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.database.repository import (
    _execute_query, 
    get_method_results, 
    upsert_validation_metrics, 
    update_scrape_run,
    get_user_profile,
    list_option_parameters,
    list_market_data,
    get_notifications,
    mark_notification_read,
    update_user_profile
)
from src.exceptions import SupabaseError

@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query_error_with_message() -> None:
    """Verify error handling when Exception has a 'message' attribute."""
    class MockError(Exception):
        def __init__(self, message: str):
            self.message = message
    
    def fail():
        raise MockError("Custom message")
        
    with pytest.raises(SupabaseError, match="Custom message"):
        await _execute_query("table", "op", fail)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query_error_with_args() -> None:
    """Verify error handling when Exception has 'args'."""
    def fail():
        raise Exception("Arg message")
        
    with pytest.raises(SupabaseError, match="Arg message"):
        await _execute_query("table", "op", fail)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_query_error_generic() -> None:
    """Verify error handling when Exception has no message or args."""
    def fail():
        raise Exception()
        
    with pytest.raises(SupabaseError, match="Database error"):
        await _execute_query("table", "op", fail)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_method_results() -> None:
    """Verify get_method_results coverage."""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await get_method_results("opt-1")
        assert res == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_validation_metrics() -> None:
    """Verify upsert_validation_metrics coverage."""
    mock_client = MagicMock()
    mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await upsert_validation_metrics({"mape": 0.1})
        assert res == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_scrape_run() -> None:
    """Verify update_scrape_run coverage."""
    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await update_scrape_run("run-1", {"status": "success"})
        assert res == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_user_profile() -> None:
    """Verify get_user_profile coverage."""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(data={"id": "1"})
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await get_user_profile("u1")
        assert res == {"id": "1"}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_option_parameters_with_market() -> None:
    """Verify list_option_parameters with market filter."""
    mock_client = MagicMock()
    mock_query = mock_client.table.return_value.select.return_value.order.return_value.limit.return_value
    mock_query.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await list_option_parameters(market="spy")
        assert res == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_market_data_with_market() -> None:
    """Verify list_market_data with market filter."""
    mock_client = MagicMock()
    mock_query = mock_client.table.return_value.select.return_value.order.return_value.limit.return_value
    mock_query.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        res = await list_market_data(market="spy")
        assert res == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_notifications_and_profile() -> None:
    """Verify notifications and update profile coverage."""
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data={"id": "1"})
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        assert await get_notifications("u1") == [{"id": "1"}]
        assert await mark_notification_read("n1") == {"id": "1"}
        assert await update_user_profile("u1", {}) == {"id": "1"}
