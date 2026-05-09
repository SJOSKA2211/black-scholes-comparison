"""Unit tests for WebSocket manager and authentication dependencies."""
from __future__ import annotations
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import WebSocket, HTTPException
from src.websocket.manager import WebSocketManager
from src.auth.dependencies import verify_ws_token

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_lifecycle() -> None:
    manager = WebSocketManager()
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    await manager.connect(mock_ws, "test")
    assert "test" in manager._connections
    assert mock_ws in manager._connections["test"]
    
    # Broadcast
    await manager.broadcast("test", {"msg": "hi"})
    mock_ws.send_json.assert_called_once_with({"msg": "hi"})
    
    # Disconnect
    await manager.disconnect(mock_ws, "test")
    assert not manager._connections.get("test") # Set should be empty

@pytest.mark.unit
@pytest.mark.asyncio
async def test_websocket_manager_broadcast_dead() -> None:
    manager = WebSocketManager()
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock(side_effect=Exception("Dead"))
    await manager.connect(mock_ws, "test")
    
    await manager.broadcast("test", {"msg": "hi"})
    assert not manager._connections.get("test")
