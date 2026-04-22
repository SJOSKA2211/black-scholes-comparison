import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.database.repository import (
    upsert_option_parameters,
    insert_method_result,
    get_experiments,
    insert_notification,
    get_user_profile,
    upsert_user_profile,
    get_market_data,
    insert_market_data,
    get_validation_summary,
    create_scrape_run,
    update_scrape_run,
    get_scrape_runs,
    mark_notification_read,
    mark_all_notifications_read,
    get_experiment_by_id,
    get_push_subscriptions,
    delete_push_subscription,
    get_experiments_by_method
)
from src.exceptions import RepositoryError

@pytest.mark.unit
class TestRepository:
    @patch("src.database.repository.get_supabase_client")
    async def test_upsert_option_parameters_existing(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "123"}]
        
        res = await upsert_option_parameters({"strike": 100})
        assert res == "123"

    @patch("src.database.repository.get_supabase_client")
    async def test_upsert_option_parameters_new(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "456"}]
        
        res = await upsert_option_parameters({"strike": 100})
        assert res == "456"

    @patch("src.database.repository.get_supabase_client")
    @patch("src.cache.redis_client.get_redis")
    async def test_insert_method_result(self, mock_get_redis, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "res1"}]
        
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        res = await insert_method_result({"price": 10.0})
        assert res[0]["id"] == "res1"
        assert mock_redis.publish.called

    @patch("src.database.repository.get_supabase_client")
    async def test_get_experiments(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_exec = mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.range.return_value.order.return_value.execute
        mock_exec.return_value.data = [{"id": "1"}]
        mock_exec.return_value.count = 1
        
        res = await get_experiments(method_type="analytical", market_source="spy")
        assert len(res["items"]) == 1
        assert res["total"] == 1

    @patch("src.database.repository.get_supabase_client")
    async def test_insert_notification(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "notif1"}]
        
        res = await insert_notification("u1", "t", "b", "info", "web")
        assert res[0]["id"] == "notif1"

    @patch("src.database.repository.get_supabase_client")
    async def test_get_user_profile(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {"id": "u1"}
        
        res = await get_user_profile("u1")
        assert res["id"] == "u1"

    @patch("src.database.repository.get_supabase_client")
    async def test_upsert_user_profile(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.upsert.return_value.execute.return_value.data = [{"id": "u1"}]
        
        res = await upsert_user_profile({"id": "u1"})
        assert res["id"] == "u1"

    @patch("src.database.repository.get_supabase_client")
    async def test_get_market_data(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.gte.return_value.lte.return_value.order.return_value.limit.return_value.execute.return_value.data = [{"id": "m1"}]
        
        import datetime
        res = await get_market_data("spy", trade_date=datetime.date(2024, 1, 1), from_date="2024-01-01", to_date="2024-01-02")
        assert res[0]["id"] == "m1"

    @patch("src.database.repository.get_supabase_client")
    async def test_insert_market_data(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.upsert.return_value.execute.return_value.data = [{"id": "m1"}]
        
        res = await insert_market_data([{"id": "m1"}])
        assert res[0]["id"] == "m1"

    @patch("src.database.repository.get_supabase_client")
    async def test_get_validation_summary(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.execute.return_value.data = [{"mape": 0.1}]
        
        res = await get_validation_summary()
        assert res[0]["mape"] == 0.1

    @patch("src.database.repository.get_supabase_client")
    async def test_create_scrape_run(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "run1"}]
        
        res = await create_scrape_run("spy")
        assert res == "run1"

    @patch("src.database.repository.get_supabase_client")
    async def test_update_scrape_run(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "run1"}]
        
        res = await update_scrape_run("run1", {"status": "done"})
        assert res["id"] == "run1"

    @patch("src.database.repository.get_supabase_client")
    async def test_get_scrape_runs(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = [{"id": "run1"}]
        
        res = await get_scrape_runs()
        assert res[0]["id"] == "run1"

    @patch("src.database.repository.get_supabase_client")
    async def test_mark_notification_read(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        await mark_notification_read("n1")
        assert mock_client.table.called

    @patch("src.database.repository.get_supabase_client")
    async def test_mark_all_notifications_read(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        await mark_all_notifications_read("u1")
        assert mock_client.table.called

    @patch("src.database.repository.get_supabase_client")
    async def test_get_experiment_by_id(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {"id": "e1"}
        
        res = await get_experiment_by_id("e1")
        assert res["id"] == "e1"

    @patch("src.database.repository.get_supabase_client")
    async def test_get_push_subscriptions(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "s1"}]
        
        res = await get_push_subscriptions("u1")
        assert res[0]["id"] == "s1"

    @patch("src.database.repository.get_supabase_client")
    async def test_delete_push_subscription(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        await delete_push_subscription("s1")
        assert mock_client.table.called

    @patch("src.database.repository.get_supabase_client")
    async def test_get_experiments_by_method(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"id": "e1"}]
        
        res = await get_experiments_by_method("analytical")
        assert res[0]["id"] == "e1"

    @patch("src.database.repository.get_supabase_client")
    async def test_error_handling(self, mock_get_supabase):
        mock_client = MagicMock()
        mock_get_supabase.return_value = mock_client
        mock_client.table.side_effect = Exception("DB Fail")
        
        with pytest.raises(RepositoryError):
            await upsert_option_parameters({})
