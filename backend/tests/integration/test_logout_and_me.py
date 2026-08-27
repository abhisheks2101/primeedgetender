"""Logout and current-user endpoint tests."""

import pytest

from tests.helpers import login


@pytest.mark.integration
def test_logout_invalidates_session(api_client, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    assert api_client.get("/api/auth/me").status_code == 200

    logout_response = api_client.post("/api/auth/logout")
    assert logout_response.status_code == 200

    me_response = api_client.get("/api/auth/me")
    assert me_response.status_code == 401


@pytest.mark.integration
def test_current_user_returns_expected_fields(api_client, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    response = api_client.get("/api/auth/me")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {
        "id",
        "email",
        "full_name",
        "role",
        "is_active",
        "created_at",
        "last_login_at",
    }
    assert payload["email"] == sample_user_payload.email.lower()
    assert payload["full_name"] == sample_user_payload.full_name


@pytest.mark.integration
def test_current_user_unauthenticated(api_client):
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401
