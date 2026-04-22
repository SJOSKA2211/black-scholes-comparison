"""WebSocket connection manager backed by Redis pub/sub."""
from __future__ import annotations
import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from src.cache.redis_client import get_redis
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
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._listeners: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accepts a connection and adds it to the specified channel."""
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = set()
            # Start a Redis listener for this channel if not already running
            self._listeners[channel] = asyncio.create_task(self.start_redis_listener(channel))
            
        self._connections[channel].add(websocket)
        logger.info("ws_client_connected", channel=channel, total=len(self._connections[channel]), step="websocket")

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Removes a connection from the channel."""
        if channel in self._connections:
            self._connections[channel].discard(websocket)
            if not self._connections[channel]:
                # Stop listener if no more connections
                if channel in self._listeners:
                    self._listeners[channel].cancel()
                    del self._listeners[channel]
                del self._connections[channel]
        logger.info("ws_client_disconnected", channel=channel, step="websocket")

    async def broadcast(self, channel: str, message: Dict[str, Any]) -> None:
        """Sends a message to all connected clients on a channel."""
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
            redis_channel = f"ws:{channel}"
            await pubsub.subscribe(redis_channel)
            logger.info("redis_ws_listener_started", channel=redis_channel)
            
            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        await self.broadcast(channel, data)
                    except Exception as e:
                        logger.error("ws_broadcast_error", error=str(e), channel=channel)
        except asyncio.CancelledError:
            logger.info("redis_ws_listener_stopped", channel=channel)
        except Exception as e:
            logger.error("redis_ws_listener_failed", error=str(e), channel=channel)

# Singleton instance
ws_manager = WebSocketManager()
