"""Storage service — uploads files to MinIO, returns presigned download URLs."""

from __future__ import annotations

import datetime
import gzip
import io
from typing import TYPE_CHECKING

import structlog

from src.metrics import MINIO_UPLOADS_TOTAL
from src.storage.minio_client import get_minio

if TYPE_CHECKING:
    from minio import Minio

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
    URL valid for 1 hour.
    """
    client: Minio = get_minio()

    if compress:
        compressed_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=compressed_buffer, mode="wb") as f:
            f.write(data)
        data = compressed_buffer.getvalue()
        filename = f"{filename}.gz"
        content_type = "application/gzip"

    object_name = f"exports/{datetime.datetime.utcnow():%Y/%m/%d}/{filename}"

    try:
        client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        MINIO_UPLOADS_TOTAL.labels(bucket=bucket).inc()
    except Exception as e:
        logger.error(
            "minio_upload_failed", bucket=bucket, object=object_name, error=str(e), step="storage"
        )
        raise

    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )

    logger.info("export_uploaded", object=object_name, bucket=bucket, step="storage")
    return url


def upload_scraper_artifact(
    data: bytes,
    filename: str,
    content_type: str,
) -> str:
    """Upload raw scraper artifacts to MinIO."""
    return upload_export(data, filename, content_type, bucket="bs-scraper", compress=True)
