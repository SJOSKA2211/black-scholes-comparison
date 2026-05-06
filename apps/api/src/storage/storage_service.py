"""Storage service — uploads files to MinIO, returns presigned download URLs."""
from __future__ import annotations
import io
import datetime
import gzip
from typing import Literal
from minio import Minio
from src.storage.minio_client import get_minio
import structlog

logger = structlog.get_logger(__name__)

def upload_export(
    data: bytes,
    filename: str,
    content_type: str,
    bucket: str = "bs-exports",
    compress: bool = True,
) -> str:
    """
    Upload binary data to MinIO and return a presigned URL.
    Optionally compresses data using gzip.
    URL valid for 1 hour — sufficient for browser-direct download.
    """
    client: Minio = get_minio()
    
    final_data = data
    final_filename = filename
    final_content_type = content_type
    
    if compress:
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as f:
            f.write(data)
        final_data = buffer.getvalue()
        final_filename = f"{filename}.gz"
        final_content_type = "application/gzip"
        logger.info("data_compressed", original_size=len(data), compressed_size=len(final_data))

    object_name = f"exports/{datetime.datetime.utcnow():%Y/%m/%d}/{final_filename}"
    
    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(final_data),
        length=len(final_data),
        content_type=final_content_type,
    )
    
    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )
    
    logger.info("export_uploaded", object=object_name, bucket=bucket, step="storage", rows=1)
    return url
