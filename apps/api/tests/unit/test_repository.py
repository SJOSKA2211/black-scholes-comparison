"""Unit tests for repository."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
import pytest
from src.database.repository import upsert_option_parameters

@pytest.mark.unit
@pytest.mark.asyncio
async def test_repository_upsert_logic() -> None:
    """Test repository interaction with Supabase client (mocked)."""
    with patch("src.database.repository.get_supabase") as mock_get_supabase:
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client

        # Mock the chain .table().upsert().execute()
        mock_table = MagicMock()
        mock_upsert = MagicMock()
        
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = MagicMock(data=[{"id": 1}])

        data = {"underlying_price": 100.0}
        result = await upsert_option_parameters(data)

        assert result.data[0]["id"] == 1
        mock_client.table.assert_called_with("option_parameters")
