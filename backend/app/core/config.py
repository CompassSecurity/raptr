from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas.configuration import ExternalAuthConfig


class Settings(BaseSettings):
    """
    Pydantic settings class used to configure RAPTR. Reads values from .env file
    """

    # This setting must be a valid Python logging level (e.g., 'INFO', 'DEBUG')
    LOG_LEVEL: str = "INFO"

    # General settings
    APPLICATION_NAME: str = "RAPTR"
    ADMIN_EMAIL: str = "admin@raptr.app"
    ADMIN_PASSWORD: str | None = None
    MIN_PASSWORD_LENGTH: int = 8
    OTP_LOCAL_ENABLED: bool = True
    OTP_EXTERNAL_ENABLED: bool = False
    FASTAPI_DOCUMENTATION: bool | None = True

    # CORS settings
    CORS_ENABLED: bool = False
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    CORS_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_HEADERS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 600

    # Database settings
    DB_ENGINE: Literal["postgres", "sqlite"] = "postgres"
    # SQLite settings
    SQLITE_DB_PATH: str = "raptr.db"
    # PostgreSQL settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # JWT settings - SECRET_KEY must be set in .env or will be auto-generated
    SECRET_KEY: str | None = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # External Identity Providers
    EXTERNAL_AUTH_CONFIGS: list[ExternalAuthConfig] = []

    # MITRE settings
    MITRE_JSON_URL: str = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

    # Custom activity templates settings
    CUSTOM_DATA_URL: str | None = None
    CUSTOM_DATA_TOKEN: str | None = None

    # Atomic Red Team settings
    ATOMIC_RED_TEAM_URL: str = (
        "https://github.com/redcanaryco/atomic-red-team/archive/refs/heads/master.zip"
    )

    # Configuration for Pydantic to read from a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Ignore extra keys in the .env file
    )


settings = Settings()
