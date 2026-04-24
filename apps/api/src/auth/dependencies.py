"""Authentication dependencies for FastAPI endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.supabase_client import get_supabase_client

logger = structlog.get_logger(__name__)
security = HTTPBearer()


async def get_current_user() -> dict[str, Any]:
    """Returns a default researcher user, bypassing authentication."""
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "researcher@example.com",
        "role": "researcher",
    }


async def verify_ws_token(websocket: WebSocket, token: str | None = None) -> dict[str, Any]:
    """Bypasses WebSocket token validation."""
    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "researcher@example.com",
    }
