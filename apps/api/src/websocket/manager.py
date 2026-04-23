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
        self._listeners: dict[str, asyncio.Task[None]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept connection and start listener if needed."""
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
            # Start a single Redis listener per channel across all users
            self._listeners[channel] = asyncio.create_task(self.start_redis_listener(channel))

        self._connections[channel].add(websocket)
        logger.info(
            "ws_client_connected",
            channel=channel,
            total=len(self._connections[channel]),
            step="websocket",
        )

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove connection and cleanup listener if last client."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            logger.info(
                "ws_client_disconnected",
                channel=channel,
                total=len(self._connections[channel]),
                step="websocket",
            )
            if not self._connections[channel]:
                # Last client disconnected, stop the Redis listener
                task = self._listeners.pop(channel, None)
                if task:
                    task.cancel()
                self._connections.pop(channel, None)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Send message to all clients in the channel."""
        if channel not in self._connections:
            return

        dead: list[WebSocket] = []
        for ws in self._connections[channel]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws, channel)

    async def start_redis_listener(self, channel: str) -> None:
        """Subscribe to Redis channel and forward messages to WebSocket clients."""
        try:
            redis = get_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(f"ws:{channel}")
            logger.info("redis_listener_started", channel=channel, step="websocket")

            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        await self.broadcast(channel, data)
                    except Exception as error:
                        logger.error("ws_broadcast_failed", error=str(error), channel=channel)
        except asyncio.CancelledError:
            logger.info("redis_listener_cancelled", channel=channel, step="websocket")
        except Exception as error:
            logger.error("redis_listener_failed", error=str(error), channel=channel)


# Singleton instance
ws_manager = WebSocketManager()
