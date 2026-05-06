"""MinIO client singleton — object storage (S3-compatible)."""

from __future__ import annotations

from functools import lru_cache

import structlog
from minio import Minio

from src.config import get_settings

logger = structlog.get_logger(__name__)

BUCKETS = ["bs-exports", "bs-scraper"]


@lru_cache(maxsize=1)
def get_minio() -> Minio:
    """Return a cached singleton MinIO client and ensure buckets exist."""
    settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,  # Nginx terminates TLS; MinIO is internal in Docker
    )
    for bucket in BUCKETS:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("minio_bucket_created", bucket=bucket, step="init", rows=0)
    return client
