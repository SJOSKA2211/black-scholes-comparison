"""Unit tests for additional repository coverage."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.database.repository import (
    check_db_health,
    insert_method_result,
    upsert_option_parameters,
    upsert_price_result,
)
from src.exceptions import RepositoryError
from src.methods.base import PriceResult


@pytest.mark.unit
class TestRepositoryCoverage:
    @patch("src.database.repository.get_supabase_client")
    @patch("src.cache.redis_client.get_redis")
    async def test_insert_method_result_with_user_id(
        self, mock_get_redis, mock_get_supabase
    ) -> None:
        """Test real-time broadcast to user-specific channel."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_res = MagicMock()
        mock_res.data = [{"id": "res-1"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_res

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        await insert_method_result({"data": "val"}, user_id="user-123")

        # Verify both broadcasts
        assert mock_redis.publish.call_count == 2
        mock_redis.publish.assert_any_call("ws:experiments", '{"id": "res-1"}')
        mock_redis.publish.assert_any_call("ws:user_user-123", '{"id": "res-1"}')

    @patch("src.database.repository.insert_method_result")
    async def test_upsert_price_result(self, mock_insert) -> None:
        """Test mapping PriceResult to DB record."""
        mock_insert.return_value = [{"id": "res-1"}]
        res = PriceResult(
            computed_price=10.45,
            method_type="analytical",
            exec_seconds=0.01,
            delta=0.5,
            gamma=0.02,
            theta=-0.01,
            vega=0.1,
            rho=0.05,
        )

        result = await upsert_price_result("opt-1", res, user_id="user-1")
        assert result["id"] == "res-1"
        mock_insert.assert_called_once()
        args, kwargs = mock_insert.call_args
        assert args[0]["option_id"] == "opt-1"
        assert args[0]["parameter_set"]["delta"] == 0.5
        assert kwargs["user_id"] == "user-1"

    @patch("src.database.repository.get_supabase_client")
    async def test_check_db_health_flow(self, mock_get_supabase) -> None:
        """Test healthy and unhealthy DB states."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase

        # Healthy
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            MagicMock()
        )
        assert await check_db_health() == "healthy"

        # Unhealthy
        mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Down"
        )
        assert await check_db_health() == "unhealthy"

    @patch("src.database.repository.get_supabase_client")
    async def test_upsert_option_parameters_exception(self, mock_get_supabase) -> None:
        """Test exception handling in upsert_option_parameters."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.return_value.select.side_effect = Exception("Query error")

        with pytest.raises(RepositoryError):
            await upsert_option_parameters({"S": 100})

    @patch("src.database.repository.get_supabase_client")
    async def test_insert_method_result_exception(self, mock_get_supabase) -> None:
        """Test exception handling in insert_method_result."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        # Trigger exception on execute()
        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("Insert error")

        from src.database.repository import insert_method_result, RepositoryError
        with pytest.raises(RepositoryError):
            await insert_method_result({"data": "test"})


    @patch("src.database.repository.insert_method_result")
    async def test_upsert_price_result_none_greeks(self, mock_insert) -> None:
        """Test upsert_price_result with some None greeks."""
        mock_insert.return_value = [{"id": "res-1"}]
        res = PriceResult(
            method_type="analytical",
            computed_price=10.0,
            exec_seconds=0.1,
            parameter_set={"S": 100},
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            rho=None,
        )

        from src.database.repository import upsert_price_result
        await upsert_price_result("opt-1", res)
        args, _ = mock_insert.call_args
        assert "delta" not in args[0]["parameter_set"]

    @patch("src.database.repository.get_supabase_client")
    async def test_create_scrape_run_with_triggered_by(self, mock_get_supabase) -> None:
        """Test create_scrape_run with triggered_by parameter."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "run-1"}]

        from src.database.repository import create_scrape_run
        res = await create_scrape_run("SPY", triggered_by="user-1")
        assert res == "run-1"
        args, _ = mock_supabase.table.return_value.insert.call_args
        assert args[0]["triggered_by"] == "user-1"

