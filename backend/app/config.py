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

    upload_storage_path: str = Field(default="storage/uploads", alias="UPLOAD_STORAGE_PATH")
    max_upload_size_bytes: int = Field(default=10_485_760, alias="MAX_UPLOAD_SIZE_BYTES")
    allowed_upload_mime_types: str = Field(
        default=(
            "application/pdf,image/jpeg,image/png,image/webp,text/plain,"
            "application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
            "application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        alias="ALLOWED_UPLOAD_MIME_TYPES",
    )
    document_expiring_soon_days: int = Field(default=30, alias="DOCUMENT_EXPIRING_SOON_DAYS")

    document_storage_path: str = Field(default="storage/tenders", alias="DOCUMENT_STORAGE_PATH")
    max_document_size_mb: int = Field(default=50, alias="MAX_DOCUMENT_SIZE_MB")
    download_timeout_seconds: int = Field(default=30, alias="DOWNLOAD_TIMEOUT_SECONDS")
    download_retries: int = Field(default=3, alias="DOWNLOAD_RETRIES")
    download_delay_seconds: float = Field(default=1.0, alias="DOWNLOAD_DELAY_SECONDS")
    max_documents_per_job: int = Field(default=50, alias="MAX_DOCUMENTS_PER_JOB")
    ocr_enabled: bool = Field(default=False, alias="OCR_ENABLED")
    ocr_languages: str = Field(default="eng", alias="OCR_LANGUAGES")
    ocr_min_text_threshold: int = Field(default=50, alias="OCR_MIN_TEXT_THRESHOLD")
    document_allowed_domains: str = Field(
        default="etender.up.nic.in,mptenders.gov.in,example.test",
        alias="DOCUMENT_ALLOWED_DOMAINS",
    )

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

    @property
    def allowed_mime_types(self) -> list[str]:
        return [item.strip() for item in self.allowed_upload_mime_types.split(",") if item.strip()]

    @property
    def max_document_size_bytes(self) -> int:
        return self.max_document_size_mb * 1024 * 1024

    @property
    def allowed_document_domains(self) -> list[str]:
        return [item.strip().lower() for item in self.document_allowed_domains.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
