"""Storage service — uploads files to MinIO, returns presigned download URLs."""

from __future__ import annotations

import datetime
import io

import structlog
from minio import Minio

from src.config import get_settings
from src.storage.minio_client import get_minio
from src.utils.compression import compress_data

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
    Optionally compresses data using Gzip (zlib).
    """
    client: Minio | None = get_minio()
    if client is None:
        logger.warning("storage_skipped", reason="disabled", filename=filename)
        return "storage_disabled_url"

    final_data = data
    final_filename = filename
    metadata: dict[str, str | list[str] | tuple[str]] = {}

    if compress and len(data) > 1024:  # Only compress if > 1KB
        final_data = compress_data(data)
        if not final_filename.endswith(".gz"):
            final_filename += ".gz"
        metadata["Content-Encoding"] = "gzip"
        logger.info("export_compressed", original_size=len(data), new_size=len(final_data))

    # Organized by date for better scalability
    object_name = f"exports/{datetime.datetime.now(datetime.UTC):%Y/%m/%d}/{final_filename}"

    client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(final_data),
        length=len(final_data),
        content_type=content_type,
        metadata=metadata,
    )

    # Generate a presigned URL that is accessible via Nginx proxy
    # The URL will contain the internal hostname (e.g. minio:9000),
    # but the client needs to access it via the public gateway /minio/
    internal_url = client.presigned_get_object(
        bucket_name=bucket,
        object_name=object_name,
        expires=datetime.timedelta(hours=1),
    )

    # Rewrite internal URL to use the public /minio proxy
    settings = get_settings()
    if "minio:9000" in internal_url:
        # Replace internal endpoint with the public API URL + /minio prefix
        # settings.api_url should be e.g. http://localhost:8000
        api_base = settings.api_url.rstrip("/")
        url = internal_url.replace(f"http://{settings.minio_endpoint}", f"{api_base}/minio")
    else:
        url = internal_url

    logger.info("export_uploaded", object=object_name, bucket=bucket, step="storage", rows=1)
    return url
