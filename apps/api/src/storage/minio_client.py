"""MinIO client singleton — handles bucket initialization."""
from __future__ import annotations
from functools import lru_cache
from minio import Minio
from minio.error import S3Error
from src.config import get_settings
import structlog
 
logger = structlog.get_logger(__name__)
 
BUCKETS = ["bs-exports", "bs-scraper"]
 
@lru_cache(maxsize=1)
def get_minio() -> Minio:
    """Return a cached MinIO client and ensure buckets exist."""
    settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=False,   # nginx terminates TLS; MinIO is internal
    )
    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info("minio_bucket_created", bucket=bucket, step="init", rows=0)
        except S3Error as e:
            logger.error("minio_bucket_error", bucket=bucket, error=str(e), step="init")
    return client
