"""Mock collector for testing the collection framework without external requests."""

from enum import Enum

from app.collectors.base import (
    CollectionContext,
    DiscoveryResult,
    NormalizedTenderDraft,
    RawDocumentRef,
    RawTenderData,
    TenderCollector,
    ValidationResult,
)
from app.collectors.errors import (
    NetworkCollectionError,
    ParsingCollectionError,
    SourceUnavailableError,
)


class MockCollectionScenario(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    PARSING_FAILURE = "PARSING_FAILURE"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class MockTenderCollector(TenderCollector):
    code = "MOCK"

    def __init__(self, scenario: MockCollectionScenario = MockCollectionScenario.SUCCESS) -> None:
        self.scenario = scenario
        self._attempts = 0

    async def discover(self, context: CollectionContext) -> DiscoveryResult:
        self._attempts += 1

        if self.scenario == MockCollectionScenario.TEMPORARY_FAILURE and self._attempts < 3:
            raise NetworkCollectionError("Simulated temporary network failure.")
        if self.scenario == MockCollectionScenario.SOURCE_UNAVAILABLE:
            raise SourceUnavailableError("Simulated source unavailable.")
        if self.scenario == MockCollectionScenario.PARSING_FAILURE:
            raise ParsingCollectionError("Simulated parsing failure during discovery.")
        if self.scenario == MockCollectionScenario.EMPTY:
            return DiscoveryResult(items=[])

        return DiscoveryResult(
            items=[
                RawTenderData(
                    source_tender_id=f"{context.source.code}-001",
                    payload={
                        "title": "Mock Tender One",
                        "reference": f"{context.source.code}-001",
                    },
                ),
                RawTenderData(
                    source_tender_id=f"{context.source.code}-002",
                    payload={
                        "title": "Mock Tender Two",
                        "reference": f"{context.source.code}-002",
                    },
                ),
            ]
        )

    async def fetch_details(self, source_tender_id: str, context: CollectionContext) -> RawTenderData:
        detail_url = f"https://example.test/tenders/{source_tender_id}"
        return RawTenderData(
            source_tender_id=source_tender_id,
            payload={
                "summary": {
                    "title": f"Mock detail for {source_tender_id}",
                    "reference_number": source_tender_id,
                    "detail_url": detail_url,
                },
                "detail": {
                    "title": f"Mock detail for {source_tender_id}",
                    "reference_number": source_tender_id,
                    "detail_url": detail_url,
                    "organization": context.source.authority,
                    "state": context.source.state,
                },
            },
        )

    async def fetch_documents(
        self,
        source_tender_id: str,
        context: CollectionContext,
    ) -> list[RawDocumentRef]:
        return [
            RawDocumentRef(
                document_id=f"{source_tender_id}-doc-1",
                title="Mock notice document",
                url=f"https://example.test/{source_tender_id}/notice.pdf",
            )
        ]

    def normalize(self, raw: RawTenderData, context: CollectionContext) -> NormalizedTenderDraft:
        summary = raw.payload.get("summary", raw.payload)
        detail = raw.payload.get("detail", raw.payload)
        return NormalizedTenderDraft(
            source_code=context.source.code,
            source_tender_id=raw.source_tender_id,
            reference_number=detail.get("reference_number") or summary.get("reference_number"),
            title=str(detail.get("title") or summary.get("title") or raw.source_tender_id),
            organization=detail.get("organization") or context.source.authority,
            state=detail.get("state") or context.source.state,
            source_url=detail.get("detail_url") or summary.get("detail_url"),
            raw_payload=raw.payload,
        )

    def validate(self, draft: NormalizedTenderDraft, context: CollectionContext) -> ValidationResult:
        errors: list[str] = []
        if not draft.source_tender_id:
            errors.append("source_tender_id is required")
        if not draft.title:
            errors.append("title is required")
        if not draft.source_url:
            errors.append("source_url is required")
        return ValidationResult(is_valid=not errors, errors=errors)
