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
    redis_password: str = "redis_pass"  # noqa: S105

    rabbitmq_user: str = "research_admin"
    rabbitmq_password: str = "rabbit_pass"  # noqa: S105

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@rabbitmq:5672/"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minio_admin"
    minio_secret_key: str = "minio_secret"  # noqa: S105
    minio_secure: bool = False

    # Observability
    grafana_admin_password: str = "admin"  # noqa: S105

    # Notifications
    resend_api_key: str | None = None

    # OAuth
    gh_client_id: str | None = None
    gh_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # Web Push
    vapid_private_key: str | None = None

    # Scraper
    playwright_headless: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
