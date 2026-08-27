"""Authentication and authorization tests."""

import pytest

from tests.helpers import login


@pytest.mark.integration
def test_unauthenticated_request_rejected(api_client):
    response = api_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
def test_authenticated_user_can_access_session_check(api_client, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    response = api_client.get("/api/auth/session-check")

    assert response.status_code == 200
    assert response.json()["email"] == sample_user_payload.email.lower()


@pytest.mark.integration
def test_authenticated_admin_can_access_session_check(api_client, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    response = api_client.get("/api/auth/session-check")

    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


@pytest.mark.integration
def test_user_cannot_access_admin_endpoint(api_client, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    response = api_client.get("/api/admin/status")

    assert response.status_code == 403


@pytest.mark.integration
def test_admin_can_access_admin_endpoint(api_client, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    response = api_client.get("/api/admin/status")

    assert response.status_code == 200
    assert "Admin access granted" in response.json()["message"]
