import io

import pandas as pd
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.auth.dependencies import get_current_user

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

    from src.database import repository

    if resource == "experiments":
        res = await repository.get_experiments(page_size=1000)
        df = pd.DataFrame(res["items"])
    elif resource == "market-data":
        res = await repository.get_market_data(source="spy")
        df = pd.DataFrame(res)
    elif resource == "validation":
        res = await repository.get_validation_summary()
        df = pd.DataFrame(res)
    else:
        df = pd.DataFrame()

    logger.info(
        "download_generated",
        user_id=current_user["id"],
        resource=resource,
        format=format,
        rows=len(df),
    )

    if format == "csv":
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={resource}.csv"},
        )

    elif format == "json":
        content = df.to_json(orient="records", date_format="iso")
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={resource}.json"},
        )

    else:  # xlsx
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=resource)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={resource}.xlsx"},
        )
