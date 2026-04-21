import io
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from src.auth.dependencies import get_current_user
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

RESOURCES = ["experiments", "market-data", "validation"]
FORMATS = ["csv", "json", "xlsx"]

@router.get("/download/{resource}")
async def download_resource(
    resource: str,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream a downloadable file of research results.
    Supports CSV, JSON, and Excel (xlsx) formats.
    """
    if resource not in RESOURCES:
        raise HTTPException(status_code=400, detail=f"Unknown resource: {resource}")

    # Dummy data for demonstration
    df = pd.DataFrame([{"id": 1, "value": "test"}])

    logger.info("download_generated",
        user_id=current_user["id"], resource=resource,
        format=format, rows=len(df))

    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={resource}.csv"})

    elif format == "json":
        content = df.to_json(orient="records", date_format="iso")
        return StreamingResponse(
            iter([content]), media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={resource}.json"})

    else:  # xlsx
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=resource)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={resource}.xlsx"})
