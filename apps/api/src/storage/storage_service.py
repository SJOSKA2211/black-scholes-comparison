"""Storage service — uploads files to MinIO, returns presigned download URLs."""

from __future__ import annotations

import datetime
import io
from typing import Any

import structlog
from minio import Minio

from src.storage.minio_client import get_minio
from src.utils.compression import compress_data

logger = structlog.get_logger(__name__)


def upload_export(
    data: bytes,
    filename: str,
    content_type: str,
    bucket: str = "bs-exports",
    compress: bool | None = None,
) -> str:
    """
    Upload binary data to MinIO and return a presigned URL.
    URL valid for 1 hour — sufficient for browser-direct download.
    """
    client: Minio = get_minio()
    
    # Automatic compression if > 1KB or explicitly requested
    should_compress = compress if compress is not None else (len(data) > 1024)

    metadata = {}
    if should_compress:
        data = compress_data(data)
        if not filename.endswith(".gz"):
            filename += ".gz"
        content_type = "application/gzip"
        metadata["Content-Encoding"] = "gzip"

    # Use UTC for object path partitioning
    # Python 3.10 compatible: use datetime.timezone.utc
    now = datetime.datetime.now(datetime.timezone.utc)
    object_name = f"exports/{now:%Y/%m/%d}/{filename}"

    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
        metadata=metadata,
    )

    url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )
    logger.info("export_uploaded", object=object_name, bucket=bucket, step="storage", size=len(data), compressed=compress)
    return url
