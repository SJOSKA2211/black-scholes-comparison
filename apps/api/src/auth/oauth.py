"""OAuth and JWT verification logic for Supabase Auth."""

from __future__ import annotations

from typing import cast

import jwt
import structlog
from fastapi import HTTPException, status

from src.config import get_settings

logger = structlog.get_logger(__name__)


async def verify_jwt(token: str) -> dict[str, str]:
    """
    Verifies a Supabase JWT and returns the decoded payload.
    In a real production app, this would use the Supabase public key
    or service role key to verify the signature.
    """
    settings = get_settings()
    try:
        # Supabase JWTs are signed with the project's JWT secret
        payload = jwt.decode(
            token,
            settings.supabase_key,  # Supabase uses service_role key for verification if configured
            algorithms=["HS256"],
            audience="authenticated",
        )
        return cast(dict[str, str], payload)
    except jwt.ExpiredSignatureError:
        logger.warning("auth_token_expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError as error:
        logger.warning("auth_token_invalid", error=str(error))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception as error:
        logger.error("auth_verification_failed", error=str(error))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not validate credentials",
        ) from None
