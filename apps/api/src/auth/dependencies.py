"""Authentication and authorization dependencies."""

from typing import Any, cast

import jwt
import structlog
from fastapi import HTTPException, Security, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import get_settings

logger = structlog.get_logger(__name__)
security = HTTPBearer()


async def get_current_user(
    auth: HTTPAuthorizationCredentials = Security(security),
) -> dict[str, Any]:
    """Validate JWT and return user info from Supabase."""
    settings = get_settings()
    try:
        # Supabase uses standard JWTs. We can verify them using the JWT secret
        # or just call auth.get_user. For efficiency, we verify the JWT locally.
        payload = jwt.decode(
            auth.credentials,
            settings.supabase_key,  # In Supabase, the service_role key can be used
            algorithms=["HS256"],
            audience="authenticated",
        )
        return cast(dict[str, Any], payload)
    except jwt.PyJWTError as e:
        logger.warning("auth_failed", error=str(e))
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        ) from e


async def verify_ws_token(websocket: WebSocket) -> dict[str, Any]:
    """Validate JWT from query parameter for WebSockets."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4003, reason="Missing token")
        raise HTTPException(status_code=401)

    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.supabase_key, algorithms=["HS256"], audience="authenticated"
        )
        return payload
    except jwt.PyJWTError as e:
        await websocket.close(code=4003, reason="Invalid token")
        raise HTTPException(status_code=401) from e
