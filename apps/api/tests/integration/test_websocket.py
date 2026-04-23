"""Integration tests for WebSocket functionality.
Verifies real-time push via Redis pub/sub.
"""
import json
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from src.main import app
from src.websocket.manager import ws_manager

@pytest.mark.integration
def test_websocket_lifecycle():
    client = TestClient(app)
    # Mock verify_ws_token to return a user
    with patch("src.routers.websocket.verify_ws_token", new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {"id": "test-user"}
        
        # 1. Connect to valid channel
        with client.websocket_connect("/api/v1/ws/experiments?token=fake") as websocket:
            # 2. Test Broadcast via ws_manager directly
            test_msg = {"event": "new_row", "data": {"id": "456"}}
            # We need to run broadcast in the event loop that TestClient uses, 
            # but TestClient's websocket is synchronous.
            # However, ws_manager.broadcast is async. 
            # We can use asyncio.run or wait for it.
            asyncio.run(ws_manager.broadcast("experiments", test_msg))
            
            data = websocket.receive_json()
            assert data == test_msg

@pytest.mark.integration
def test_websocket_invalid_channels():
    client = TestClient(app)
    # Invalid channel
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/invalid?token=fake") as websocket:
            pass

@pytest.mark.integration
def test_websocket_unauthorized():
    client = TestClient(app)
    # verify_ws_token should raise if no mock, but let's test the endpoint logic
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/experiments?token=invalid") as websocket:
            pass

@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
async def test_redis_pubsub_integration(redis):
    """Verifies that a message published to Redis is received by the WebSocket manager."""
    # This test is more of a unit/integration test for the manager logic
    with patch.object(ws_manager, "broadcast", new_callable=AsyncMock) as mock_broadcast:
        # Start listener in background
        task = asyncio.create_task(ws_manager.start_redis_listener("scrapers"))
        
        # Wait a bit for subscription
        await asyncio.sleep(0.1)
        
        # Publish to Redis
        payload = {"market": "spy", "status": "success"}
        await redis.publish("ws:scrapers", json.dumps(payload))
        
        # Wait for listener to catch it
        await asyncio.sleep(0.2)
        
        mock_broadcast.assert_called_with("scrapers", payload)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
