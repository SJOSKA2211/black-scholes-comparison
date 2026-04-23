import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.config import get_settings
from src.database.repository import insert_method_result
from src.main import lifespan
from fastapi import FastAPI
import asyncio

@pytest.mark.unit
async def test_config_env_property() -> None:
    settings = get_settings()
    assert settings.env == settings.environment

@pytest.mark.unit
async def test_insert_method_result_redis_failure() -> None:
    # Trigger lines 77-78 in repository.py
    mock_supabase = MagicMock()
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"id": "res1"}]
    
    mock_redis = AsyncMock()
    mock_redis.publish.side_effect = Exception("Redis Down")
    
    with patch("src.database.repository.get_supabase_client", return_value=mock_supabase), \
         patch("src.cache.redis_client.get_redis", return_value=mock_redis):
        
        # Should not raise exception because of internal try-except
        res = await insert_method_result({"price": 10}, user_id="u123")
        assert res[0]["id"] == "res1"
        assert mock_redis.publish.called

@pytest.mark.unit
async def test_lifespan_success_hit_logger() -> None:
    # Trigger line 54 in main.py
    app = FastAPI()
    
    mock_redis = MagicMock()
    mock_minio = MagicMock()
    
    with patch("src.cache.redis_client.get_redis", return_value=mock_redis), \
         patch("src.storage.minio_client.get_minio", return_value=mock_minio), \
         patch("src.main.start_consumers", new_callable=AsyncMock) as mock_start:
        
        mock_start.return_value = None
        
        async with lifespan(app):
            pass
        
        assert mock_start.called
