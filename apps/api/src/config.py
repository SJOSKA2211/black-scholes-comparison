"""Global configuration settings for the Black-Scholes Research Platform."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Adheres strictly to Section 1.2 of the Production Final mandate.
    """

    # --- Supabase ---
    supabase_url: str = Field(..., alias="SUPABASE_URL")
    supabase_db_host: str = Field(..., alias="SUPABASE_DB_HOST")
    supabase_key: str = Field(..., alias="SUPABASE_KEY")
    supabase_anon_key: str = Field(..., alias="SUPABASE_ANON_KEY")

    # --- API ---
    api_url: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    environment: str = Field("development", alias="ENVIRONMENT")

    # --- Redis ---
    redis_url: str = Field(..., alias="REDIS_URL")
    redis_password: str = Field(..., alias="REDIS_PASSWORD")

    # --- RabbitMQ ---
    rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")
    rabbitmq_user: str = Field("rabbitmq_user", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field(..., alias="RABBITMQ_PASSWORD")
    rabbitmq_management_port: int = Field(15672, alias="RABBITMQ_MANAGEMENT_PORT")

    # --- MinIO ---
    minio_endpoint: str = Field("minio:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., alias="MINIO_SECRET_KEY")
    minio_bucket_exports: str = Field("bs-exports", alias="MINIO_BUCKET_EXPORTS")
    minio_bucket_scraper: str = Field("bs-scraper", alias="MINIO_BUCKET_SCRAPER")

    # --- Observability ---
    prometheus_port: int = Field(9090, alias="PROMETHEUS_PORT")
    grafana_port: int = Field(3001, alias="GRAFANA_PORT")
    grafana_admin_password: str = Field(..., alias="GRAFANA_ADMIN_PASSWORD")

    # --- Notifications ---
    resend_api_key: str | None = Field(None, alias="RESEND_API_KEY")

    # --- Auth (OAuth) ---
    github_client_id: str | None = Field(None, alias="GITHUB_CLIENT_ID")
    github_client_secret: str | None = Field(None, alias="GITHUB_CLIENT_SECRET")
    google_client_id: str | None = Field(None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(None, alias="GOOGLE_CLIENT_SECRET")

    # --- Vercel ---
    vercel_deploy_hook: str | None = Field(None, alias="VERCEL_DEPLOY_HOOK")

    # --- Pydantic Config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of settings."""
    return Settings()  # type: ignore
