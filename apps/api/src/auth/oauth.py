import structlog

logger = structlog.get_logger(__name__)


def extract_oauth_metadata(user_data: dict) -> dict:
    """
    Extracts relevant display names and avatars from Supabase OAuth user metadata.
    """
    identities = user_data.get("identities", [])
    if not identities:
        return {}

    # Simple extraction logic for profile updates
    metadata = user_data.get("user_metadata", {})
    return {
        "full_name": metadata.get("full_name"),
        "avatar_url": metadata.get("avatar_url"),
        "provider": identities[0].get("provider") if identities else "unknown",
    }
