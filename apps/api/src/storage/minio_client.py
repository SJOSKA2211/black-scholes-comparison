"""MinIO client singleton — bucket initialization."""

from __future__ import annotations

from functools import lru_cache

import structlog
from minio import Minio

from src.config import get_settings

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_minio() -> Minio:
    """Return a cached MinIO client and ensure buckets exist."""
    import urllib3

    settings = get_settings()
    logger.info("minio_client_init", endpoint=settings.minio_endpoint)

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

    try:
        # Check if host is resolvable to avoid long timeouts/retries on cloud platforms
        import socket

        host = settings.minio_host
        try:
            # getaddrinfo is more robust than gethostbyname
            socket.getaddrinfo(host, settings.minio_port)
        except (TimeoutError, socket.gaierror):
            logger.warning("minio_host_not_resolvable", host=host, step="init")
            return client

        # Ensure buckets exist
        for bucket in [settings.minio_bucket_exports, settings.minio_bucket_scraper]:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("minio_bucket_created", bucket=bucket, step="init")
    except Exception as error:
        # We catch but don't re-raise to ensure API startup continues
        logger.error("minio_bucket_check_failed", error=str(error), step="init")

    return client
