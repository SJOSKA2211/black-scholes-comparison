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
@pytest.mark.asyncio
async def test_websocket_lifecycle() -> None:
    client = TestClient(app)
    # TestClient.websocket_connect is a context manager, but it doesn't need to be awaited
    with client.websocket_connect("/api/v1/ws/experiments") as websocket:
        test_msg = {"event": "new_row", "data": {"id": "456"}}
        
        # Publish to Redis
        import json
        from src.cache.redis_client import get_redis
        redis = get_redis()
        await asyncio.sleep(0.5) # Wait for subscription
        await redis.publish("ws:experiments", json.dumps(test_msg))

        data = websocket.receive_json()
        assert data == test_msg

@pytest.mark.integration
def test_websocket_invalid_channels() -> None:
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/invalid"):
            pass
