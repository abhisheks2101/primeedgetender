"""Generic tender collector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.models.tender_source import TenderSource
from app.schemas.tender_source import SourceConfiguration


@dataclass(slots=True)
class CollectionContext:
    source: TenderSource
    job_id: UUID
    configuration: SourceConfiguration


@dataclass(slots=True)
class RawTenderData:
    source_tender_id: str
    payload: dict[str, Any]


@dataclass(slots=True)
class RawDocumentRef:
    document_id: str
    url: str | None = None
    title: str | None = None


@dataclass(slots=True)
class DiscoveryResult:
    items: list[RawTenderData] = field(default_factory=list)


@dataclass(slots=True)
class NormalizedTenderDraft:
    source_code: str
    source_tender_id: str
    title: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)


class TenderCollector(ABC):
    """Base interface implemented by all source-specific collectors."""

    code: str

    @abstractmethod
    async def discover(self, context: CollectionContext) -> DiscoveryResult:
        """Discover tender references from the source."""

    @abstractmethod
    async def fetch_details(self, source_tender_id: str, context: CollectionContext) -> RawTenderData:
        """Fetch detailed tender information for a discovered reference."""

    @abstractmethod
    async def fetch_documents(
        self,
        source_tender_id: str,
        context: CollectionContext,
    ) -> list[RawDocumentRef]:
        """Fetch document references associated with a tender."""

    @abstractmethod
    def normalize(self, raw: RawTenderData, context: CollectionContext) -> NormalizedTenderDraft:
        """Convert raw source data into a normalized draft structure."""

    @abstractmethod
    def validate(self, draft: NormalizedTenderDraft, context: CollectionContext) -> ValidationResult:
        """Validate normalized draft data."""
