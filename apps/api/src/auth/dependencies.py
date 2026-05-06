"""Authentication dependencies for FastAPI routes."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.config import get_settings
from src.database.supabase_client import get_supabase

logger = structlog.get_logger(__name__)

# auto_error=False allows us to handle missing tokens manually for dev/test bypass
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(token: str | None = Depends(oauth2_scheme)) -> dict[str, Any]:
    """
    Validate the Supabase JWT and return the user profile.
    In development mode, bypasses validation if no token is provided.
    """
    settings = get_settings()

    # 1. Development/Test Bypass
    if settings.environment == "development" and not token:
        logger.warning("auth_bypassed", mode="development")
        return {
            "id": "de34e0d4-ad52-4ffe-9f75-1d41c83a4fb2",
            "email": "researcher@example.com",
            "role": "researcher",
        }

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Real Supabase Validation
    try:
        supabase = get_supabase()
        # verify_session is not directly in supabase-py client anymore?
        # We use auth.get_user(token)
        user_resp = supabase.auth.get_user(token)
        if not user_resp.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "id": user_resp.user.id,
            "email": user_resp.user.email,
            "role": user_resp.user.user_metadata.get("role", "researcher"),
        }
    except Exception as e:
        logger.error("auth_validation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e
