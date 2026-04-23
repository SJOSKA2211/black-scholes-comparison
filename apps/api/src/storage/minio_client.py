"""MinIO client singleton — bucket initialization."""

from __future__ import annotations

from functools import lru_cache

import structlog
from minio import Minio

from src.config import get_settings

logger = structlog.get_logger(__name__)

# Bucket names are managed in src.config (Section 1.2)


@lru_cache(maxsize=1)
def get_minio() -> Minio:
    """Return a cached MinIO client and ensure buckets exist."""
    settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )
    # Ensure buckets exist
    for bucket in [settings.minio_bucket_exports, settings.minio_bucket_scraper]:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("minio_bucket_created", bucket=bucket, step="init", rows=0)
        except Exception as error:
            logger.error("minio_bucket_check_failed", bucket=bucket, error=str(error), step="init")

    return client
