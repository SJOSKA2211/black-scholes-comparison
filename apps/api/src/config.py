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
    supabase_db_host: str = Field(..., alias="SUPABASE_DB_HOST")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")

    # 2. API
    api_url: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    environment: str = Field("production", alias="ENVIRONMENT")
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
        """Alias for environment."""
        return self.environment

    # 3. Cache / Pub-Sub (Redis)
    redis_url_override: str = Field(..., alias="REDIS_URL")

    @property
    def redis_url(self) -> str:
        """Return the mandatory Redis URL."""
        return self.redis_url_override

    redis_password: str = Field(..., alias="REDIS_PASSWORD")

    # 4. Message Queue (RabbitMQ)
    rabbitmq_url_override: str = Field(..., alias="RABBITMQ_URL")

    @property
    def rabbitmq_url(self) -> str:
        """Return the mandatory RabbitMQ URL."""
        return self.rabbitmq_url_override

    # 5. Object Storage (MinIO / S3)
    minio_endpoint_override: str = Field(..., alias="MINIO_ENDPOINT")

    @property
    def minio_endpoint(self) -> str:
        """Return the mandatory MinIO endpoint."""
        return self.minio_endpoint_override

    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY")
    minio_bucket_exports: str = Field("bs-exports", alias="MINIO_BUCKET_EXPORTS")
    minio_bucket_scraper: str = Field("bs-scraper", alias="MINIO_BUCKET_SCRAPER")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")
    minio_enabled: bool = Field(True, alias="MINIO_ENABLED")

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

    model_config = SettingsConfigDict(
        env_file=".env" if not os.getenv("SKIP_DOTENV") else None,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton instance of settings."""
    return Settings()  # type: ignore


settings = get_settings()
