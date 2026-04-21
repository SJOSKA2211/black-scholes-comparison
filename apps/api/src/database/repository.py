from typing import Any, Optional
from src.database.supabase_client import get_supabase_client
from src.exceptions import RepositoryError
import structlog

logger = structlog.get_logger(__name__)

async def upsert_option_parameters(params: dict[str, Any]) -> str:
    """Upserts option parameters and returns the ID."""
    supabase = get_supabase_client()
    try:
        # Check if exists first to maintain uniqueness as specified in schema
        response = supabase.table("option_parameters").upsert(params, on_conflict="underlying_price, strike_price, maturity_years, volatility, risk_free_rate, option_type, market_source").execute()
        if not response.data:
            raise RepositoryError("Failed to upsert option parameters")
        return response.data[0]["id"]
    except Exception as e:
        logger.error("repository_error", operation="upsert_option_parameters", error=str(e))
        raise RepositoryError(f"Database operation failed: {str(e)}")

async def insert_method_result(result: dict[str, Any]):
    supabase = get_supabase_client()
    try:
        response = supabase.table("method_results").insert(result).execute()
        return response.data
    except Exception as e:
        logger.error("repository_error", operation="insert_method_result", error=str(e))
        raise RepositoryError(f"Database operation failed: {str(e)}")

async def get_experiments(
    method_type: Optional[str] = None,
    market_source: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> dict[str, Any]:
    supabase = get_supabase_client()
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    query = supabase.table("method_results").select("*, option_parameters(*)", count="exact")
    
    if method_type:
        query = query.eq("method_type", method_type)
    if market_source:
        query = query.eq("option_parameters.market_source", market_source)
        
    response = query.range(start, end).order("run_at", desc=True).execute()
    
    total = response.count
    return {
        "items": response.data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (start + page_size) < total if total else False,
        "has_prev": page > 1
    }

async def insert_notification(
    user_id: str,
    title: str,
    body: str,
    severity: str,
    channel: str,
    action_url: Optional[str] = None
):
    supabase = get_supabase_client()
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "body": body,
            "severity": severity,
            "channel": channel,
            "action_url": action_url,
            "read": False
        }
        response = supabase.table("notifications").insert(data).execute()
        return response.data
    except Exception as e:
        logger.error("repository_error", operation="insert_notification", error=str(e))
        raise RepositoryError(f"Database operation failed: {str(e)}")

# ... additional operations will be added here
