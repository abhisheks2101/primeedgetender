"""Generic tender collector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.enums import TenderStatus
from app.models.tender_source import TenderSource
from app.schemas.tender_source import SourceConfiguration


@dataclass(slots=True)
class CollectionContext:
    source: TenderSource
    job_id: UUID
    configuration: SourceConfiguration
    current_summary: dict[str, Any] | None = None
    current_detail_payload: dict[str, Any] | None = None


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
    reference_number: str | None = None
    title: str | None = None
    work_description: str | None = None
    organization: str | None = None
    department: str | None = None
    tender_type: str | None = None
    tender_category: str | None = None
    location: str | None = None
    district: str | None = None
    state: str | None = None
    estimated_value: Decimal | None = None
    emd_amount: Decimal | None = None
    tender_fee: Decimal | None = None
    publication_date: datetime | None = None
    document_sale_start: datetime | None = None
    document_sale_end: datetime | None = None
    submission_start: datetime | None = None
    submission_end: datetime | None = None
    opening_date: datetime | None = None
    status: TenderStatus = TenderStatus.UNKNOWN
    source_status: str | None = None
    source_url: str | None = None
    source_last_updated: datetime | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)
    documents: list[RawDocumentRef] = field(default_factory=list)


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
