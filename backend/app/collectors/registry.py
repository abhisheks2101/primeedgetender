"""Collector registry."""

from app.collectors.base import TenderCollector
from app.collectors.mock_collector import MockTenderCollector
from app.collectors.mp.mp_collector import MPTenderCollector
from app.collectors.up.up_collector import UPTenderCollector
from app.models.tender_source import TenderSource


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
