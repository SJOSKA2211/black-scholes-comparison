"""Unit tests for WebSocket manager and authentication dependencies."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import WebSocket
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
async def test_get_current_user_valid() -> None:
    """Verify user dependency with valid token."""
    # This is a simplified test for the dependency
    with patch("src.auth.dependencies.get_supabase") as mock_supa:
        mock_client = MagicMock()
        mock_supa.return_value = mock_client
        mock_client.auth.get_user.return_value = MagicMock(user=MagicMock(id="test-id"))
        
        user = await get_current_user("valid-token")
        assert user["id"] == "test-id"
