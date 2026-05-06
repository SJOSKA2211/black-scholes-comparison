"""Unit tests for repository."""

import pytest
from unittest.mock import MagicMock, patch
from src.database.repository import Repository

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
        mock_execute = MagicMock()
        
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value = mock_upsert
        mock_upsert.execute.return_value = MagicMock(data=[{"id": 1}])
        
        repo = Repository()
        data = {"underlying_price": 100}
        result = await repo.upsert_option_parameters(data)
        
        assert result["id"] == 1
        mock_client.table.assert_called_with("option_parameters")
