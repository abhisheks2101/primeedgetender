"""Integration tests for UP tender collector with mocked portal responses."""

from __future__ import annotations

from pathlib import Path

import httpx
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.collectors.up.up_collector import UPTenderCollector
from app.core.enums import CollectionJobStatus, CollectionMethod, TenderSourceType, TenderStatus
from app.models.tender import Tender, TenderDocument
from app.models.tender_source import TenderRawRecord
from app.schemas.tender_source import SourceConfiguration, TenderSourceCreate
from app.services.collection_runner import CollectionRunner
from app.services.tender_source_service import TenderSourceService

FIXTURES = Path("/agent/backend/tests/fixtures/up")


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class MockUPTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "FrontEndViewTender" in url and "1178990" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_open.html"))
        if "FrontEndViewTender" in url and "1178991" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_closed.html"))
        if "FrontEndViewTender" in url and "1178992" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_invalid_date.html"))
        if "FrontEndViewTender" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_open.html"))
        if request.url.host == "timeout.test":
            raise httpx.TimeoutException("timeout")
        if request.url.host == "error.test":
            return httpx.Response(500, text="server error")
        if request.url.host == "malformed.test":
            return httpx.Response(200, text=load_fixture("malformed_listing.html"))
        return httpx.Response(200, text=load_fixture("home_listing.html"))


def create_up_source(db, *, code: str = "UP_TENDER", source_url: str | None = None):
    service = TenderSourceService(db)
    return service.create_source(
        TenderSourceCreate(
            name="Uttar Pradesh Tender Portal",
            code=code,
            state="Uttar Pradesh",
            authority="Government of Uttar Pradesh",
            portal_url="https://etender.up.nic.in/nicgep/app",
            source_type=TenderSourceType.GOVERNMENT_PORTAL,
            collection_method=CollectionMethod.HTML,
            configuration=SourceConfiguration(
                source_url=source_url or "https://etender.up.nic.in/nicgep/app?page=Home&service=page",
                search_url="https://etender.up.nic.in/nicgep/app?page=FrontEndLatestActiveTenders&service=page",
                request_timeout_seconds=5,
                retry_count=0,
                request_delay_seconds=0,
                max_requests_per_collection=10,
                pagination={"page_size": 3},
            ),
        )
    )


@pytest.mark.asyncio
async def test_up_collector_integration_creates_tenders(db):
    source = create_up_source(db)
    collector = UPTenderCollector(transport=MockUPTransport())
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(source.id, collector)

    assert job.status == CollectionJobStatus.COMPLETED
    assert job.records_discovered == 3
    assert job.records_created == 3
    assert job.records_failed == 0

    tenders = db.scalars(select(Tender).where(Tender.tender_source_id == source.id)).all()
    assert len(tenders) == 3

    open_tender = db.scalar(
        select(Tender).where(Tender.source_tender_id == "2026_UPCDF_1178990_1")
    )
    assert open_tender is not None
    assert open_tender.title == "Supply of Medical Equipment"
    assert open_tender.status == TenderStatus.OPEN
    assert open_tender.estimated_value == Decimal("12500000")
    assert open_tender.state == "Uttar Pradesh"

    documents = db.scalars(select(TenderDocument).where(TenderDocument.tender_id == open_tender.id)).all()
    assert len(documents) == 1
    assert documents[0].document_name == "Tendernotice_1.pdf"

    raw_records = db.scalars(select(TenderRawRecord).where(TenderRawRecord.job_id == job.id)).all()
    assert len(raw_records) == 3


@pytest.mark.asyncio
async def test_up_collector_upsert_updates_existing_tender(db):
    source = create_up_source(db)
    collector = UPTenderCollector(transport=MockUPTransport())
    runner = CollectionRunner(db)

    first_job = await runner.run_with_collector(source.id, collector)
    assert first_job.records_created == 3

    second_job = await runner.run_with_collector(source.id, UPTenderCollector(transport=MockUPTransport()))
    assert second_job.records_skipped == 3
    assert second_job.records_created == 0

    tenders = db.scalars(select(Tender).where(Tender.tender_source_id == source.id)).all()
    assert len(tenders) == 3


@pytest.mark.asyncio
async def test_up_collector_malformed_listing_fails_job(db):
    source = create_up_source(db, source_url="https://malformed.test/home")
    collector = UPTenderCollector(transport=MockUPTransport())
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(source.id, collector)
    assert job.status == CollectionJobStatus.FAILED


@pytest.mark.asyncio
async def test_up_collector_http_failure_marks_partial_or_failed(db, monkeypatch):
    source = create_up_source(db)

    class PartialFailureTransport(MockUPTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if "FrontEndViewTender" in str(request.url) and "1178992" in str(request.url):
                return httpx.Response(500, text="detail failure")
            return await super().handle_async_request(request)

    collector = UPTenderCollector(transport=PartialFailureTransport())
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(source.id, collector)
    assert job.status == CollectionJobStatus.PARTIAL
    assert job.records_failed == 1
    assert job.records_created == 2
