"""Configuration management using Pydantic Settings."""
from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Platform configuration settings."""
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App
    app_env: str = "development"
    debug: bool = True
    api_url: str = "http://localhost:8000"

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_anon_key: str
    supabase_db_host: str

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_password: str | None = None

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_exports: str = "bs-exports"
    minio_bucket_scraper: str = "bs-scraper"

    # Grafana
    grafana_admin_password: str

    # OAuth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Email (Resend)
    resend_api_key: str | None = None

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings object."""
    # Note: pydantic-settings automatically loads from environment or .env
    return Settings() # type: ignore[call-arg]
