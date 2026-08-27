"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Tender Intelligence Platform", alias="APP_NAME")
    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")
    backend_cors_origins: str = Field(
        default="http://localhost:3000",
        alias="BACKEND_CORS_ORIGINS",
    )

    postgres_user: str = Field(default="tender_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="tender_intelligence", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: PostgresDsn | str = Field(default="", alias="DATABASE_URL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    auth_secret: str = Field(default="", alias="AUTH_SECRET")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")
    session_cookie_name: str = Field(default="tip_session", alias="SESSION_COOKIE_NAME")
    session_expire_hours: int = Field(default=24, alias="SESSION_EXPIRE_HOURS")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax", alias="COOKIE_SAMESITE")
    allow_public_registration: bool = Field(default=False, alias="ALLOW_PUBLIC_REGISTRATION")
    login_rate_limit_max_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_MAX_ATTEMPTS")
    login_rate_limit_window_minutes: int = Field(default=15, alias="LOGIN_RATE_LIMIT_WINDOW_MINUTES")

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, value: str | None, info) -> str:
        if value:
            return str(value)
        data = info.data
        user = data.get("postgres_user", "tender_user")
        password = data.get("postgres_password", "")
        host = data.get("postgres_host", "localhost")
        port = data.get("postgres_port", 5432)
        db = data.get("postgres_db", "tender_intelligence")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    @field_validator("cookie_secure", mode="before")
    @classmethod
    def default_cookie_secure(cls, value, info):
        if value is not None and str(value).strip() != "":
            return value
        data = info.data
        return data.get("app_env") == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
