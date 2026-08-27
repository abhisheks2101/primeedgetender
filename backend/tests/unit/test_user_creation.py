"""User creation tests."""

import uuid

import pytest
from pydantic import ValidationError

from app.core.enums import UserRole
from app.core.security import verify_password
from app.schemas.auth import UserCreate


@pytest.mark.integration
def test_create_valid_user(user_service, sample_user_payload):
    user = user_service.create_user(sample_user_payload, role=UserRole.USER)

    assert user.email == sample_user_payload.email.lower()
    assert user.full_name == sample_user_payload.full_name
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert verify_password(sample_user_payload.password, user.password_hash)


@pytest.mark.integration
def test_create_duplicate_email_fails(user_service, sample_user_payload):
    user_service.create_user(sample_user_payload)

    with pytest.raises(ValueError, match="already exists"):
        user_service.create_user(sample_user_payload)


def test_invalid_email_rejected():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="Password123", full_name="Test")


@pytest.mark.integration
def test_invalid_password_requirements(user_service):
    payload = UserCreate(
        email=f"weak-{uuid.uuid4().hex[:8]}@example.com",
        password="12345678",
        full_name="Weak Password User",
    )

    with pytest.raises(ValueError, match="letter"):
        user_service.create_user(payload)
