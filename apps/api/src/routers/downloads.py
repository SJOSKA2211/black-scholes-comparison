"""Download router — handles CSV/JSON export generation."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import Repository
from src.storage.storage_service import upload_export

router = APIRouter(prefix="/download", tags=["Downloads"])


async def _fetch_data(resource: str, user_id: str) -> pd.DataFrame:
    """Fetch raw data from DB and return as DataFrame."""
    repo = Repository()
    if resource == "experiments":
        data = await repo.get_experiments(user_id=user_id)
    elif resource == "market_data":
        # Simplified: fetch first 1000 market data rows for the user
        # In a real app, you'd filter by date or option_id
        data = await repo.get_market_data(option_id="all")  # Placeholder for bulk
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
        df = await _fetch_data(resource, user["id"])
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
    format: str = Query("json", pattern="^(json|csv|xlsx)$"),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate an export of experiments."""
    return await download_resource("experiments", format, user)


@router.get("/market_data")
async def export_market_data(
    format: str = Query("json", pattern="^(json|csv|xlsx)$"),
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Generate an export of market data."""
    return await download_resource("market_data", format, user)
