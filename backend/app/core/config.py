"""
Centralized configuration using Pydantic Settings.
Loads environment variables from .env file.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Upstox API Configuration
    UPSTOX_API_KEY: str
    UPSTOX_API_SECRET: str
    UPSTOX_ACCESS_TOKEN: str

    # Application Configuration
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENV == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
