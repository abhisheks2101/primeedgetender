"""Seed fictional and real tender source configurations."""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.config import Settings
from app.core.database import create_db_engine, create_session_factory
from app.core.enums import CollectionMethod, TenderSourceType
from app.models.tender_source import TenderSource
from app.schemas.tender_source import SourceConfiguration, TenderSourceCreate
from app.services.tender_source_service import TenderSourceService

UP_PORTAL_URL = "https://etender.up.nic.in/nicgep/app"
UP_HOME_URL = f"{UP_PORTAL_URL}?page=Home&service=page"
UP_SEARCH_URL = f"{UP_PORTAL_URL}?page=FrontEndLatestActiveTenders&service=page"


def seed_demo_tender_sources() -> int:
    settings = Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        service = TenderSourceService(db)
        created_any = False

        if db.scalar(select(TenderSource).where(TenderSource.code == "TEST_SOURCE_A")) is None:
            service.create_source(
                TenderSourceCreate(
                    name="Test Source A",
                    code="TEST_SOURCE_A",
                    state="Demo State A",
                    authority="Fictional Procurement Authority A",
                    portal_url="https://example.test/source-a",
                    source_type=TenderSourceType.GOVERNMENT_PORTAL,
                    collection_method=CollectionMethod.HTML,
                    description="Fictional test source for development.",
                    configuration=SourceConfiguration(
                        source_url="https://example.test/source-a",
                        search_url="https://example.test/source-a/search",
                        request_timeout_seconds=30,
                        retry_count=2,
                        request_delay_seconds=1.5,
                        max_requests_per_collection=50,
                    ),
                )
            )
            created_any = True

        if db.scalar(select(TenderSource).where(TenderSource.code == "TEST_SOURCE_B")) is None:
            service.create_source(
                TenderSourceCreate(
                    name="Test Source B",
                    code="TEST_SOURCE_B",
                    state="Demo State B",
                    authority="Fictional Procurement Authority B",
                    portal_url="https://example.test/source-b",
                    source_type=TenderSourceType.PUBLIC_DATA,
                    collection_method=CollectionMethod.HTTP,
                    description="Second fictional test source for development.",
                    configuration=SourceConfiguration(
                        source_url="https://example.test/source-b",
                        request_timeout_seconds=20,
                        retry_count=1,
                        request_delay_seconds=2.0,
                        max_requests_per_collection=25,
                    ),
                )
            )
            created_any = True

        if db.scalar(select(TenderSource).where(TenderSource.code == "UP_TENDER")) is None:
            service.create_source(
                TenderSourceCreate(
                    name="Uttar Pradesh Tender Portal",
                    code="UP_TENDER",
                    state="Uttar Pradesh",
                    authority="Government of Uttar Pradesh",
                    portal_url=UP_PORTAL_URL,
                    source_type=TenderSourceType.GOVERNMENT_PORTAL,
                    collection_method=CollectionMethod.HTML,
                    description="Official Uttar Pradesh NIC GeP tender portal (public home listing and detail pages).",
                    configuration=SourceConfiguration(
                        source_url=UP_HOME_URL,
                        search_url=UP_SEARCH_URL,
                        request_timeout_seconds=30,
                        retry_count=2,
                        request_delay_seconds=1.5,
                        max_requests_per_collection=50,
                        pagination={"page_size": 10},
                    ),
                )
            )
            created_any = True

        if not created_any:
            print("Tender sources already seeded. Skipping seed.")
            return 0

    print("Seeded tender sources (TEST_SOURCE_A, TEST_SOURCE_B, UP_TENDER as needed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed_demo_tender_sources())
