"""Collector registry and future source adapter stubs."""

from app.collectors.base import TenderCollector
from app.collectors.mock_collector import MockTenderCollector
from app.models.tender_source import TenderSource


class UPTenderCollector(TenderCollector):
    """Placeholder for Module 5 — no real UP collection logic."""

    code = "UP_TENDER"

    async def discover(self, context):
        raise NotImplementedError("UP tender collection is implemented in Module 5.")

    async def fetch_details(self, source_tender_id: str, context):
        raise NotImplementedError("UP tender collection is implemented in Module 5.")

    async def fetch_documents(self, source_tender_id: str, context):
        raise NotImplementedError("UP tender collection is implemented in Module 5.")

    def normalize(self, raw, context):
        raise NotImplementedError("UP tender collection is implemented in Module 5.")

    def validate(self, draft, context):
        raise NotImplementedError("UP tender collection is implemented in Module 5.")


class MPTenderCollector(TenderCollector):
    """Placeholder for Module 6 — no real MP collection logic."""

    code = "MP_TENDER"

    async def discover(self, context):
        raise NotImplementedError("MP tender collection is implemented in Module 6.")

    async def fetch_details(self, source_tender_id: str, context):
        raise NotImplementedError("MP tender collection is implemented in Module 6.")

    async def fetch_documents(self, source_tender_id: str, context):
        raise NotImplementedError("MP tender collection is implemented in Module 6.")

    def normalize(self, raw, context):
        raise NotImplementedError("MP tender collection is implemented in Module 6.")

    def validate(self, draft, context):
        raise NotImplementedError("MP tender collection is implemented in Module 6.")


class CollectorRegistry:
    _collectors: dict[str, type[TenderCollector]] = {
        "MOCK": MockTenderCollector,
        "UP_TENDER": UPTenderCollector,
        "MP_TENDER": MPTenderCollector,
    }

    @classmethod
    def register(cls, code: str, collector_cls: type[TenderCollector]) -> None:
        cls._collectors[code.upper()] = collector_cls

    @classmethod
    def get(cls, code: str) -> type[TenderCollector] | None:
        return cls._collectors.get(code.upper())

    @classmethod
    def known_codes(cls) -> list[str]:
        return sorted(cls._collectors.keys())


def get_collector_for_source(source: TenderSource) -> TenderCollector | None:
    if source.code.startswith("TEST_") or source.code == "MOCK":
        return MockTenderCollector()
    collector_cls = CollectorRegistry.get(source.code)
    if collector_cls is None:
        return None
    return collector_cls()
