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
        return RawTenderData(
            source_tender_id=source_tender_id,
            payload={
                "title": f"Mock detail for {source_tender_id}",
                "reference": source_tender_id,
                "authority": context.source.authority,
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
        return NormalizedTenderDraft(
            source_code=context.source.code,
            source_tender_id=raw.source_tender_id,
            title=str(raw.payload.get("title") or raw.source_tender_id),
            raw_payload=raw.payload,
        )

    def validate(self, draft: NormalizedTenderDraft, context: CollectionContext) -> ValidationResult:
        if not draft.source_tender_id:
            return ValidationResult(is_valid=False, errors=["source_tender_id is required"])
        return ValidationResult(is_valid=True)
