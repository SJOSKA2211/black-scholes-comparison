"""API router for WebSockets."""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.auth.dependencies import verify_ws_token
from src.websocket.manager import ws_manager

from src.websocket.channels import CHANNELS

router = APIRouter(tags=["websocket"])
logger = structlog.get_logger(__name__)

ALLOWED_CHANNELS = frozenset(CHANNELS)


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """
    WebSocket endpoint. Clients connect to /ws/{channel} after authenticating.
    Each channel maps to a Redis pub/sub channel ws:{channel}.
    """
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4004, reason="Unknown channel")
        return

    try:
        await verify_ws_token(websocket)
        await ws_manager.connect(websocket, channel)

        # Start the listener for this channel if not already started
        # In a real multi-worker setup, we might need more coordination,
        # but here we start it per connection (or once per worker).
        listener_task = asyncio.create_task(ws_manager.start_redis_listener(channel))

        try:
            while True:
                # Keep connection alive; receive pings if client sends them
                await websocket.receive_text()
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket, channel)
            listener_task.cancel()
    except Exception as error:
        logger.error("ws_endpoint_failed", channel=channel, error=str(error))
        await websocket.close(code=1011, reason="Internal error")
