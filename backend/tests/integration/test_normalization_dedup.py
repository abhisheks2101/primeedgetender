"""Integration tests for normalization, deduplication, and admin APIs."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.enums import DuplicateReviewStatus
from app.services.tender_service import TenderService
from tests.helpers import login
from tests.tender_factory import create_source, future_date, upsert_test_tender


@pytest.fixture
def admin_client(api_client: TestClient, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    return api_client


@pytest.fixture
def user_client(api_client: TestClient, created_user, sample_user_payload):
    login(api_client, sample_user_payload.email, sample_user_payload.password)
    return api_client


@pytest.fixture
def up_mp_sources(db):
    up_id = create_source(db, code="UP_TENDER", state="Uttar Pradesh")
    mp_id = create_source(db, code="MP_TENDER", state="Madhya Pradesh")
    return {"up_id": up_id, "mp_id": mp_id}


def _seed_up_mp_dataset(db, up_mp_sources):
    up_id = up_mp_sources["up_id"]
    mp_id = up_mp_sources["mp_id"]
    end = future_date()

    for index in range(12):
        upsert_test_tender(
            db,
            source_id=up_id,
            source_code="UP_TENDER",
            source_tender_id=f"UP-{index:03d}",
            title=f"UP Road Work {index}",
            reference_number=f"UP-REF-{index}",
            organization="UP PWD",
            location="Lucknow",
            state="Uttar Pradesh",
            estimated_value=Decimal("10000000") + index,
            submission_end=end,
        )

    for index in range(12):
        upsert_test_tender(
            db,
            source_id=mp_id,
            source_code="MP_TENDER",
            source_tender_id=f"MP-{index:03d}",
            title=f"MP Road Work {index}",
            reference_number=f"MP-REF-{index}",
            organization="MP PWD",
            location="Bhopal",
            state="Madhya Pradesh",
            estimated_value=Decimal("10000000") + index,
            submission_end=end,
        )


class TestNormalizationUpsert:
    def test_exact_duplicate_updates_existing_record(self, db, up_mp_sources):
        up_id = up_mp_sources["up_id"]
        tender, action = upsert_test_tender(
            db,
            source_id=up_id,
            source_code="UP_TENDER",
            source_tender_id="UP-EXACT-1",
            title="Exact Duplicate Tender",
            reference_number="UP-EXACT-REF",
            estimated_value=Decimal("5000000"),
        )
        assert action == "created"

        updated, second_action = upsert_test_tender(
            db,
            source_id=up_id,
            source_code="UP_TENDER",
            source_tender_id="UP-EXACT-1",
            title="Exact Duplicate Tender Updated",
            reference_number="UP-EXACT-REF",
            estimated_value=Decimal("6000000"),
        )
        assert second_action == "updated"
        assert updated.id == tender.id
        assert updated.estimated_value == Decimal("6000000")

    def test_cross_source_identical_records_remain_separate(self, db, up_mp_sources):
        shared_title = "Shared Road Construction"
        shared_value = Decimal("20000000")
        up_tender, _ = upsert_test_tender(
            db,
            source_id=up_mp_sources["up_id"],
            source_code="UP_TENDER",
            source_tender_id="123",
            title=shared_title,
            reference_number="123",
            location="Lucknow",
            state="Uttar Pradesh",
            estimated_value=shared_value,
        )
        mp_tender, _ = upsert_test_tender(
            db,
            source_id=up_mp_sources["mp_id"],
            source_code="MP_TENDER",
            source_tender_id="123",
            title=shared_title,
            reference_number="123",
            location="Lucknow",
            state="Madhya Pradesh",
            estimated_value=shared_value,
        )
        assert up_tender.id != mp_tender.id

    def test_reprocess_normalization_updates_version_fields(self, db, up_mp_sources):
        tender, _ = upsert_test_tender(
            db,
            source_id=up_mp_sources["up_id"],
            source_code="UP_TENDER",
            source_tender_id="UP-REPROCESS",
            title="Reprocess Target",
            reference_number="UP-REPROCESS",
        )
        service = TenderService(db)
        reprocessed = service.reprocess_tender(tender, source_code="UP_TENDER")
        db.commit()
        assert reprocessed.normalization_version == 1
        assert reprocessed.normalization_status.value in {"NORMALIZED", "NEEDS_REVIEW"}


class TestTenderApis:
    def test_list_and_get_tenders(self, admin_client, db, up_mp_sources):
        _seed_up_mp_dataset(db, up_mp_sources)
        response = admin_client.get("/api/tenders")
        assert response.status_code == 200
        body = response.json()
        assert len(body) >= 20

        tender_id = body[0]["id"]
        detail = admin_client.get(f"/api/tenders/{tender_id}")
        assert detail.status_code == 200
        assert detail.json()["normalization_version"] == 1

    def test_unauthenticated_tender_access_rejected(self, api_client):
        assert api_client.get("/api/tenders").status_code == 401


class TestDuplicateReviewApis:
    def test_admin_can_review_duplicate_candidate(self, admin_client, db, up_mp_sources):
        up_id = up_mp_sources["up_id"]
        upsert_test_tender(
            db,
            source_id=up_id,
            source_code="UP_TENDER",
            source_tender_id="UP-DUP-A",
            title="Bridge Construction Project Alpha",
            reference_number="BRIDGE-A",
            organization="PWD Division 1",
            estimated_value=Decimal("50000000"),
            submission_end=future_date(),
        )
        upsert_test_tender(
            db,
            source_id=up_id,
            source_code="UP_TENDER",
            source_tender_id="UP-DUP-B",
            title="Bridge Construction Project Alpha Phase 2",
            reference_number="BRIDGE-B",
            organization="PWD Division 1",
            estimated_value=Decimal("50000000"),
            submission_end=future_date(),
        )

        candidates = admin_client.get("/api/tender-duplicates")
        assert candidates.status_code == 200
        data = candidates.json()
        assert len(data) >= 1
        candidate_id = data[0]["id"]

        reviewed = admin_client.patch(
            f"/api/tender-duplicates/{candidate_id}",
            json={"review_status": "NOT_DUPLICATE"},
        )
        assert reviewed.status_code == 200
        assert reviewed.json()["review_status"] == "NOT_DUPLICATE"

    def test_user_cannot_access_duplicate_admin_api(self, user_client):
        assert user_client.get("/api/tender-duplicates").status_code == 403

    def test_uncertain_match_not_auto_merged(self, db, up_mp_sources):
        shared_title = "Identical Cross Source Tender"
        up_tender, _ = upsert_test_tender(
            db,
            source_id=up_mp_sources["up_id"],
            source_code="UP_TENDER",
            source_tender_id="CROSS-1",
            title=shared_title,
            reference_number="CROSS-REF",
            estimated_value=Decimal("1000000"),
        )
        mp_tender, _ = upsert_test_tender(
            db,
            source_id=up_mp_sources["mp_id"],
            source_code="MP_TENDER",
            source_tender_id="CROSS-2",
            title=shared_title,
            reference_number="CROSS-REF",
            estimated_value=Decimal("1000000"),
        )
        service = TenderService(db)
        assert service.get_by_id(up_tender.id) is not None
        assert service.get_by_id(mp_tender.id) is not None
        assert up_tender.id != mp_tender.id

        from app.services.deduplication_service import DeduplicationService

        dedup = DeduplicationService(db)
        candidates = dedup.list_candidates(review_status=DuplicateReviewStatus.PENDING)
        cross_source = [
            candidate
            for candidate in candidates
            if {candidate.tender_id, candidate.candidate_tender_id} == {up_tender.id, mp_tender.id}
        ]
        if cross_source:
            assert cross_source[0].review_status == DuplicateReviewStatus.PENDING
