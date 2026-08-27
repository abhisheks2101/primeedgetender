"""Shared pytest fixtures."""

import os
import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.core.database import check_database_connection
from app.core.enums import UserRole
from app.core.security import hash_password
from app.main import create_app
from app.models.user import LoginAttempt, User, UserSession
from app.schemas.auth import UserCreate
from app.services.user_service import UserService


def _build_test_settings() -> Settings:
    return Settings(
        app_env="test",
        app_debug=True,
        auth_secret="test-auth-secret-key-for-module-2",
        frontend_url="http://testserver",
        backend_cors_origins="http://testserver",
        allow_public_registration=True,
        cookie_secure=False,
        cookie_samesite="lax",
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
def database_is_available(db_engine) -> bool:
    connected, _, _ = check_database_connection(db_engine)
    return connected


@pytest.fixture(scope="session")
def session_factory(db_engine):
    return sessionmaker(bind=db_engine, autocommit=False, autoflush=False)


@pytest.fixture
def db(session_factory, database_is_available) -> Generator[Session, None, None]:
    if not database_is_available:
        pytest.skip("PostgreSQL is not available for integration tests")

    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def api_client(test_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app(test_settings)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def user_service(db: Session) -> UserService:
    return UserService(db)


@pytest.fixture
def sample_user_payload() -> UserCreate:
    suffix = uuid.uuid4().hex[:8]
    return UserCreate(
        email=f"user-{suffix}@example.com",
        password="Password123",
        full_name="Test User",
    )


@pytest.fixture
def created_user(user_service: UserService, sample_user_payload: UserCreate) -> User:
    return user_service.create_user(sample_user_payload, role=UserRole.USER)


@pytest.fixture
def created_admin(user_service: UserService) -> User:
    suffix = uuid.uuid4().hex[:8]
    return user_service.create_user(
        UserCreate(
            email=f"admin-{suffix}@example.com",
            password="AdminPass123",
            full_name="Test Admin",
        ),
        role=UserRole.ADMIN,
    )
