"""Router for generating and retrieving data exports."""

from __future__ import annotations

import io
import time
from typing import Any, Dict

import pandas as pd
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_experiments, get_market_data
from src.storage.storage_service import upload_export

router = APIRouter()
logger = structlog.get_logger(__name__)


async def _fetch_data(resource: str) -> pd.DataFrame:
    """Helper to fetch data based on resource type."""
    if resource == "experiments":
        # Use get_experiments and extract data list
        results_dict = await get_experiments(page_size=1000)
        data = results_dict.get("data", [])
    elif resource == "market_data":
        data = await get_market_data(source="synthetic", limit=1000)
    else:
        raise ValueError(f"Unknown resource: {resource}")
    return pd.DataFrame(data)


def _serialize(df: pd.DataFrame, format: str) -> tuple[bytes, str]:
    """Helper to serialize DataFrame to requested format."""
    if format == "csv":
        return df.to_csv(index=False).encode(), "text/csv"
    elif format == "json":
        return df.to_json(orient="records").encode(), "application/json"
    elif format == "xlsx":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        return (
            output.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        raise ValueError(f"Unknown format: {format}")


@router.get("/{resource}")
async def download_resource(
    resource: str,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Generates the export file, uploads to MinIO, returns a presigned URL.
    The frontend redirects the browser to the URL for direct download.
    """
    try:
        df = await _fetch_data(resource)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for resource")

        data, content_type = _serialize(df, format)
        filename = f"{resource}_{int(time.time())}.{format}"
        presigned_url = upload_export(data=data, filename=filename, content_type=content_type)

        logger.info(
            "download_generated",
            resource=resource,
            format=format,
            rows=len(df),
            user_id=current_user["id"],
            step="download",
        )
        return {"url": presigned_url, "filename": filename, "expires_in": 3600}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("download_failed", error=str(e), resource=resource, step="router")
        raise HTTPException(status_code=500, detail=f"Failed to generate download: {str(e)}")
