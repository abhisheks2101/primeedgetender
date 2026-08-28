"""Integration tests for MP tender collector with mocked portal responses."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.collectors.mp.mp_collector import MPTenderCollector
from app.collectors.up.up_collector import UPTenderCollector
from app.core.enums import CollectionJobStatus, CollectionMethod, TenderSourceType, TenderStatus
from app.models.tender import Tender, TenderDocument
from app.models.tender_source import TenderRawRecord
from app.schemas.tender_source import SourceConfiguration, TenderSourceCreate
from app.services.collection_runner import CollectionRunner
from app.services.tender_source_service import TenderSourceService

FIXTURES = Path("/agent/backend/tests/fixtures/mp")


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class MockMPTransport(httpx.AsyncBaseTransport):
    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "FrontEndViewTender" in url or ("service=direct" in url and "sp=MP_CLOSED" in url):
            return httpx.Response(200, text=load_fixture("tender_detail_closed.html"))
        if "service=direct" in url and "MP_OPEN" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_open.html"))
        if "service=direct" in url and "MP_INVALID" in url:
            return httpx.Response(200, text=load_fixture("tender_detail_invalid_date.html"))
        if request.url.host == "malformed.test":
            return httpx.Response(200, text=load_fixture("malformed_listing.html"))
        if "service=direct" in url and "1178990" in url:
            return httpx.Response(500, text="server error")
        return httpx.Response(200, text=load_fixture("home_listing.html"))


def create_mp_source(db, **overrides):
    service = TenderSourceService(db)
    config = SourceConfiguration(
        source_url="https://mptenders.gov.in/nicgep/app?page=Home&service=page",
        search_url="https://mptenders.gov.in/nicgep/app?page=FrontEndLatestActiveTenders&service=page",
        request_timeout_seconds=5,
        retry_count=0,
        request_delay_seconds=0,
        max_requests_per_collection=10,
        pagination={"page_size": 3},
    )
    return service.create_source(
        TenderSourceCreate(
            name="Madhya Pradesh Tender Portal",
            code=overrides.pop("code", "MP_TENDER"),
            state="Madhya Pradesh",
            authority="Government of Madhya Pradesh",
            portal_url="https://mptenders.gov.in/nicgep/app",
            source_type=TenderSourceType.GOVERNMENT_PORTAL,
            collection_method=CollectionMethod.HTML,
            configuration=config,
            **overrides,
        )
    )


@pytest.mark.asyncio
async def test_mp_collector_integration_creates_tenders(db):
    source = create_mp_source(db)
    collector = MPTenderCollector(transport=MockMPTransport())
    job = await CollectionRunner(db).run_with_collector(source.id, collector)

    assert job.status == CollectionJobStatus.COMPLETED
    assert job.records_discovered == 3
    assert job.records_created == 3

    tender = db.scalar(select(Tender).where(Tender.source_tender_id == "2026_MP_100001_1"))
    assert tender is not None
    assert tender.title == "Road Construction Work in Bhopal"
    assert tender.status == TenderStatus.OPEN
    assert tender.state == "Madhya Pradesh"
    assert tender.estimated_value == Decimal("5000000")

    docs = db.scalars(select(TenderDocument).where(TenderDocument.tender_id == tender.id)).all()
    assert len(docs) == 2


@pytest.mark.asyncio
async def test_mp_collector_upsert_skips_duplicates(db):
    source = create_mp_source(db)
    runner = CollectionRunner(db)
    first = await runner.run_with_collector(source.id, MPTenderCollector(transport=MockMPTransport()))
    assert first.records_created == 3
    second = await runner.run_with_collector(source.id, MPTenderCollector(transport=MockMPTransport()))
    assert second.records_skipped == 3
    tenders = db.scalars(select(Tender).where(Tender.tender_source_id == source.id)).all()
    assert len(tenders) == 3


@pytest.mark.asyncio
async def test_mp_collector_malformed_listing_fails(db):
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name="MP Malformed",
            code="MP_TEST_MALFORMED",
            source_type=TenderSourceType.GOVERNMENT_PORTAL,
            collection_method=CollectionMethod.HTML,
            configuration=SourceConfiguration(
                source_url="https://malformed.test/home",
                request_timeout_seconds=5,
                retry_count=0,
                request_delay_seconds=0,
            ),
        )
    )
    job = await CollectionRunner(db).run_with_collector(source.id, MPTenderCollector(transport=MockMPTransport()))
    assert job.status == CollectionJobStatus.FAILED


@pytest.mark.asyncio
async def test_cross_source_isolation_same_source_tender_id(db):
    mp_source = create_mp_source(db)
    up_service = TenderSourceService(db)
    up_source = up_service.create_source(
        TenderSourceCreate(
            name="UP Cross Test",
            code="UP_CROSS_TEST",
            state="Uttar Pradesh",
            source_type=TenderSourceType.GOVERNMENT_PORTAL,
            collection_method=CollectionMethod.HTML,
            configuration=SourceConfiguration(request_timeout_seconds=5, retry_count=0, request_delay_seconds=0),
        )
    )

    shared_id = "12345"
    mp_tender = Tender(tender_source_id=mp_source.id, source_tender_id=shared_id, title="MP Shared Title", state="Madhya Pradesh")
    up_tender = Tender(tender_source_id=up_source.id, source_tender_id=shared_id, title="UP Shared Title", state="Uttar Pradesh")
    db.add_all([mp_tender, up_tender])
    db.commit()

    mp_row = db.scalar(select(Tender).where(Tender.tender_source_id == mp_source.id, Tender.source_tender_id == shared_id))
    up_row = db.scalar(select(Tender).where(Tender.tender_source_id == up_source.id, Tender.source_tender_id == shared_id))
    assert mp_row.id != up_row.id
    assert mp_row.title == "MP Shared Title"
    assert up_row.title == "UP Shared Title"
