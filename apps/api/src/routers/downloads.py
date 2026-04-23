"""Download router — handles CSV/JSON export generation."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import get_experiments, get_market_data
from src.storage.storage_service import upload_export

router = APIRouter(prefix="/download", tags=["Downloads"])


async def _fetch_data(resource: str) -> pd.DataFrame:
    """Fetch raw data from DB and return as DataFrame."""
    if resource == "experiments":
        results = await get_experiments(page_size=1000)
        # get_experiments returns {"items": [...], "total": ...}
        data = results.get("items", [])
    elif resource == "market_data":
        data = await get_market_data(source="spy", limit=1000)
    else:
        raise ValueError(f"Unknown resource type: {resource}")

    return pd.DataFrame(data)


def _serialize(df: pd.DataFrame, format: str) -> tuple[bytes, str]:
    """Serialize DataFrame to bytes for specific format."""
    if format == "csv":
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue(), "text/csv"
    elif format == "json":
        return df.to_json(orient="records").encode(), "application/json"
    elif format == "xlsx":
        xlsx_buffer = io.BytesIO()
        df.to_excel(xlsx_buffer, index=False)
        return (
            xlsx_buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        raise ValueError(f"Unsupported format: {format}")


async def download_resource(resource: str, format: str, user: dict[str, Any]) -> dict[str, Any]:
    """Core logic for resource download."""
    try:
        df = await _fetch_data(resource)
        if df.empty:
            raise HTTPException(status_code=404, detail="No data found for export")

        data, content_type = _serialize(df, format)
        filename = f"{resource}_export.{format}"

        # Upload to MinIO
        download_url = upload_export(data, filename, content_type)
        return {"url": download_url, "filename": filename, "expires_in": 3600}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/experiments")
async def export_experiments(
    format: str = Query("json", description="Export format (json/csv/xlsx)"),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate an export of experiments."""
    return await download_resource("experiments", format, user)


@router.get("/market_data")
async def export_market_data(
    format: str = Query("json", description="Export format (json/csv/xlsx)"),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate an export of market data."""
    return await download_resource("market_data", format, user)
