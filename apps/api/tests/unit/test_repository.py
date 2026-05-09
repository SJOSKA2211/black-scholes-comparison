"""Unit tests for Supabase repository layer with mocks."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.database.repository import upsert_option_parameters, get_option_parameters

@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_option_parameters_unit() -> None:
    """Verify repository upsert logic using mocks."""
    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mock_upsert = mock_table.upsert.return_value
    mock_upsert.execute.return_value = MagicMock(data=[{"id": "test-uuid"}])
    
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        # The execute() call is inside a lambda, so we need to mock it properly.
        # But wait, repository.py uses a lambda that calls .execute().
        # So we just need to ensure the mock is available when the lambda runs.
        result = await upsert_option_parameters({
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call"
        })
        assert result == [{"id": "test-uuid"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_option_parameters_unit() -> None:
    """Verify repository query logic using mocks."""
    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mock_select = mock_table.select.return_value
    mock_eq = mock_select.eq.return_value
    mock_single = mock_eq.single.return_value
    mock_single.execute.return_value = MagicMock(data={"id": "test-uuid"})
    
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        result = await get_option_parameters("test-uuid")
        assert result == {"id": "test-uuid"}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_method_result() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    from src.database.repository import upsert_method_result
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        result = await upsert_method_result({"price": 10.0})
        assert result == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_market_data() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    from src.database.repository import upsert_market_data
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        result = await upsert_market_data([{"bid": 1.0}])
        assert result == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_functions() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    from src.database.repository import list_option_parameters, list_method_results, list_market_data
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        assert await list_option_parameters() == [{"id": "1"}]
        assert await list_method_results() == [{"id": "1"}]
        assert await list_market_data() == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_operational_tables() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    from src.database.repository import create_scrape_run, create_audit_log, create_scrape_error
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        assert await create_scrape_run({}) == [{"id": "1"}]
        assert await create_audit_log({}) == [{"id": "1"}]
        assert await create_scrape_error({}) == [{"id": "1"}]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_user_and_notifications() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
    from src.database.repository import get_notifications, mark_notification_read, update_user_profile
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        # We need to mock .update().eq().execute() for mark_notification_read
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{"id": "1"}])
        assert await mark_notification_read("1") is not None
        assert await get_notifications("u1") is not None
        assert await update_user_profile("u1", {}) is not None
