"""Authentication dependencies for FastAPI endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import WebSocket
from fastapi.security import HTTPBearer

logger = structlog.get_logger(__name__)
security = HTTPBearer()


async def get_current_user() -> dict[str, Any]:
    """Returns a default researcher user, bypassing authentication."""
    return {
        "id": "a24fb1a2-700a-4590-8d43-2930596a14f2",
        "email": "researcher@example.com",
        "role": "researcher",
    }


async def verify_ws_token(websocket: WebSocket, token: str | None = None) -> dict[str, Any]:
    """Bypasses WebSocket token validation."""
    return {
        "id": "a24fb1a2-700a-4590-8d43-2930596a14f2",
        "email": "researcher@example.com",
    }
