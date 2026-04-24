"""Integration tests for WebSocket functionality.
Verifies real-time push via Redis pub/sub.
"""

import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.websocket.manager import WebSocketManager, ws_manager


@pytest.mark.integration
def test_websocket_lifecycle() -> None:
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/experiments") as websocket:
        test_msg = {"event": "new_row", "data": {"id": "456"}}
        # Use a synchronous way to trigger broadcast or a separate thread
        # But easier to just use an async test for everything.
        async def trigger():
            await ws_manager.broadcast("experiments", test_msg)
        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(trigger())
        loop.close()

        data = websocket.receive_json()
        assert data == test_msg

@pytest.mark.integration
def test_websocket_invalid_channels() -> None:
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/invalid"):
            pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_extended_coverage():
    # Avoid using global ws_manager to prevent side effects
    manager = WebSocketManager()
    mock_ws = AsyncMock()
    
    # 1. Connect
    await manager.connect(mock_ws, "test-ch")
    assert "test-ch" in manager._connections
    
    # 2. Broadcast success
    await manager.broadcast("test-ch", {"hi": 1})
    mock_ws.send_json.assert_called_with({"hi": 1})
    
    # 3. Broadcast failure (line 71-72)
    mock_ws.send_json.side_effect = Exception("Fail")
    await manager.broadcast("test-ch", {"hi": 2})
    assert mock_ws not in manager._connections["test-ch"]
    
    # 4. Broadcast no connections (line 65)
    await manager.broadcast("empty", {"hi": 3})
    
    # 5. Disconnect and cleanup (line 55-60)
    mock_ws2 = AsyncMock()
    await manager.connect(mock_ws2, "test-ch")
    await manager.disconnect(mock_ws2, "test-ch")
    assert "test-ch" not in manager._connections

@pytest.mark.integration
@pytest.mark.asyncio
async def test_listener_error_paths(monkeypatch):
    manager = WebSocketManager()
    mock_pubsub = AsyncMock()
    
    # Mocking the async for loop on pubsub.listen()
    class AsyncIter:
        def __init__(self, items):
            self.items = items
        def __aiter__(self):
            return self
        async def __anext__(self):
            if not self.items:
                raise StopAsyncIteration
            return self.items.pop(0)

    mock_pubsub.listen.return_value = AsyncIter([
        {"type": "message", "data": "invalid"}, # JSON error (line 90-91)
        {"type": "message", "data": '{"ok": 1}'}, # Success
    ])
    
    mock_redis = MagicMock()
    mock_redis.pubsub.return_value = mock_pubsub
    monkeypatch.setattr("src.websocket.manager.get_redis", lambda: mock_redis)
    
    with patch.object(manager, "broadcast", AsyncMock()) as mock_b:
        # Start listener
        task = asyncio.create_task(manager.start_redis_listener("ch"))
        await asyncio.sleep(0.1)
        mock_b.assert_called_with("ch", {"ok": 1})
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    # Generic exception (line 94-95)
    mock_pubsub.listen.side_effect = Exception("Err")
    await manager.start_redis_listener("ch-err")

@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
async def test_redis_pubsub_integration(redis) -> None:
    with patch.object(ws_manager, "broadcast", new_callable=AsyncMock) as mock_broadcast:
        task = asyncio.create_task(ws_manager.start_redis_listener("scrapers"))
        await asyncio.sleep(0.1)
        payload = {"market": "spy", "status": "success"}
        await redis.publish("ws:scrapers", json.dumps(payload))
        await asyncio.sleep(0.2)
        mock_broadcast.assert_called_with("scrapers", payload)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
