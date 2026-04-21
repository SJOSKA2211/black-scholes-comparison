from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.websocket.manager import ws_manager
from src.auth.dependencies import verify_ws_token
import asyncio
import structlog
 
router = APIRouter()
logger = structlog.get_logger(__name__)
 
ALLOWED_CHANNELS = frozenset(["experiments","scrapers","notifications","metrics"])
 
@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """
    WebSocket endpoint. Clients connect to /ws/{channel} after authenticating.
    Token passed as query param: /ws/experiments?token=<jwt>.
    Each channel maps to a Redis pub/sub channel ws:{channel}.
    """
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4004, reason="Unknown channel")
        return
    await verify_ws_token(websocket)   # Validates JWT from query param
    await ws_manager.connect(websocket, channel)
    listener = asyncio.create_task(ws_manager.start_redis_listener(channel))
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive; client pings
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
        listener.cancel()
