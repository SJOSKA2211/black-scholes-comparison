"""Authentication dependencies for FastAPI endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Depends, HTTPException, WebSocket, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.database.supabase_client import get_supabase

logger = structlog.get_logger(__name__)
security = HTTPBearer()

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security)
) -> dict[str, Any]:
    """
    Validates the Supabase JWT from the Authorization header.
    Returns the user object if valid, otherwise raises 401.
    """
    try:
        supabase = get_supabase()
        # Verify the JWT with Supabase Auth
        response = supabase.auth.get_user(auth.credentials)
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "role": response.user.user_metadata.get("role", "researcher"),
        }
    except Exception as e:
        logger.error("auth_validation_failed", error=str(e), step="auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from e

async def verify_ws_token(websocket: WebSocket) -> dict[str, Any]:
    """
    Validates the Supabase JWT passed as a query parameter for WebSockets.
    Expected URL: /ws/{channel}?token=<jwt>
    """
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("ws_auth_missing_token", step="auth")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Token missing")

    try:
        supabase = get_supabase()
        response = supabase.auth.get_user(token)
        if not response.user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=403, detail="Invalid token")
        
        return {
            "id": response.user.id,
            "email": response.user.email,
        }
    except Exception as e:
        logger.error("ws_auth_failed", error=str(e), step="auth")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=403, detail="Authentication failed") from e
