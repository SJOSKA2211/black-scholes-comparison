"""API router for data downloads."""

from __future__ import annotations

import io
import time
from typing import Any

import pandas as pd
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import list_market_data, list_method_results, list_option_parameters
from src.storage.storage_service import upload_export

router = APIRouter(prefix="/api/v1/download", tags=["downloads"])
logger = structlog.get_logger(__name__)


async def _fetch_data(resource: str) -> list[dict[str, Any]]:
    """Fetch data for the requested resource from Supabase."""
    if resource == "options":
        return await list_option_parameters(limit=1000)
    elif resource == "results":
        return await list_method_results(limit=1000)
    elif resource == "market":
        return await list_market_data(limit=1000)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown resource: {resource}")


@router.get("/{resource}")
async def download_resource(
    resource: str,
    format_type: str = Query("csv", alias="format", pattern="^(csv|json|xlsx)$"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str | int]:
    """
    Generates the export file, uploads to MinIO with compression, returns a presigned URL.
    """
    logger.info(
        "download_request", resource=resource, format=format_type, user_id=current_user.get("id")
    )

    try:
        data_rows = await _fetch_data(resource)
        if not data_rows:
            # Create a sample row if no data exists to avoid empty dataframe issues
            dataframe = pd.DataFrame([{"info": f"No data found for {resource}"}])
        else:
            dataframe = pd.DataFrame(data_rows)

        if format_type == "csv":
            buffer = dataframe.to_csv(index=False).encode()
            content_type = "text/csv"
        elif format_type == "json":
            buffer = dataframe.to_json(orient="records").encode()
            content_type = "application/json"
        else:  # xlsx
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                dataframe.to_excel(writer, index=False)
            buffer = output_buffer.getvalue()
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        filename = f"{resource}_{int(time.time())}.{format_type}"
        presigned_url = upload_export(
            data=buffer, filename=filename, content_type=content_type, compress=True
        )

        return {"url": presigned_url, "filename": filename, "expires_in": 3600}
    except HTTPException:
        raise
    except Exception as error:
        logger.error("download_failed", resource=resource, error=str(error))
        raise HTTPException(status_code=500, detail="Failed to generate download") from error
