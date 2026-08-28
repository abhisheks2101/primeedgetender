"""Tests for collector framework, jobs, retry, and logging."""

import pytest

from app.collectors.base import TenderCollector
from app.collectors.errors import NetworkCollectionError
from app.collectors.mock_collector import MockCollectionScenario, MockTenderCollector
from app.collectors.mp.mp_collector import MPTenderCollector
from app.collectors.registry import CollectorRegistry
from app.collectors.up.up_collector import UPTenderCollector
from app.collectors.retry import RetryPolicy, retry_async
from app.core.enums import CollectionJobStatus
from app.schemas.tender_source import TenderSourceCreate, SourceConfiguration
from app.services.collection_runner import CollectionRunner, sanitize_context
from app.services.tender_source_service import TenderSourceService
from app.core.enums import CollectionMethod, TenderSourceType


@pytest.mark.asyncio
async def test_collector_interface_methods_exist():
    collector = MockTenderCollector()
    assert isinstance(collector, TenderCollector)
    for method_name in ("discover", "fetch_details", "fetch_documents", "normalize", "validate"):
        assert callable(getattr(collector, method_name))


@pytest.mark.asyncio
async def test_mock_collector_success(db, created_admin):
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name="Mock Source",
            code="TEST_MOCK",
            source_type=TenderSourceType.OTHER,
            collection_method=CollectionMethod.OTHER,
            configuration=SourceConfiguration(retry_count=0),
        )
    )
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(source.id, MockTenderCollector(), scenario=MockCollectionScenario.SUCCESS)
    assert job.status == CollectionJobStatus.COMPLETED
    assert job.records_discovered == 2
    assert job.records_created == 2


@pytest.mark.asyncio
async def test_mock_collector_empty(db):
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name="Mock Empty",
            code="TEST_EMPTY",
            source_type=TenderSourceType.OTHER,
            collection_method=CollectionMethod.OTHER,
        )
    )
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(source.id, MockTenderCollector(), scenario=MockCollectionScenario.EMPTY)
    assert job.status == CollectionJobStatus.COMPLETED
    assert job.records_discovered == 0


@pytest.mark.asyncio
async def test_mock_collector_temporary_failure_retries(db):
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name="Mock Retry",
            code="TEST_RETRY",
            source_type=TenderSourceType.OTHER,
            collection_method=CollectionMethod.OTHER,
            configuration=SourceConfiguration(retry_count=3, request_delay_seconds=0),
        )
    )
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(
        source.id,
        MockTenderCollector(),
        scenario=MockCollectionScenario.TEMPORARY_FAILURE,
    )
    assert job.status == CollectionJobStatus.COMPLETED


@pytest.mark.asyncio
async def test_mock_collector_parsing_failure(db):
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name="Mock Parse Fail",
            code="TEST_PARSE",
            source_type=TenderSourceType.OTHER,
            collection_method=CollectionMethod.OTHER,
            configuration=SourceConfiguration(retry_count=0),
        )
    )
    runner = CollectionRunner(db)
    job = await runner.run_with_collector(
        source.id,
        MockTenderCollector(),
        scenario=MockCollectionScenario.PARSING_FAILURE,
    )
    assert job.status == CollectionJobStatus.FAILED


@pytest.mark.asyncio
async def test_retry_limit_records_final_failure():
    attempts = {"count": 0}

    async def failing_operation():
        attempts["count"] += 1
        raise NetworkCollectionError("temporary")

    with pytest.raises(NetworkCollectionError):
        await retry_async(failing_operation, policy=RetryPolicy(max_attempts=3, delay_seconds=0))

    assert attempts["count"] == 3


def test_sensitive_context_redacted():
    sanitized = sanitize_context({"token": "secret-value", "page": 1})
    assert sanitized["token"] == "[REDACTED]"
    assert sanitized["page"] == 1


def test_registry_contains_collectors():
    assert CollectorRegistry.get("UP_TENDER") is UPTenderCollector
    assert CollectorRegistry.get("MP_TENDER") is MPTenderCollector


def test_mp_collector_is_registered():
    collector = MPTenderCollector()
    assert collector.code == "MP_TENDER"
    assert CollectorRegistry.get("MP_TENDER") is MPTenderCollector
