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
    class MockPubSub:
        def __init__(self, mode="normal"): self.mode = mode
        async def subscribe(self, *args, **kwargs): pass
        async def unsubscribe(self, *args, **kwargs): pass
        async def close(self, *args, **kwargs): pass
        async def listen(self):
            yield {"type": "message", "data": json.dumps({"a": 1})}
            yield {"type": "other"}
            if self.mode == "cancel":
                raise asyncio.CancelledError()
            # Normal exit hits 88->97
            
    m = WebSocketManager(); r = MagicMock()
    
    with patch("src.websocket.manager.get_redis", return_value=r):
        # Normal exit
        r.pubsub.return_value = MockPubSub(mode="normal")
        await m.start_redis_listener("c1")
        
        # CancelledError
        r.pubsub.return_value = MockPubSub(mode="cancel")
        await m.start_redis_listener("c1")
        
        # General exception
        ps_err = MagicMock()
        ps_err.subscribe = AsyncMock()
        ps_err.unsubscribe = AsyncMock()
        ps_err.close = AsyncMock()
        ps_err.listen = AsyncMock(side_effect=Exception("err"))
        r.pubsub.return_value = ps_err
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

@pytest.mark.unit
@pytest.mark.asyncio
async def test_ws_router():
    from src.routers.websocket import websocket_endpoint
    from fastapi import WebSocketDisconnect
    ws = AsyncMock(spec=WebSocket)
    # Test unknown channel
    await websocket_endpoint(ws, "invalid")
    ws.close.assert_called_with(code=4004, reason="Unknown channel")
    
    # Test valid channel and disconnect
    ws.receive_text.side_effect = WebSocketDisconnect()
    with patch("src.routers.websocket.verify_ws_token", AsyncMock()), \
         patch("src.routers.websocket.ws_manager") as wm:
        wm.connect = AsyncMock()
        wm.disconnect = AsyncMock()
        await websocket_endpoint(ws, "experiments")
        assert wm.connect.called
        assert wm.disconnect.called

    # Test internal error
    ws.receive_text.side_effect = Exception("err")
    with patch("src.routers.websocket.verify_ws_token", AsyncMock()), \
         patch("src.routers.websocket.ws_manager") as wm:
        wm.connect = AsyncMock()
        await websocket_endpoint(ws, "experiments")
        ws.close.assert_called_with(code=1011, reason="Internal error")
