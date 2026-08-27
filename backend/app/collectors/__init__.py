"""Tender collector framework."""

from app.collectors.base import (
    CollectionContext,
    DiscoveryResult,
    NormalizedTenderDraft,
    RawDocumentRef,
    RawTenderData,
    TenderCollector,
    ValidationResult,
)
from app.collectors.mock_collector import MockTenderCollector, MockCollectionScenario
from app.collectors.registry import CollectorRegistry, get_collector_for_source
from app.collectors.retry import RetryPolicy, retry_async

__all__ = [
    "CollectionContext",
    "CollectorRegistry",
    "DiscoveryResult",
    "MockCollectionScenario",
    "MockTenderCollector",
    "NormalizedTenderDraft",
    "RawDocumentRef",
    "RawTenderData",
    "RetryPolicy",
    "TenderCollector",
    "ValidationResult",
    "get_collector_for_source",
    "retry_async",
]
