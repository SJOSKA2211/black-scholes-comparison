"""Additional unit tests for WebSocketManager coverage."""
from __future__ import annotations
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.websocket.manager import WebSocketManager

class MockAsyncIterator:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_listener_loop() -> None:
    """Verify that the redis listener processes messages correctly."""
    manager = WebSocketManager()
    ws = AsyncMock()
    # Mock WebSocket.accept()
    ws.accept = AsyncMock()
    await manager.connect(ws, "experiments")
    
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()
    mock_redis.pubsub.return_value = mock_pubsub
    
    # pubsub.subscribe and unsubscribe are async in redis-py async
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    
    message = {"type": "message", "channel": b"ws:experiments", "data": json.dumps({"status": "completed"})}
    # listen() is a sync call that returns an async iterator
    mock_pubsub.listen.return_value = MockAsyncIterator([message])
    
    with patch("src.websocket.manager.get_redis", return_value=mock_redis):
        try:
            await manager.start_redis_listener("experiments")
        except StopAsyncIteration:
            pass
            
    # Verify the message was broadcast (ws.send_json called)
    ws.send_json.assert_called_with({"status": "completed"})
