from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str  # service_role key
    supabase_anon_key: str

    # API
    api_url: str = "http://localhost:8000"
    environment: str = "development"

    # Infrastructure
    redis_url: str = "redis://redis:6379/0"
    redis_password: str
    
    rabbitmq_url: str = "amqp://rabbitmq_user:guest@rabbitmq:5672/"
    rabbitmq_user: str = "rabbitmq_user"
    rabbitmq_password: str
    
    minio_endpoint: str = "minio:9000"
    minio_access_key: str
    minio_secret_key: str

    # Observability
    grafana_admin_password: str

    # Notifications
    resend_api_key: str | None = None

    # OAuth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Web Push
    vapid_private_key: str | None = None

    # Scraper
    playwright_headless: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
