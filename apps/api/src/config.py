"""Global configuration settings for the Black-Scholes Research Platform."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Adheres to Section 1.2 of the Production Final mandate.
    """

    # 1. Supabase
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_db_host: str = Field(
        "db.smawxojcohoqeqyksuvp.supabase.co:5432", alias="SUPABASE_DB_HOST"
    )
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_anon_key: str = Field("dummy_anon_key", alias="SUPABASE_ANON_KEY")

    # 2. API
    api_url: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    environment: str = Field("development", alias="ENVIRONMENT")
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:8000",
        "https://localhost",
        "https://black-scholes-comparison.vercel.app",
        "https://*.vercel.app",
        "https://*.railway.app",
    ]

    @property
    def env(self) -> str:
        """Alias for environment with auto-detection for cloud platforms."""
        if os.getenv("RENDER") or os.getenv("RAILWAY_STATIC_URL"):
            return "production"
        return self.environment

    # 3. Cache / Pub-Sub (Redis)
    redis_url_override: str = Field("redis://redis:6379/0", alias="REDIS_URL")
    redis_cluster_enabled: bool = Field(False, alias="REDIS_CLUSTER_ENABLED")

    @property
    def redis_url(self) -> str:
        """Return the Redis URL."""
        return self.redis_url_override

    redis_password: str = Field("JKmaish2025", alias="REDIS_PASSWORD")

    # 4. Message Queue (RabbitMQ)
    rabbitmq_url_override: str = Field(
        "amqp://rabbitmq_user:JKmaish2025@rabbitmq:5672/", alias="RABBITMQ_URL"
    )

    @property
    def rabbitmq_url(self) -> str:
        """Return the RabbitMQ URL."""
        return self.rabbitmq_url_override

    # 5. Object Storage (MinIO / S3)
    minio_endpoint_override: str = Field("minio:9000", alias="MINIO_ENDPOINT")

    @property
    def minio_endpoint(self) -> str:
        """Return the MinIO endpoint."""
        return self.minio_endpoint_override

    @property
    def minio_host(self) -> str:
        """Extract host from endpoint."""
        return self.minio_endpoint_override.split(":")[0]

    @property
    def minio_port(self) -> int:
        """Extract port from endpoint."""
        parts = self.minio_endpoint_override.split(":")
        return int(parts[1]) if len(parts) > 1 else 9000

    minio_access_key: str = Field("IH8P9j7hVWrapfay7rTv", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("PdcNNjWEvo28vnuxSfdWAZNgkCBCut4G5dPi77Yk", alias="MINIO_SECRET_KEY")
    minio_bucket_exports: str = Field("bs-exports", alias="MINIO_BUCKET_EXPORTS")
    minio_bucket_scraper: str = Field("bs-scraper", alias="MINIO_BUCKET_SCRAPER")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")
    minio_enabled: bool = Field(True, alias="MINIO_ENABLED")
    minio_cluster_enabled: bool = Field(False, alias="MINIO_CLUSTER_ENABLED")
    minio_cluster_nodes: list[str] = Field(["minio:9000"], alias="MINIO_CLUSTER_NODES")

    # 6. Observability
    prometheus_port: int = Field(9090, alias="PROMETHEUS_PORT")
    grafana_port: int = Field(3001, alias="GRAFANA_PORT")
    grafana_admin_password: str = Field("admin", alias="GRAFANA_ADMIN_PASSWORD")

    # 7. Notifications
    resend_api_key: str | None = Field(None, alias="RESEND_API_KEY")

    # 9. Vercel
    vercel_deploy_hook: str | None = Field(None, alias="VERCEL_DEPLOY_HOOK")

    # 10. Scraper
    playwright_headless: bool = Field(True, alias="PLAYWRIGHT_HEADLESS")

    # 11. Compression
    gzip_enabled: bool = Field(True, alias="GZIP_ENABLED")
    gzip_min_size: int = Field(1000, alias="GZIP_MIN_SIZE")
    gzip_level: int = Field(9, alias="GZIP_LEVEL")

    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            "apps/api/.env",
            "../.env",
            "../../.env"
        ) if not os.getenv("SKIP_DOTENV") else None,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton instance of settings."""
    return Settings()  # type: ignore


settings = get_settings()
