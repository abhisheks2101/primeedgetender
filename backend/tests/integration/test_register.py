"""Registration endpoint tests."""

import pytest


@pytest.mark.integration
def test_register_creates_user_role_only(api_client, sample_user_payload):
    response = api_client.post(
        "/api/auth/register",
        json=sample_user_payload.model_dump(),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["role"] == "USER"
    assert payload["email"] == sample_user_payload.email.lower()


@pytest.mark.integration
def test_register_disabled_when_setting_off(test_settings, sample_user_payload):
    from fastapi.testclient import TestClient

    from app.main import create_app

    disabled_settings = test_settings.model_copy(update={"allow_public_registration": False})
    with TestClient(create_app(disabled_settings)) as client:
        response = client.post("/api/auth/register", json=sample_user_payload.model_dump())

    assert response.status_code == 403
