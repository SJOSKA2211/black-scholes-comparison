"""Unit tests for WebSocket manager and authentication dependencies."""
from __future__ import annotations
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import WebSocket, HTTPException, status
from src.websocket.manager import WebSocketManager
from src.auth.dependencies import get_current_user, verify_ws_token

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_connect_disconnect() -> None:
    """Verify WebSocket connection lifecycle."""
    manager = WebSocketManager()
    mock_ws = AsyncMock(spec=WebSocket)
    
    await manager.connect(mock_ws, "experiments")
    assert mock_ws in manager._connections["experiments"]
    
    await manager.disconnect(mock_ws, "experiments")
    assert mock_ws not in manager._connections["experiments"]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_broadcast() -> None:
    """Verify message broadcasting."""
    manager = WebSocketManager()
    mock_ws = AsyncMock(spec=WebSocket)
    await manager.connect(mock_ws, "experiments")
    
    await manager.broadcast("experiments", {"data": "test"})
    mock_ws.send_json.assert_called_once_with({"data": "test"})

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_broadcast_error() -> None:
    """Verify handling of dead connections during broadcast."""
    manager = WebSocketManager()
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.send_json.side_effect = Exception("Connection lost")
    
    await manager.connect(mock_ws, "experiments")
    await manager.broadcast("experiments", {"data": "test"})
    
    # Connection should be discarded after failure
    assert mock_ws not in manager._connections["experiments"]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_listener() -> None:
    """Verify Redis listener task management."""
    manager = WebSocketManager()
    mock_redis = AsyncMock()
    mock_pubsub = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub
    
    # Mock pubsub.listen() as an async generator
    async def mock_listen():
        yield {"type": "message", "data": json.dumps({"status": "ready"})}
        # Task will be cancelled after one message in this test
        raise asyncio.CancelledError()
        
    mock_pubsub.listen.return_value = mock_listen()
    
    with patch("src.websocket.manager.get_redis", return_value=mock_redis):
        # We use ensure_listener_started to trigger start_redis_listener
        manager.ensure_listener_started("experiments")
        assert "experiments" in manager._listeners
        
        # Wait a bit for the task to run
        await asyncio.sleep(0.1)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_ws_token_valid() -> None:
    """Verify WebSocket token dependency with valid token."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.query_params = {"token": "valid-token"}
    
    with patch("src.auth.dependencies.get_supabase") as mock_supa:
        mock_client = MagicMock()
        mock_supa.return_value = mock_client
        mock_user = MagicMock()
        mock_client.auth.get_user.return_value = MagicMock(user=mock_user)
        
        token = await verify_ws_token(mock_ws)
        assert token == "valid-token"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_ws_token_missing() -> None:
    """Verify WebSocket token dependency with missing token."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.query_params = {}
    mock_ws.close = AsyncMock()
    
    with pytest.raises(HTTPException):
        await verify_ws_token(mock_ws)
    mock_ws.close.assert_called_once()
