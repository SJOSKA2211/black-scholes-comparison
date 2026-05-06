"""WebSocket connection manager backed by Redis pub/sub."""

import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket

from src.cache.redis_client import get_redis
from src.metrics import WS_CONNECTIONS_ACTIVE

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """
    Manages active WebSocket connections per channel.
    Subscribes to the Redis channel and broadcasts messages to all
    connected WebSocket clients for that channel.
    """

    def __init__(self) -> None:
        # {channel: set of connected WebSocket objects}
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        self._connections.setdefault(channel, set()).add(websocket)
        WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(len(self._connections[channel]))
        logger.info(
            "ws_client_connected",
            channel=channel,
            total=len(self._connections[channel]),
            step="websocket",
            rows=0,
        )

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        self._connections.get(channel, set()).discard(websocket)
        WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(
            len(self._connections.get(channel, set()))
        )
        logger.info("ws_client_disconnected", channel=channel, step="websocket", rows=0)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in self._connections.get(channel, set()):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, channel)

    async def start_redis_listener(self, channel: str) -> None:
        """Subscribe to Redis channel and forward messages to WebSocket clients."""
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"ws:{channel}")
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                data = json.loads(msg["data"])
                await self.broadcast(channel, data)


# Singleton instance — shared across all workers via Redis
ws_manager = WebSocketManager()
