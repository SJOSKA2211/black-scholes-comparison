"""WebSocket connection manager backed by Redis pub/sub."""
from __future__ import annotations
import asyncio
import json
from typing import Any
from fastapi import WebSocket
from src.cache.redis_client import get_redis
from src.metrics import WS_CONNECTIONS_ACTIVE
import structlog

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
        """Accept connection and add to channel."""
        await websocket.accept()
        self._connections.setdefault(channel, set()).add(websocket)
        WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(float(len(self._connections[channel])))
        logger.info("ws_client_connected", channel=channel,
                    total=len(self._connections[channel]), step="websocket")

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Discard connection from channel."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            WS_CONNECTIONS_ACTIVE.labels(channel=channel).set(float(len(self._connections[channel])))
        logger.info("ws_client_disconnected", channel=channel, step="websocket")

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Send message to all clients in a channel."""
        dead_connections: list[WebSocket] = []
        for websocket in self._connections.get(channel, set()):
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
        await pubsub.subscribe(redis_channel)
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(str(message["data"]))
                    await self.broadcast(channel, data)
        except Exception as error:
            logger.error("redis_listener_failed", channel=channel, error=str(error))
        finally:
            await pubsub.unsubscribe(redis_channel)

# Singleton instance
ws_manager = WebSocketManager()
