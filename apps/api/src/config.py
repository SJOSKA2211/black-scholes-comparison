from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str  # service_role key
    supabase_anon_key: str
    
    # API
    api_url: str = "http://localhost:8000"
    environment: str = "development"
    
    # Datadog
    datadog_api_key: str | None = None
    datadog_site: str = "datadoghq.com"
    
    # Notifications
    resend_api_key: str | None = None
    
    # OAuth
    github_client_id: str | None = None
    github_client_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    
    # Scraper
    playwright_headless: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
