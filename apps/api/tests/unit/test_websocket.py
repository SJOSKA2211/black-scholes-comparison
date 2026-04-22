import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.websocket.manager import WebSocketManager
from src.websocket.channels import ALLOWED_CHANNELS
import asyncio
import json

@pytest.mark.unit
class TestWebSocketManager:
    @pytest.mark.asyncio
    async def test_connect_disconnect(self):
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        mock_ws2 = AsyncMock()
        
        with patch.object(manager, "start_redis_listener", return_value=AsyncMock()):
            # Branch 32->37: New channel
            await manager.connect(mock_ws, "test")
            assert mock_ws in manager._connections["test"]
            assert "test" in manager._listeners
            
            # Branch 32->37: Existing channel
            await manager.connect(mock_ws2, "test")
            assert mock_ws2 in manager._connections["test"]
            
            # Branch 49->55: Still has connections
            await manager.disconnect(mock_ws, "test")
            assert "test" in manager._connections
            
            # Branch 49->55: Last connection
            await manager.disconnect(mock_ws2, "test")
            assert "test" not in manager._connections
            assert "test" not in manager._listeners
            
            # Branch 47->55: Channel doesn't exist
            await manager.disconnect(mock_ws, "unknown")

    @pytest.mark.asyncio
    async def test_broadcast(self):
        manager = WebSocketManager()
        await manager.broadcast("empty", {"msg": "hi"})
        
        mock_ws = AsyncMock()
        manager._connections["test"] = {mock_ws}
        await manager.broadcast("test", {"msg": "hi"})
        mock_ws.send_json.assert_called_once_with({"msg": "hi"})
        
        mock_ws.send_json.side_effect = Exception("Dead")
        await manager.broadcast("test", {"msg": "bye"})
        assert "test" not in manager._connections

    @pytest.mark.asyncio
    @patch("src.websocket.manager.get_redis")
    async def test_redis_listener_flow(self, mock_get_redis):
        manager = WebSocketManager()
        mock_redis = MagicMock()
        
        # Manually construct mock_pubsub to handle both await and async for
        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        
        async def mock_listen():
            yield {"type": "message", "data": '{"foo": "bar"}'}
            yield {"type": "subscribe", "data": "ignore"}
            yield {"type": "message", "data": 'invalid json'}
            raise asyncio.CancelledError()
            
        mock_pubsub.listen = mock_listen
        mock_redis.pubsub.return_value = mock_pubsub
        mock_get_redis.return_value = mock_redis
        
        with patch.object(manager, "broadcast", new_callable=AsyncMock) as mock_broadcast:
            await manager.start_redis_listener("test")
            mock_broadcast.assert_called_once_with("test", {"foo": "bar"})

    @pytest.mark.asyncio
    @patch("src.websocket.manager.get_redis")
    async def test_redis_listener_error(self, mock_get_redis):
        manager = WebSocketManager()
        mock_get_redis.side_effect = Exception("Redis connection fail")
        await manager.start_redis_listener("test")

    def test_channels_import(self):
        assert "experiments" in ALLOWED_CHANNELS
