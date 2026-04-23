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
    import urllib3

    settings = get_settings()

    # Use custom urllib3 PoolManager with timeouts to avoid hanging on init
    http_client = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=2.0, read=5.0),
        retries=urllib3.Retry(total=1, backoff_factor=0.2),
    )

    client = Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
        http_client=http_client,
    )
    # Ensure buckets exist
    try:
        # We don't have a direct timeout for bucket_exists in minio-py,
        # but we can assume it will fail if endpoint is wrong.
        for bucket in [settings.minio_bucket_exports, settings.minio_bucket_scraper]:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("minio_bucket_created", bucket=bucket, step="init")
    except Exception as error:
        logger.error("minio_bucket_check_failed", error=str(error), step="init")

    return client
