"""Login endpoint tests."""

import pytest

from tests.helpers import create_inactive_user, login


@pytest.mark.integration
def test_login_with_valid_credentials(api_client, created_user, sample_user_payload):
    response = login(api_client, sample_user_payload.email, sample_user_payload.password)

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == sample_user_payload.email.lower()
    assert "password" not in payload
    assert "password_hash" not in payload
    assert api_client.cookies.get("tip_session")


@pytest.mark.integration
def test_login_with_invalid_credentials(api_client, created_user, sample_user_payload):
    response = login(api_client, sample_user_payload.email, "WrongPassword123")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.integration
def test_login_inactive_user(api_client, user_service):
    user = create_inactive_user(user_service)
    response = login(api_client, user.email, "Password123")

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.integration
def test_login_nonexistent_user(api_client):
    response = login(api_client, "missing@example.com", "Password123")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
