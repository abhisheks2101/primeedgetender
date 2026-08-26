"""Health API integration tests."""

import pytest


@pytest.mark.integration
def test_health_endpoint_returns_expected_shape(api_client, database_is_available):
    if not database_is_available:
        pytest.skip("PostgreSQL is not available for integration tests")

    response = api_client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["application"] == "Tender Intelligence Platform"
    assert payload["status"] in {"healthy", "degraded", "unhealthy"}
    assert payload["database"]["status"] == "connected"
    assert payload["database"]["latency_ms"] is not None
