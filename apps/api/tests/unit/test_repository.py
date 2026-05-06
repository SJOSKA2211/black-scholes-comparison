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
        # Note: repository.py returns response.data usually, or the whole response.
        # In repository.py: return cast(dict[str, Any], response)
        # and response = query_fn() which is .execute()
        # .execute() returns a SyncResponse object with .data attribute
        # So result will be the SyncResponse object if I mock it that way.
        assert result.data == [{"id": "test-uuid"}]

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
        assert result.data == {"id": "test-uuid"}
