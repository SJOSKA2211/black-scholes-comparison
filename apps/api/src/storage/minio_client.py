"""MinIO client singleton — S3-compatible object storage."""

from __future__ import annotations

from functools import lru_cache

import structlog
from minio import Minio

from src.config import get_settings

logger = structlog.get_logger(__name__)

BUCKETS = ["bs-exports", "bs-scraper"]


@lru_cache(maxsize=1)
def get_minio() -> Minio:
    """Return a cached MinIO client and initialize buckets."""
    settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,  # Nginx terminates TLS; MinIO is internal
    )

    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("minio_bucket_created", bucket=bucket, step="init")
        except Exception as e:
            logger.error("minio_bucket_check_failed", bucket=bucket, error=str(e), step="init")

    return client
