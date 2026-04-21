"""Storage service — uploads files to MinIO, returns presigned download URLs."""
from __future__ import annotations
import io
import datetime
from minio import Minio
from src.storage.minio_client import get_minio
import structlog
 
logger = structlog.get_logger(__name__)
 
def upload_export(
    data: bytes,
    filename: str,
    content_type: str,
    bucket: str = "bs-exports",
) -> str:
    """
    Upload binary data to MinIO and return a presigned URL.
    URL valid for 1 hour — sufficient for browser-direct download.
    """
    client: Minio = get_minio()
    object_name = f"exports/{datetime.datetime.utcnow():%Y/%m/%d}/{filename}"
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )
    logger.info("export_uploaded",object=object_name,bucket=bucket,step="storage",rows=1)
    return url
