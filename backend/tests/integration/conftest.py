"""Integration test fixtures."""

import pytest
from sqlalchemy import delete

from app.models.user import LoginAttempt, User, UserSession


@pytest.fixture(autouse=True)
def clean_auth_tables(db):
    db.execute(delete(LoginAttempt))
    db.execute(delete(UserSession))
    db.execute(delete(User))
    db.commit()
    yield
