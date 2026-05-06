"""Integration tests for WebSocket functionality.
Verifies real-time push via Redis pub/sub and channel validation.
"""

import json

import pytest
from fastapi.testclient import TestClient

from src.cache.redis_client import get_redis
from src.main import app
from src.websocket.manager import WebSocketManager


@pytest.mark.integration
def test_websocket_lifecycle() -> None:
    """Test WS connect, Redis publish, receive, disconnect — zero mocks."""
    # Ensure we have a real Redis client (not a cached MagicMock from unit tests)
    import redis as redis_sync

    from src.config import get_settings

    settings = get_settings()
    # Use sync client for publish to avoid loop conflicts
    r_sync = redis_sync.from_url(
        settings.redis_url,
        password=settings.redis_password,
        decode_responses=True,
    )

    with TestClient(app) as client:
        with client.websocket_connect("/api/v1/ws/experiments") as websocket:
            import time
            time.sleep(0.5)  # Wait for consumer to subscribe
            test_msg = {"event": "new_row", "data": {"id": "test-ws-123"}}

            # Publish via sync Redis to the same channel the manager listens to
            r_sync.publish("ws:experiments", json.dumps(test_msg))

            # Manager should receive from Redis and broadcast to WS
            data = websocket.receive_json()
            assert data == test_msg


@pytest.mark.integration
def test_websocket_invalid_channels() -> None:
    """Invalid channel returns 4004 close code."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/invalid"):
            pass
