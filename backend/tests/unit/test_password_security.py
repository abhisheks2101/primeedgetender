"""Password security tests."""

import uuid

import pytest

from app.core.security import hash_password, validate_password_strength, verify_password
from app.schemas.auth import UserCreate


def test_password_is_hashed():
    password = "Password123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2b$")


@pytest.mark.integration
def test_plaintext_password_is_never_stored(user_service):
    password = "Password123"
    user = user_service.create_user(
        UserCreate(
            email=f"hash-{uuid.uuid4().hex[:8]}@example.com",
            password=password,
            full_name="Hash Test",
        )
    )

    assert user.password_hash != password


@pytest.mark.integration
def test_correct_password_verifies(user_service):
    password = "Password123"
    user = user_service.create_user(
        UserCreate(
            email=f"verify-{uuid.uuid4().hex[:8]}@example.com",
            password=password,
            full_name="Verify Test",
        )
    )

    assert verify_password(password, user.password_hash)


@pytest.mark.integration
def test_incorrect_password_fails(user_service):
    user = user_service.create_user(
        UserCreate(
            email=f"fail-{uuid.uuid4().hex[:8]}@example.com",
            password="Password123",
            full_name="Fail Test",
        )
    )

    assert not verify_password("WrongPassword123", user.password_hash)


def test_password_validation_rules():
    with pytest.raises(ValueError):
        validate_password_strength("short1")

    with pytest.raises(ValueError):
        validate_password_strength("passwordonly")

    with pytest.raises(ValueError):
        validate_password_strength("12345678")

    validate_password_strength("ValidPass1")
