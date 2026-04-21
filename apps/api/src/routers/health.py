from fastapi import APIRouter

from src.database.supabase_client import get_supabase_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """Returns the health status of the API and database."""
    db_status = "connected"
    try:
        # Simple query to check DB connectivity
        get_supabase_client().table("user_profiles").select(
            "count", count="exact"
        ).limit(1).execute()
    except Exception:
        db_status = "disconnected"

    return {"status": "ok", "db": db_status, "version": "1.0.0"}
