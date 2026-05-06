"""
Script to register and initialize the MinIO storage cluster.
Adheres to Zero-Mock policy by ensuring real production infrastructure is ready.
"""

import os
import sys

import httpx
import structlog
from minio import Minio

# Add apps/api to path
sys.path.append(os.path.join(os.getcwd(), "apps/api"))

from src.config import get_settings

logger = structlog.get_logger(__name__)


async def register_cluster():
    settings = get_settings()

    # 1. Fetch Credentials if a service account URL is provided
    # The user provided: http://localhost:9001/api/v1/service-account-credentials
    sa_url = os.getenv("MINIO_CLUSTER_SA_URL")
    if sa_url:
        logger.info("fetching_cluster_credentials", url=sa_url)
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(sa_url)
                if res.status_code == 200:
                    creds = res.json()
                    settings.minio_access_key = creds.get("accessKey", settings.minio_access_key)
                    settings.minio_secret_key = creds.get("secretKey", settings.minio_secret_key)
                    logger.info("cluster_credentials_updated")
        except Exception as e:
            logger.error("credential_fetch_failed", error=str(e))

    # 2. Initialize Cluster Nodes
    nodes = (
        settings.minio_cluster_nodes
        if settings.minio_cluster_enabled
        else [settings.minio_endpoint]
    )

    for node in nodes:
        logger.info("registering_node", node=node)
        try:
            client = Minio(
                node,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )

            # Ensure buckets exist on this node
            for bucket in [settings.minio_bucket_exports, settings.minio_bucket_scraper]:
                if not client.bucket_exists(bucket):
                    client.make_bucket(bucket)
                    logger.info("bucket_registered", node=node, bucket=bucket)
                else:
                    logger.info("bucket_already_exists", node=node, bucket=bucket)

        except Exception as e:
            logger.error("node_registration_failed", node=node, error=str(e))


if __name__ == "__main__":
    import asyncio

    asyncio.run(register_cluster())
