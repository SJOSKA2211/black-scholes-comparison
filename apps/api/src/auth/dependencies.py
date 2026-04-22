"""Authentication dependencies for FastAPI endpoints."""
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.database.supabase_client import get_supabase_client
import structlog

logger = structlog.get_logger(__name__)
security = HTTPBearer()

async def get_current_user(auth: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Validates JWT token against Supabase and returns user info."""
    supabase = get_supabase_client()
    try:
        response = supabase.auth.get_user(auth.credentials)
        if response is None or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {
            "id": response.user.id,
            "email": response.user.email,
            "role": response.user.user_metadata.get("role", "researcher")
        }
    except Exception as e:
        logger.error("auth_error", error=str(e), step="auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_ws_token(websocket: WebSocket, token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Validates WebSocket token and closes connection if invalid."""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return None
        
    supabase = get_supabase_client()
    try:
        response = supabase.auth.get_user(token)
        if response is None or not response.user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return None
            
        return {
            "id": response.user.id,
            "email": response.user.email
        }
    except Exception as e:
        logger.error("ws_auth_error", error=str(e), step="auth")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Auth failed")
        return None
