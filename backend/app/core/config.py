"""Centralized Backend Application Settings and Configuration."""

from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Platform configuration loaded from environment or defaults."""

    PROJECT_NAME: str = "Smart Multizone Irrigation API"
    APP_NAME: str = "Smart Multizone Irrigation API"
    DESCRIPTION: str = "Hierarchical Adaptive Fuzzy Control System for Multizone Irrigation"
    VERSION: str = "1.0.0"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    # Supabase / PostgreSQL Credentials
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # Groq AI Service
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Local Storage & Database
    LOCAL_DB_PATH: str = "data/platform.db"
    REPORTS_DIR: str = "reports/generated"

    @property
    def has_supabase(self) -> bool:
        return bool(self.SUPABASE_URL and self.SUPABASE_ANON_KEY)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return settings
