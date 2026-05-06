"""Authentication dependencies for FastAPI."""
from __future__ import annotations
from typing import Any, cast
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.database.supabase_client import get_supabase
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> dict[str, Any]:
    """Verify JWT from Authorization header and return user data."""
    client = get_supabase()
    try:
        # Verify the JWT with Supabase
        user_response = client.auth.get_user(auth.credentials)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return cast(dict[str, Any], user_response.user.model_dump())
    except Exception as error:
        logger.error("auth_failed", error=str(error))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        ) from error

async def verify_ws_token(websocket: WebSocket) -> str:
    """Verify JWT from WebSocket query parameter."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        raise HTTPException(status_code=403, detail="Missing WebSocket token")
    
    client = get_supabase()
    try:
        user_response = client.auth.get_user(token)
        if not user_response.user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            raise HTTPException(status_code=403, detail="Invalid WebSocket token")
        return token
    except Exception as error:
        logger.error("ws_auth_failed", error=str(error))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Auth failed")
        raise HTTPException(status_code=403, detail="WebSocket authentication failed") from error
