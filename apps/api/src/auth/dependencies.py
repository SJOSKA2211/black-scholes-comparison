from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from src.database.supabase_client import get_supabase_client
from src.exceptions import AuthenticationError
import structlog

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
                detail="Invalid or expired token"
            )
        
        logger.info("user_authenticated", user_id=user_response.user.id)
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "token": token
        }
    except Exception as exc:
        logger.warning("auth_validation_failed", reason=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        ) from exc
