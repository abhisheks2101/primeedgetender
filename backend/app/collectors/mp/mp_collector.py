"""Madhya Pradesh government tender collector."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app import __version__
from app.collectors.base import (
    CollectionContext,
    DiscoveryResult,
    NormalizedTenderDraft,
    RawDocumentRef,
    RawTenderData,
    TenderCollector,
    ValidationResult,
)
from app.collectors.errors import ParsingCollectionError
from app.collectors.mp import mp_parsers
from app.collectors.mp.mp_client import MPPortalClient


class MPTenderCollector(TenderCollector):
    """Collects publicly listed MP tenders from the NIC GeP home page and detail pages."""

    code = "MP_TENDER"

    def __init__(
        self,
        *,
        client_factory: type[MPPortalClient] | None = None,
        transport=None,
    ) -> None:
        self._client_factory = client_factory or MPPortalClient
        self._transport = transport
        self._client: MPPortalClient | None = None

    async def _get_client(self, context: CollectionContext) -> MPPortalClient:
        if self._client is None:
            self._client = self._client_factory(
                context.configuration,
                app_version=__version__,
                transport=self._transport,
            )
            await self._client.__aenter__()
        return self._client

    async def discover(self, context: CollectionContext) -> DiscoveryResult:
        client = await self._get_client(context)
        html = await client.fetch_home_listing()
        summaries = mp_parsers.parse_listing_page(html, client.listing_page_url())

        pagination = context.configuration.pagination or {}
        page_size = int(pagination.get("page_size", len(summaries) or 10))
        max_items = min(page_size, context.configuration.max_requests_per_collection)

        items = [
            RawTenderData(
                source_tender_id=summary["source_tender_id"],
                payload={"summary": summary, "discovery_source": "home_active_tenders"},
            )
            for summary in summaries[:max_items]
        ]
        return DiscoveryResult(items=items)

    async def fetch_details(self, source_tender_id: str, context: CollectionContext) -> RawTenderData:
        client = await self._get_client(context)
        summary_payload = context.current_summary
        detail_url = summary_payload.get("detail_url") if summary_payload else None

        if not detail_url:
            raise ParsingCollectionError(f"Could not resolve MP detail URL for tender {source_tender_id}.")

        html = await client.fetch_detail_page(detail_url)
        detail = mp_parsers.parse_tender_detail(html, detail_url)
        payload = {
            "summary": summary_payload or {},
            "detail": detail,
            "detail_html_length": len(html),
        }
        resolved_id = detail.get("source_tender_id") or source_tender_id
        context.current_detail_payload = payload
        return RawTenderData(source_tender_id=resolved_id, payload=payload)

    async def fetch_documents(
        self,
        source_tender_id: str,
        context: CollectionContext,
    ) -> list[RawDocumentRef]:
        if not context.current_detail_payload:
            await self.fetch_details(source_tender_id, context)
        payload = context.current_detail_payload or {}
        documents = payload.get("detail", {}).get("documents", [])
        return [
            RawDocumentRef(
                document_id=document.get("document_id") or document.get("document_name") or "document",
                title=document.get("document_name"),
                url=document.get("document_url"),
            )
            for document in documents
        ]

    def normalize(self, raw: RawTenderData, context: CollectionContext) -> NormalizedTenderDraft:
        summary = raw.payload.get("summary", {})
        detail = raw.payload.get("detail", {})

        def parse_iso(value: str | None) -> datetime | None:
            if not value:
                return None
            try:
                parsed = datetime.fromisoformat(value)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except ValueError:
                return None

        def parse_decimal(value: str | None) -> Decimal | None:
            if value is None:
                return None
            try:
                return Decimal(value)
            except Exception:
                return None

        submission_end = parse_iso(detail.get("submission_end")) or parse_iso(summary.get("submission_end"))
        status, source_status = mp_parsers.parse_status(submission_end)

        return NormalizedTenderDraft(
            source_code=context.source.code,
            source_tender_id=raw.source_tender_id,
            reference_number=detail.get("reference_number") or summary.get("reference_number"),
            title=detail.get("title") or summary.get("title"),
            work_description=detail.get("work_description"),
            organization=detail.get("organization"),
            department=detail.get("organization"),
            tender_type=detail.get("tender_type"),
            tender_category=detail.get("tender_category"),
            location=detail.get("location"),
            district=detail.get("district"),
            state=detail.get("state") or mp_parsers.DEFAULT_STATE,
            estimated_value=parse_decimal(detail.get("estimated_value")),
            emd_amount=parse_decimal(detail.get("emd_amount")),
            tender_fee=parse_decimal(detail.get("tender_fee")),
            publication_date=parse_iso(detail.get("publication_date")),
            document_sale_start=parse_iso(detail.get("document_sale_start")),
            document_sale_end=parse_iso(detail.get("document_sale_end")),
            submission_start=parse_iso(detail.get("submission_start")),
            submission_end=submission_end,
            opening_date=parse_iso(detail.get("opening_date")) or parse_iso(summary.get("opening_date")),
            status=status,
            source_status=source_status,
            source_url=detail.get("detail_url") or summary.get("detail_url"),
            raw_payload=raw.payload,
            documents=[
                RawDocumentRef(
                    document_id=doc.get("document_id") or doc.get("document_name") or "document",
                    title=doc.get("document_name"),
                    url=doc.get("document_url"),
                )
                for doc in detail.get("documents", [])
            ],
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

    async def close(self) -> None:
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None
