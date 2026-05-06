"""WebSocket connection manager backed by Redis pub/sub."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket

from src.cache.redis_client import get_redis

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
        self._consumer_task: asyncio.Task | None = None

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept a new WebSocket connection and add to the channel."""
        await websocket.accept()
        self._connections.setdefault(channel, set()).add(websocket)
        logger.info(
            "ws_client_connected",
            channel=channel,
            total=len(self._connections[channel]),
            step="websocket",
        )

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Discard a WebSocket connection from the channel."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            if not self._connections[channel]:
                del self._connections[channel]
        logger.info("ws_client_disconnected", channel=channel, step="websocket")

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Broadcast a message to all clients in a channel."""
        if channel not in self._connections:
            return

        dead_connections: list[WebSocket] = []
        for ws in self._connections[channel]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        for ws in dead_connections:
            await self.disconnect(ws, channel)

    async def start_consumer(self) -> None:
        """Global Redis consumer — listens to ws:* and broadcasts."""
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.psubscribe("ws:*")

        logger.info("ws_global_consumer_started")
        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    # Channel format from Redis: ws:experiments
                    full_channel = (
                        message["channel"].decode()
                        if isinstance(message["channel"], bytes)
                        else message["channel"]
                    )
                    channel = full_channel.replace("ws:", "")
                    data = json.loads(message["data"])
                    await self.broadcast(channel, data)
        except asyncio.CancelledError:
            await pubsub.punsubscribe("ws:*")
            logger.info("ws_global_consumer_stopped")
        except Exception as e:
            logger.error("ws_consumer_error", error=str(e))


# Singleton instance
ws_manager = WebSocketManager()
