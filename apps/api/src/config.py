"""Global configuration settings for the Black-Scholes Research Platform."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Adheres to Section 1.2 of the Production Final mandate.
    """

    # 1. Supabase
    supabase_url: str = Field("https://smawxojcohoqeqyksuvp.supabase.co", alias="SUPABASE_URL")
    supabase_db_host: str = Field(
        "db.smawxojcohoqeqyksuvp.supabase.co:5432", alias="SUPABASE_DB_HOST"
    )
    supabase_key: str = Field("dummy_service_key", alias="SUPABASE_KEY")
    supabase_anon_key: str = Field("dummy_anon_key", alias="SUPABASE_ANON_KEY")

    # 2. API
    api_url: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    environment: str = Field("production", alias="ENVIRONMENT")
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @property
    def env(self) -> str:
        """Alias for environment."""
        return self.environment

    # 3. Cache / Pub-Sub (Redis)
    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")
    redis_password: str = Field("JKmaish2025", alias="REDIS_PASSWORD")

    # 4. Message Queue (RabbitMQ)
    rabbitmq_user: str = Field("rabbitmq_user", alias="RABBITMQ_USER")
    rabbitmq_password: str = Field("JKmaish2025", alias="RABBITMQ_PASSWORD")
    rabbitmq_url_override: str | None = Field(None, alias="RABBITMQ_URL")

    @property
    def rabbitmq_url(self) -> str:
        """Construct the AMQP connection string, allowing override."""
        if self.rabbitmq_url_override:  # pragma: no cover
            return self.rabbitmq_url_override
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@rabbitmq:5672/"  # pragma: no cover

    # 5. Object Storage (MinIO / S3)
    minio_endpoint: str = Field("minio:9000", alias="MINIO_ENDPOINT")
    minio_access_key: str = Field("minio_admin", alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minio_secret", alias="MINIO_SECRET_KEY")
    minio_bucket_exports: str = Field("bs-exports", alias="MINIO_BUCKET_EXPORTS")
    minio_bucket_scraper: str = Field("bs-scraper", alias="MINIO_BUCKET_SCRAPER")
    minio_secure: bool = Field(False, alias="MINIO_SECURE")

    # 6. Observability
    prometheus_port: int = Field(9090, alias="PROMETHEUS_PORT")
    grafana_port: int = Field(3001, alias="GRAFANA_PORT")
    grafana_admin_password: str = Field("admin", alias="GRAFANA_ADMIN_PASSWORD")

    # 7. Notifications
    resend_api_key: str | None = Field(None, alias="RESEND_API_KEY")

    # 8. OAuth (Mandate requested GH_ prefix)
    gh_client_id: str | None = Field(None, alias="GH_CLIENT_ID")
    gh_client_secret: str | None = Field(None, alias="GH_CLIENT_SECRET")
    google_client_id: str | None = Field(None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(None, alias="GOOGLE_CLIENT_SECRET")

    # 9. Vercel
    vercel_deploy_hook: str | None = Field(None, alias="VERCEL_DEPLOY_HOOK")

    # 10. Scraper
    playwright_headless: bool = Field(True, alias="PLAYWRIGHT_HEADLESS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton instance of settings."""
    return Settings()  # type: ignore


settings = get_settings()
