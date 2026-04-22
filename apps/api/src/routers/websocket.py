"""Router for WebSocket connections."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.auth.dependencies import verify_ws_token
from src.websocket.channels import ALLOWED_CHANNELS
from src.websocket.manager import ws_manager

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.websocket("/ws/{channel}")
async def websocket_endpoint(
    websocket: WebSocket, channel: str, token: str | None = Query(None)
) -> None:
    """
    WebSocket endpoint. Clients connect to /ws/{channel}?token={jwt}.
    Validates token and subscribes to Redis pub/sub for the channel.
    """
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4004, reason="Unknown channel")
        return

    # Verify token
    user = await verify_ws_token(websocket, token)
    if not user:
        # verify_ws_token should have closed the socket already
        return

    try:
        await ws_manager.connect(websocket, channel)
        while True:
            # Keep connection alive; client can send pings
            await websocket.receive_text()
            # Handle optional incoming messages if needed
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error("ws_connection_error", error=str(e), channel=channel)
        await ws_manager.disconnect(websocket, channel)
