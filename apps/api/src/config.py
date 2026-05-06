"""Configuration management using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_db_host: str
    supabase_anon_key: str

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_password: str

    # RabbitMQ
    rabbitmq_url: str
    rabbitmq_user: str = "rabbitmq_user"
    rabbitmq_password: str
    rabbitmq_management_port: int = 15672

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_exports: str = "bs-exports"
    minio_bucket_scraper: str = "bs-scraper"

    # Grafana
    grafana_admin_password: str

    # External APIs
    resend_api_key: str | None = None

    # Auth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # App
    app_env: str = "development"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    return Settings()  # type: ignore[call-arg]
