"""Unit tests for application configuration."""

from app.config import Settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("APP_NAME", "Test Tender Platform")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("DATABASE_URL", "")

    settings = Settings()

    assert settings.app_name == "Test Tender Platform"
    assert settings.app_env == "test"
    assert "test_user" in str(settings.database_url)


def test_cors_origins_are_parsed():
    settings = Settings(backend_cors_origins="http://localhost:3000, http://127.0.0.1:3000")
    assert settings.cors_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]
