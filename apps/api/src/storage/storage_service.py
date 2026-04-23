"""Storage service — uploads files to MinIO, returns presigned download URLs."""

from __future__ import annotations

import datetime
import io

import structlog
from minio import Minio

from src.storage.minio_client import get_minio

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
    # Organized by date for better scalability
    object_name = f"exports/{datetime.datetime.now(datetime.UTC):%Y/%m/%d}/{filename}"

    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )

    # Generate a presigned URL that is accessible via Nginx proxy
    # The URL will contain the internal hostname, but the client will access it via /minio/
    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )

    logger.info("export_uploaded", object=object_name, bucket=bucket, step="storage", rows=1)
    return url
