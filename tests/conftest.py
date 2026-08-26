"""Shared pytest fixtures for integration tests."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.config import Settings
from app.core.database import check_database_connection
from app.main import create_app


def _build_test_settings() -> Settings:
    return Settings(
        app_env="test",
        app_debug=True,
        postgres_user=os.getenv("POSTGRES_USER", "tender_user"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "change_me_in_production"),
        postgres_db=os.getenv("POSTGRES_DB", "tender_intelligence"),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
    )


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return _build_test_settings()


@pytest.fixture(scope="session")
def db_engine(test_settings: Settings):
    engine = create_engine(str(test_settings.database_url), pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def api_client(test_settings: Settings):
    app = create_app(test_settings)
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def database_is_available(db_engine) -> bool:
    connected, _, _ = check_database_connection(db_engine)
    return connected
