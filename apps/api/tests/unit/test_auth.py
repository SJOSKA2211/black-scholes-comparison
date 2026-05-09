"""Unit tests for authentication dependencies."""
from __future__ import annotations
import pytest
from fastapi import HTTPException, WebSocket
from src.auth.dependencies import get_current_user, verify_ws_token
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_success() -> None:
    """Verify user extraction on valid token."""
    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_user.model_dump.return_value = {"id": "123", "email": "test@example.com"}
    mock_client.auth.get_user.return_value = MagicMock(user=mock_user)
    
    auth_creds = MagicMock(credentials="valid-token")
    
    with patch("src.auth.dependencies.get_supabase", return_value=mock_client):
        user = await get_current_user(auth_creds)
        assert user["id"] == "123"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid() -> None:
    """Verify 401 on invalid token."""
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = MagicMock(user=None)
    auth_creds = MagicMock(credentials="invalid-token")
    
    with patch("src.auth.dependencies.get_supabase", return_value=mock_client):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(auth_creds)
        assert exc.value.status_code == 401

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_exception() -> None:
    """Verify 401 on Supabase exception."""
    mock_client = MagicMock()
    mock_client.auth.get_user.side_effect = Exception("Network error")
    auth_creds = MagicMock(credentials="token")
    
    with patch("src.auth.dependencies.get_supabase", return_value=mock_client):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(auth_creds)
        assert exc.value.status_code == 401

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_ws_token_success() -> None:
    """Verify WS token validation."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.query_params = {"token": "ws-token"}
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = MagicMock(user=MagicMock())
    
    with patch("src.auth.dependencies.get_supabase", return_value=mock_client):
        token = await verify_ws_token(mock_ws)
        assert token == "ws-token"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_ws_token_missing() -> None:
    """Verify WS closure on missing token."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.query_params = {}
    mock_ws.close = AsyncMock()
    
    with pytest.raises(HTTPException):
        await verify_ws_token(mock_ws)
    assert mock_ws.close.called

@pytest.mark.unit
@pytest.mark.asyncio
async def test_verify_ws_token_invalid() -> None:
    """Verify WS closure on invalid token."""
    mock_ws = MagicMock(spec=WebSocket)
    mock_ws.query_params = {"token": "bad-token"}
    mock_ws.close = AsyncMock()
    mock_client = MagicMock()
    mock_client.auth.get_user.return_value = MagicMock(user=None)
    
    with patch("src.auth.dependencies.get_supabase", return_value=mock_client):
        with pytest.raises(HTTPException):
            await verify_ws_token(mock_ws)
    assert mock_ws.close.called
