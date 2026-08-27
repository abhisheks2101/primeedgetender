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
                        request_timeout_seconds=90,
                        retry_count=3,
                        request_delay_seconds=2.0,
                        max_requests_per_collection=50,
                        pagination={"page_size": 10},
                    ),
                )
            )
            created_any = True
        else:
            up_source = db.scalar(select(TenderSource).where(TenderSource.code == "UP_TENDER"))
            if up_source is not None:
                config = SourceConfiguration.model_validate(up_source.configuration or {})
                if (
                    config.request_timeout_seconds < 60
                    or config.retry_count < 3
                    or int((config.pagination or {}).get("page_size", 10)) < 10
                ):
                    up_source.configuration = SourceConfiguration(
                        source_url=config.source_url or UP_HOME_URL,
                        search_url=config.search_url or UP_SEARCH_URL,
                        detail_url_pattern=config.detail_url_pattern,
                        document_url_pattern=config.document_url_pattern,
                        request_timeout_seconds=90,
                        retry_count=3,
                        request_delay_seconds=max(config.request_delay_seconds, 2.0),
                        max_requests_per_collection=max(config.max_requests_per_collection, 50),
                        pagination={"page_size": 10},
                    ).model_dump(mode="json")
                    db.commit()
                    print("Updated UP_TENDER source with improved timeout/retry settings.")
                    created_any = True

        if not created_any:
            print("Tender sources already seeded. Skipping seed.")
            return 0

    print("Seeded tender sources (TEST_SOURCE_A, TEST_SOURCE_B, UP_TENDER as needed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed_demo_tender_sources())
