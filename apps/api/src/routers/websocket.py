"""WebSocket router for real-time notifications and experiment updates."""

from __future__ import annotations

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
    Relies on the global WebSocketManager consumer for message delivery.
    """
    if channel not in ALLOWED_CHANNELS:
        await websocket.close(code=4004, reason="Unknown channel")
        return

    await ws_manager.connect(websocket, channel)

    try:
        while True:
            # Keep connection alive, wait for client to close or disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error("websocket_error", channel=channel, error=str(e))
        await ws_manager.disconnect(websocket, channel)
