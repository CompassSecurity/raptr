from typing import Literal

from pydantic import BaseModel


class ExternalAuthConfig(BaseModel):
    """
    Configuration for an external authentication provider
    """

    name: str
    configuration: str
    issuer: str
    jwks_url: str
    audience: str
    scope: str
    username_claim: str
    client_id: str
    trusted_email_domains: list[str]


class ExternalAuthProvider(BaseModel):
    """
    Configuration for an external authentication provider exposed to frontend
    """

    name: str
    authority: str
    client_id: str
    scope: str


class Configuration(BaseModel):
    """
    Configuration model for RAPTR
    """

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    APPLICATION_NAME: str
    FASTAPI_DOCUMENTATION: bool
    ADMIN_EMAIL: str
    MIN_PASSWORD_LENGTH: int
    OTP_LOCAL_ENABLED: bool
    OTP_EXTERNAL_ENABLED: bool
    CORS_ENABLED: bool
    CORS_ORIGINS: list[str]
    CORS_METHODS: list[str]
    CORS_HEADERS: list[str]
    CORS_CREDENTIALS: bool
    CORS_MAX_AGE: int
    DB_ENGINE: Literal["postgres", "sqlite"]
    SQLITE_DB_PATH: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MITRE_JSON_URL: str
    CUSTOM_DATA_URL: str | None
    ATOMIC_RED_TEAM_URL: str
    WELCOME_MESSAGE: str | None
    EXTERNAL_AUTH_CONFIGS: list[ExternalAuthConfig] | None
