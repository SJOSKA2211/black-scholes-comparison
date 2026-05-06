"""Global configuration settings for the Black-Scholes Research Platform."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Adheres strictly to Section 1.2 of the Production Final mandate.
    """

    # --- Supabase ---
    supabase_url: str = Field("https://placeholder.supabase.co", alias="SUPABASE_URL")
    supabase_db_host: str = Field("localhost", alias="SUPABASE_DB_HOST")
    supabase_key: str = Field("placeholder", alias="SUPABASE_KEY")
    supabase_anon_key: str = Field("placeholder", alias="SUPABASE_ANON_KEY")

    # --- API ---
    api_url: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    environment: str = Field("development", alias="ENVIRONMENT")

    # --- Redis ---
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    redis_password: str = Field("placeholder", alias="REDIS_PASSWORD")

    # --- RabbitMQ ---
    rabbitmq_url: str = Field("amqp://guest:guest@localhost:5672/", alias="RABBITMQ_URL")
    rabbitmq_user: str = Field("guest", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field("guest", alias="RABBITMQ_PASSWORD")
    rabbitmq_management_port: int = Field(15672, alias="RABBITMQ_MANAGEMENT_PORT")

    @field_validator("rabbitmq_url", mode="before")
    @classmethod
    def validate_rabbitmq_url(cls, v: Any) -> str:
        if v is None:
            return "amqp://guest:guest@localhost:5672/"
        return str(v)

    # --- MinIO ---
    minio_endpoint: str = Field("localhost:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", alias="MINIO_SECRET_KEY")
    minio_bucket_exports: str = Field("bs-exports", alias="MINIO_BUCKET_EXPORTS")
    minio_bucket_scraper: str = Field("bs-scraper", alias="MINIO_BUCKET_SCRAPER")

    # --- Observability ---
    prometheus_port: int = Field(9090, alias="PROMETHEUS_PORT")
    grafana_port: int = Field(3001, alias="GRAFANA_PORT")
    grafana_admin_password: str = Field("admin", alias="GRAFANA_ADMIN_PASSWORD")

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
