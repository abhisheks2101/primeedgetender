"""Integration tests for tender source management."""

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.helpers import login


def _source_payload(**overrides):
    suffix = uuid.uuid4().hex[:8].upper()
    payload = {
        "name": f"Test Source {suffix}",
        "code": f"TEST_{suffix}",
        "state": "Demo State",
        "authority": "Demo Authority",
        "portal_url": "https://example.test/portal",
        "source_type": "GOVERNMENT_PORTAL",
        "collection_method": "HTML",
        "priority": 50,
        "description": "Integration test source",
        "configuration": {
            "source_url": "https://example.test/source",
            "request_timeout_seconds": 30,
            "retry_count": 2,
            "request_delay_seconds": 1.0,
            "max_requests_per_collection": 10,
        },
        "is_active": True,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def admin_client(api_client: TestClient, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    return api_client


@pytest.fixture
def user_client(api_client: TestClient, created_user):
    login(api_client, created_user.email, "Password123")
    return api_client


class TestTenderSourceManagement:
    def test_create_and_get_source(self, admin_client: TestClient):
        payload = _source_payload()
        create_response = admin_client.post("/api/tender-sources", json=payload)
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["code"] == payload["code"]

        get_response = admin_client.get(f"/api/tender-sources/{created['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == payload["name"]

    def test_list_sources(self, admin_client: TestClient):
        admin_client.post("/api/tender-sources", json=_source_payload())
        response = admin_client.get("/api/tender-sources")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_update_source(self, admin_client: TestClient):
        created = admin_client.post("/api/tender-sources", json=_source_payload()).json()
        response = admin_client.patch(
            f"/api/tender-sources/{created['id']}",
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

    def test_activate_deactivate_source(self, admin_client: TestClient):
        created = admin_client.post("/api/tender-sources", json=_source_payload()).json()
        response = admin_client.patch(
            f"/api/tender-sources/{created['id']}/status",
            json={"is_active": False, "health_status": "DEGRADED"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["is_active"] is False
        assert body["health_status"] == "DEGRADED"

    def test_duplicate_source_code_rejected(self, admin_client: TestClient):
        payload = _source_payload(code="DUPLICATE_CODE")
        first = admin_client.post("/api/tender-sources", json=payload)
        assert first.status_code == 201
        second = admin_client.post("/api/tender-sources", json=payload)
        assert second.status_code == 409

    def test_invalid_url_rejected(self, admin_client: TestClient):
        payload = _source_payload(portal_url="not-a-url")
        response = admin_client.post("/api/tender-sources", json=payload)
        assert response.status_code == 422

    def test_invalid_configuration_rejected(self, admin_client: TestClient):
        payload = _source_payload(configuration={"request_timeout_seconds": -1})
        response = admin_client.post("/api/tender-sources", json=payload)
        assert response.status_code == 422


class TestTenderSourceAuthorization:
    def test_unauthenticated_rejected(self, api_client: TestClient):
        response = api_client.get("/api/tender-sources")
        assert response.status_code == 401

    def test_user_can_read_sources(self, user_client: TestClient, admin_client: TestClient):
        admin_client.post("/api/tender-sources", json=_source_payload())
        response = user_client.get("/api/tender-sources")
        assert response.status_code == 200

    def test_user_cannot_create_source(self, user_client: TestClient):
        response = user_client.post("/api/tender-sources", json=_source_payload())
        assert response.status_code == 403

    def test_user_cannot_update_source(
        self,
        test_settings,
        created_admin,
        created_user,
    ):
        from app.main import create_app

        with TestClient(create_app(test_settings)) as admin_client, TestClient(create_app(test_settings)) as user_client:
            login(admin_client, created_admin.email, "AdminPass123")
            login(user_client, created_user.email, "Password123")
            created = admin_client.post("/api/tender-sources", json=_source_payload()).json()
            response = user_client.patch(
                f"/api/tender-sources/{created['id']}",
                json={"description": "Blocked"},
            )
            assert response.status_code == 403
