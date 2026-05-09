"""Final websocket tests."""
from __future__ import annotations
import json, asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import WebSocket, HTTPException, status
from src.websocket.manager import WebSocketManager
from src.auth.dependencies import get_current_user, verify_ws_token

@pytest.mark.unit
@pytest.mark.asyncio
async def test_lifecycle():
    m = WebSocketManager(); ws = AsyncMock(spec=WebSocket)
    await m.connect(ws, "c1")
    # First time started
    with patch("src.websocket.manager.get_redis"):
        m.ensure_listener_started("c1")
    # Already running
    t = MagicMock(); t.done.return_value = False
    m._listeners["c1"] = t
    m.ensure_listener_started("c1")
    await m.disconnect(ws, "c1")
    await m.disconnect(ws, "c-none")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_broadcast():
    m = WebSocketManager(); ws = AsyncMock(spec=WebSocket)
    ws.send_json.side_effect = Exception("err")
    await m.connect(ws, "c1")
    await m.broadcast("c1", {"v": 1})
    assert len(m._connections.get("c1", set())) == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_listener():
    m = WebSocketManager(); r = MagicMock(); ps = AsyncMock(); r.pubsub.return_value = ps
    async def L():
        yield {"type": "message", "data": json.dumps({"a": 1})}
        yield {"type": "other"}
        raise asyncio.CancelledError()
    ps.listen.return_value = L()
    with patch("src.websocket.manager.get_redis", return_value=r):
        await m.start_redis_listener("c1")
        ps.listen.side_effect = Exception("err")
        await m.start_redis_listener("c1")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_auth():
    with patch("src.auth.dependencies.get_supabase") as su:
        c = MagicMock(); su.return_value = c
        u = MagicMock(); u.model_dump.return_value = {"id": "1"}
        c.auth.get_user.return_value = MagicMock(user=u)
        await get_current_user(MagicMock(credentials="t"))
        c.auth.get_user.return_value = MagicMock(user=None)
        with pytest.raises(HTTPException): await get_current_user(MagicMock(credentials="t"))
        c.auth.get_user.side_effect = Exception("err")
        with pytest.raises(HTTPException): await get_current_user(MagicMock(credentials="t"))

@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_token():
    ws = MagicMock(spec=WebSocket); ws.close = AsyncMock(); ws.query_params = {}
    with pytest.raises(HTTPException): await verify_ws_token(ws)
    with patch("src.auth.dependencies.get_supabase") as su:
        c = MagicMock(); su.return_value = c
        ws.query_params = {"token": "t"}
        c.auth.get_user.return_value = MagicMock(user=MagicMock())
        await verify_ws_token(ws)
        c.auth.get_user.return_value = MagicMock(user=None)
        with pytest.raises(HTTPException): await verify_ws_token(ws)
        c.auth.get_user.side_effect = Exception("err")
        with pytest.raises(HTTPException): await verify_ws_token(ws)
