"""Shared helpers for backend tests."""

import uuid

from fastapi.testclient import TestClient

from app.schemas.auth import UserCreate
from app.services.user_service import UserService


def login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def create_inactive_user(user_service: UserService):
    suffix = uuid.uuid4().hex[:8]
    user = user_service.create_user(
        UserCreate(
            email=f"inactive-{suffix}@example.com",
            password="Password123",
            full_name="Inactive User",
        )
    )
    user.is_active = False
    user_service.db.commit()
    user_service.db.refresh(user)
    return user
