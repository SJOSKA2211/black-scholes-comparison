"""WebSocket connection manager backed by Redis pub/sub."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import structlog

from src.cache.redis_client import get_redis
from src.metrics import WS_CONNECTIONS_ACTIVE

if TYPE_CHECKING:
    from fastapi import WebSocket

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
        # {channel: listener task}
        self._listeners: dict[str, asyncio.Task[None]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept connection and add to channel."""
        await websocket.accept()
        self._connections.setdefault(channel, set()).add(websocket)
        WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(float(len(self._connections[channel])))
        logger.info(
            "ws_client_connected",
            channel=channel,
            total=len(self._connections[channel]),
            step="websocket",
        )

    def ensure_listener_started(self, channel: str) -> None:
        """Start the Redis listener for a channel if not already running."""
        if channel not in self._listeners or self._listeners[channel].done():
            self._listeners[channel] = asyncio.create_task(self.start_redis_listener(channel))

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Discard connection from channel."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(
                float(len(self._connections[channel]))
            )

            # Cancel listener if no more connections
            if not self._connections[channel] and channel in self._listeners:
                self._listeners[channel].cancel()
                del self._listeners[channel]

        logger.info("ws_client_disconnected", channel=channel, step="websocket")

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Send message to all clients in a channel."""
        dead_connections: list[WebSocket] = []
        connections = self._connections.get(channel, set())
        for websocket in list(connections):
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            await self.disconnect(websocket, channel)

    async def start_redis_listener(self, channel: str) -> None:
        """Subscribe to Redis channel and forward messages to WebSocket clients."""
        redis = get_redis()
        pubsub = redis.pubsub()
        redis_channel = f"ws:{channel}"

        try:
            await pubsub.subscribe(redis_channel)
            logger.info("redis_listener_started", channel=channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(str(message["data"]))
                    await self.broadcast(channel, data)
        except asyncio.CancelledError:
            logger.info("redis_listener_cancelled", channel=channel)
        except Exception as error:
            logger.error("redis_listener_failed", channel=channel, error=str(error))
        finally:
            await pubsub.unsubscribe(redis_channel)
            await pubsub.close()


# Singleton instance
ws_manager = WebSocketManager()
