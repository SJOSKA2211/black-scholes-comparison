import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.database.supabase_client import get_supabase_client

security = HTTPBearer()
logger = structlog.get_logger(__name__)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate the Bearer JWT from Supabase Auth.
    Attached to every protected FastAPI route via Depends().
    Raises HTTP 401 if token is missing, expired, or invalid.
    """
    token = credentials.credentials
    supabase = get_supabase_client()
    try:
        # get_user() validates the JWT with the Supabase server
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        # Fetch profile for role-based access control
        profile_res = (
            supabase.table("user_profiles")
            .select("role")
            .eq("id", user_response.user.id)
            .execute()
        )
        role = profile_res.data[0]["role"] if profile_res.data else "researcher"

        logger.info("user_authenticated", user_id=user_response.user.id, role=role)
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "token": token,
            "role": role,
        }
    except Exception as exc:
        logger.warning("auth_validation_failed", reason=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc
