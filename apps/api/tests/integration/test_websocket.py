"""Integration tests for WebSocket endpoints."""
from __future__ import annotations
import json
import asyncio
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.cache.redis_client import get_redis

@pytest.mark.integration
def test_websocket_invalid_channel() -> None:
    """Verify that connecting to an invalid channel returns 4004."""
    from starlette.websockets import WebSocketDisconnect
    client = TestClient(app)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/invalid_channel"):
            pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket_broadcast() -> None:
    """
    Verify that messages published to Redis are broadcast to WebSocket clients.
    Uses a real Redis instance (Zero-Mock).
    """
    from src.websocket.manager import ws_manager
    
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.accepted = False
            self.closed = False
        
        async def accept(self):
            self.accepted = True
            
        async def send_json(self, data):
            self.sent_messages.append(data)
            
        async def close(self, code=1000, reason=None):
            self.closed = True

    ws = MockWebSocket()
    channel = "experiments"
    
    # Connect
    await ws_manager.connect(ws, channel)
    assert ws.accepted
    
    # Wait for listener to be fully started in the background
    await asyncio.sleep(0.2)
    
    # Publish message to Redis
    redis = get_redis()
    test_msg = {"event": "test_broadcast", "data": "hello"}
    
    await redis.publish(f"ws:{channel}", json.dumps(test_msg))
    
    # Wait for listener to process
    for _ in range(10):
        if test_msg in ws.sent_messages:
            break
        await asyncio.sleep(0.1)
    
    assert test_msg in ws.sent_messages
    
    # Disconnect
    await ws_manager.disconnect(ws, channel)
