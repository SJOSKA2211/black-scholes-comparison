"""Integration tests for WebSocket functionality.
Verifies real-time push via Redis pub/sub.
"""

import asyncio
import contextlib
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.websocket.manager import ws_manager


@pytest.mark.integration
def test_websocket_lifecycle() -> None:
    client = TestClient(app)
    # No need to mock verify_ws_token as it now bypasses by default
    with client.websocket_connect("/api/v1/ws/experiments") as websocket:
        test_msg = {"event": "new_row", "data": {"id": "456"}}
        asyncio.run(ws_manager.broadcast("experiments", test_msg))

        data = websocket.receive_json()
        assert data == test_msg


@pytest.mark.integration
def test_websocket_invalid_channels() -> None:
    client = TestClient(app)
    # Invalid channel
    with pytest.raises(Exception), client.websocket_connect("/api/v1/ws/invalid"):
        pass


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.asyncio
async def test_redis_pubsub_integration(redis) -> None:
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
        with contextlib.suppress(asyncio.CancelledError):
            await task
