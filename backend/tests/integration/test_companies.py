"""Company profile integration tests."""

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.enums import FinancialRecordType
from tests.helpers import login


@pytest.fixture
def admin_client(api_client: TestClient, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    return api_client


@pytest.fixture
def user_client(api_client: TestClient, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    return api_client


def _company_payload(name: str) -> dict:
    suffix = uuid.uuid4().hex[:6]
    return {
        "legal_name": f"{name} Legal {suffix}",
        "display_name": f"{name} {suffix}",
        "legal_entity_type": "Private Limited",
        "city": "Demo City",
        "state": "Demo State",
        "email": f"{suffix}@example.com",
        "description": "Test company",
    }


@pytest.mark.integration
def test_create_and_get_company(admin_client: TestClient):
    response = admin_client.post("/api/companies", json=_company_payload("Alpha"))
    assert response.status_code == 201
    company = response.json()
    get_response = admin_client.get(f"/api/companies/{company['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["display_name"] == company["display_name"]


@pytest.mark.integration
def test_multiple_companies_remain_isolated(admin_client: TestClient):
    company_a = admin_client.post("/api/companies", json=_company_payload("CompanyA")).json()
    company_b = admin_client.post("/api/companies", json=_company_payload("CompanyB")).json()

    admin_client.post(
        f"/api/companies/{company_a['id']}/experiences",
        json={"project_name": "A Project", "work_category": "ROAD_CONSTRUCTION", "project_status": "COMPLETED"},
    )
    admin_client.post(
        f"/api/companies/{company_b['id']}/experiences",
        json={"project_name": "B Project", "work_category": "DRAINAGE", "project_status": "COMPLETED"},
    )

    a_experiences = admin_client.get(f"/api/companies/{company_a['id']}/experiences").json()
    b_experiences = admin_client.get(f"/api/companies/{company_b['id']}/experiences").json()
    assert len(a_experiences) == 1
    assert len(b_experiences) == 1
    assert a_experiences[0]["project_name"] == "A Project"
    assert b_experiences[0]["project_name"] == "B Project"


@pytest.mark.integration
def test_user_can_read_but_not_create_company(test_settings, created_admin, created_user, sample_user_payload):
    from app.main import create_app

    with TestClient(create_app(test_settings)) as admin_client, TestClient(create_app(test_settings)) as user_client:
        login(admin_client, created_admin.email, "AdminPass123")
        login(user_client, sample_user_payload.email, sample_user_payload.password)
        company = admin_client.post("/api/companies", json=_company_payload("ReadOnly")).json()
        assert user_client.get(f"/api/companies/{company['id']}").status_code == 200
        assert user_client.post("/api/companies", json=_company_payload("Denied")).status_code == 403


@pytest.mark.integration
def test_financial_records_support_multiple_years(admin_client: TestClient):
    company = admin_client.post("/api/companies", json=_company_payload("Finance")).json()
    for year, amount in [("2023-24", "1000000"), ("2024-25", "1500000")]:
        response = admin_client.post(
            f"/api/companies/{company['id']}/financial-records",
            json={"record_type": FinancialRecordType.TURNOVER.value, "amount": amount, "financial_year": year},
        )
        assert response.status_code == 201
    records = admin_client.get(f"/api/companies/{company['id']}/financial-records").json()
    assert len(records) == 2


@pytest.mark.integration
def test_document_upload_validation(admin_client: TestClient):
    company = admin_client.post("/api/companies", json=_company_payload("Docs")).json()
    doc_types = admin_client.get("/api/companies/lookup/document-types").json()
    doc_type_id = doc_types[0]["id"]

    files = {"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
    data = {"document_type_id": doc_type_id, "description": "Test upload"}
    ok = admin_client.post(f"/api/companies/{company['id']}/documents", files=files, data=data)
    assert ok.status_code == 201

    bad_files = {"file": ("bad.exe", io.BytesIO(b"MZ"), "application/octet-stream")}
    bad = admin_client.post(f"/api/companies/{company['id']}/documents", files=bad_files, data=data)
    assert bad.status_code == 400


@pytest.mark.integration
def test_archive_company(admin_client: TestClient):
    company = admin_client.post("/api/companies", json=_company_payload("Archive")).json()
    response = admin_client.delete(f"/api/companies/{company['id']}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False
