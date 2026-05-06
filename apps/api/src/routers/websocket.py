"""WebSocket router for real-time notifications and experiment updates."""

from __future__ import annotations

import asyncio

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.websocket.manager import ws_manager

router = APIRouter(tags=["websocket"])
logger = structlog.get_logger(__name__)

ALLOWED_CHANNELS = frozenset(["experiments", "scrapers", "notifications", "metrics"])


@router.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """
    WebSocket endpoint for real-time data push.
    Each channel maps to a Redis pub/sub channel.
    """
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4004, reason="Unknown channel")
        return

    await ws_manager.connect(websocket, channel)

    listener_task = asyncio.create_task(ws_manager.start_redis_listener(channel))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
        listener_task.cancel()
    except Exception as e:
        logger.error("websocket_error", channel=channel, error=str(e))
        await ws_manager.disconnect(websocket, channel)
        listener_task.cancel()
