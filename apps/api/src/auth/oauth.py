"""OAuth metadata extraction and profile synchronization."""

from __future__ import annotations

from typing import Any, Dict

import structlog

from src.database import repository

logger = structlog.get_logger(__name__)


async def sync_user_profile(user_data: Dict[str, Any]) -> Dict[str, Any]:
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
