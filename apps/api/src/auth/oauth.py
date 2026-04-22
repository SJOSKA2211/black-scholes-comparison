"""OAuth metadata extraction and profile synchronization."""

from __future__ import annotations

from typing import Any, cast

import structlog

from src.database import repository

logger = structlog.get_logger(__name__)


import httpx
from src.config import settings
from src.exceptions import AuthenticationError

async def get_github_user(code: str) -> dict[str, Any]:
    """Exchanges GitHub code for user data."""
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_res.status_code != 200:
            raise AuthenticationError("GitHub token exchange failed")
        
        token = token_res.json().get("access_token")
        if not token:
            raise AuthenticationError("No access token returned from GitHub")

        # Get user data
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        if user_res.status_code != 200:
            raise AuthenticationError("GitHub user fetch failed")
        
        return cast("dict[str, Any]", user_res.json())

async def get_google_user(code: str) -> dict[str, Any]:
    """Exchanges Google code for user data."""
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.api_url}/api/v1/auth/callback/google"
            }
        )
        if token_res.status_code != 200:
            raise AuthenticationError("Google token exchange failed")
        
        token = token_res.json().get("access_token")
        if not token:
            raise AuthenticationError("No access token returned from Google")

        # Get user data
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token}"}
        )
        if user_res.status_code != 200:
            raise AuthenticationError("Google user fetch failed")
        
        return cast("dict[str, Any]", user_res.json())

async def sync_user_profile(user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Synchronizes Supabase auth user data with the public user_profiles table.
    Called during the auth callback flow.
    """
    user_id = user_data.get("id")
    if not user_id:
        raise ValueError("Missing user ID in metadata")

    metadata = user_data.get("user_metadata", {})
    email = user_data.get("email")

    profile_data = {
        "id": user_id,
        "display_name": metadata.get("full_name")
        or metadata.get("name")
        or (email.split("@")[0] if email else "User"),
        "avatar_url": metadata.get("avatar_url"),
        "role": "researcher",  # Default role
    }

    try:
        profile = await repository.upsert_user_profile(profile_data)
        logger.info("user_profile_synced", user_id=user_id)
        return profile
    except Exception as e:
        logger.error("profile_sync_failed", user_id=user_id, error=str(e))
        raise
