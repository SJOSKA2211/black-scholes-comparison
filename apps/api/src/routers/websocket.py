import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.auth.dependencies import verify_ws_token
from src.websocket.channels import ALLOWED_CHANNELS
from src.websocket.manager import ws_manager

router = APIRouter()
logger = structlog.get_logger(__name__)


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

    await verify_ws_token(websocket)  # Validates JWT from query param
    await ws_manager.connect(websocket, channel)

    # Start the Redis listener for this channel if not already running
    # In a production app, you might want to ensure only one listener per worker/channel
    listener = asyncio.create_task(ws_manager.start_redis_listener(channel))

    try:
        while True:
            # Keep connection alive; client pings or we just wait for disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
        listener.cancel()
