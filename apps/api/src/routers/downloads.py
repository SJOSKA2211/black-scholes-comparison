"""API router for data downloads."""
from __future__ import annotations
import time
import io
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException
from src.auth.dependencies import get_current_user
from src.storage.storage_service import upload_export
import structlog

router = APIRouter(prefix="/api/v1/download", tags=["downloads"])
logger = structlog.get_logger(__name__)

@router.get("/{resource}")
async def download_resource(
    resource: str,
    format_type: str = Query("csv", alias="format", pattern="^(csv|json|xlsx)$"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str | int]:
    """
    Generates the export file, uploads to MinIO, returns a presigned URL.
    """
    logger.info("download_request", resource=resource, format=format_type, user_id=current_user.get("id"))
    
    try:
        data_rows: list[dict[str, Any]] = [{"status": "Placeholder data for " + resource}]
        dataframe = pd.DataFrame(data_rows)
        
        if format_type == "csv":
            buffer = dataframe.to_csv(index=False).encode()
            content_type = "text/csv"
        elif format_type == "json":
            buffer = dataframe.to_json(orient="records").encode()
            content_type = "application/json"
        else: # xlsx
            output_buffer = io.BytesIO()
            with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
                dataframe.to_excel(writer, index=False)
            buffer = output_buffer.getvalue()
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        filename = f"{resource}_{int(time.time())}.{format_type}"
        presigned_url = upload_export(
            data=buffer, 
            filename=filename, 
            content_type=content_type,
            compress=True
        )
        
        return {
            "url": presigned_url, 
            "filename": filename, 
            "expires_in": 3600
        }
    except Exception as error:
        logger.error("download_failed", resource=resource, error=str(error))
        raise HTTPException(status_code=500, detail="Failed to generate download") from error
