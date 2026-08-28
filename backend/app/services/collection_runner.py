"""Collection runner used by collectors and API endpoints."""

import hashlib
import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.collectors.base import CollectionContext, TenderCollector
from app.collectors.errors import CollectionError
from app.collectors.mock_collector import MockCollectionScenario, MockTenderCollector
from app.collectors.registry import get_collector_for_source
from app.collectors.retry import RetryPolicy, retry_async
from app.core.enums import CollectionErrorType, CollectionEventLevel, CollectionJobStatus
from app.models.tender_source import TenderCollectionJob, TenderRawRecord
from app.schemas.tender_source import SourceConfiguration
from app.services.collection_job_service import CollectionJobService
from app.services.tender_service import TenderService
from app.services.tender_source_service import TenderSourceService

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "api_key", "apikey"}


def sanitize_context(context: dict | None) -> dict | None:
    if not context:
        return None
    sanitized: dict = {}
    for key, value in context.items():
        if any(part in key.lower() for part in SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_context(value)
        else:
            sanitized[key] = value
    return sanitized


class CollectionRunner:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.source_service = TenderSourceService(db)
        self.job_service = CollectionJobService(db)
        self.tender_service = TenderService(db)

    async def run_for_source(self, source_id: UUID) -> TenderCollectionJob:
        source = self.source_service.get_source_or_404(source_id)
        if not source.is_active:
            raise ValueError("Tender source is inactive.")

        collector = get_collector_for_source(source)
        if collector is None:
            raise ValueError(f"No collector registered for source code {source.code}.")

        return await self.run_with_collector(source_id, collector)

    async def run_with_collector(
        self,
        source_id: UUID,
        collector: TenderCollector,
        *,
        scenario: MockCollectionScenario | None = None,
        job_id: UUID | None = None,
    ) -> TenderCollectionJob:
        source = self.source_service.get_source_or_404(source_id)
        configuration = self.source_service.parse_configuration(source)

        if job_id is not None:
            job = self.job_service.get_job_model_or_404(job_id)
        else:
            job = self.job_service.create_job(source)
        self.job_service.mark_running(job, source)
        self.job_service.log_event(
            job=job,
            source_id=source.id,
            level=CollectionEventLevel.INFO,
            message="Collection started",
        )

        if isinstance(collector, MockTenderCollector) and scenario is not None:
            collector.scenario = scenario

        context = CollectionContext(source=source, job_id=job.id, configuration=configuration)
        policy = RetryPolicy(
            max_attempts=configuration.retry_count + 1,
            delay_seconds=configuration.request_delay_seconds,
        )

        pages_accessed = 0

        try:
            discovery = await retry_async(lambda: collector.discover(context), policy=policy, operation_name="discover")
            pages_accessed += 1
            job.records_discovered = len(discovery.items)
            self.job_service.log_event(
                job=job,
                source_id=source.id,
                level=CollectionEventLevel.INFO,
                message="Page fetched",
                context=sanitize_context({"pages_accessed": pages_accessed}),
            )
            self.job_service.log_event(
                job=job,
                source_id=source.id,
                level=CollectionEventLevel.INFO,
                message=f"{job.records_discovered} tenders discovered",
            )

            if not discovery.items:
                self.job_service.finalize_job(job, source, status=CollectionJobStatus.COMPLETED)
                await self._close_collector(collector)
                return job

            for item in discovery.items[: configuration.max_requests_per_collection]:
                job.records_processed += 1
                context.current_summary = item.payload.get("summary", item.payload)
                context.current_detail_payload = None
                try:
                    details = await retry_async(
                        lambda tender_id=item.source_tender_id: collector.fetch_details(tender_id, context),
                        policy=policy,
                        operation_name="fetch_details",
                    )
                    pages_accessed += 1
                    documents = await collector.fetch_documents(details.source_tender_id, context)
                    draft = collector.normalize(details, context)
                    validation = collector.validate(draft, context)
                    if not validation.is_valid:
                        job.records_failed += 1
                        self.job_service.log_event(
                            job=job,
                            source_id=source.id,
                            level=CollectionEventLevel.WARNING,
                            message="Could not validate tender",
                            error_type=CollectionErrorType.VALIDATION,
                            context=sanitize_context(
                                {
                                    "source_tender_id": details.source_tender_id,
                                    "errors": validation.errors,
                                }
                            ),
                        )
                        continue

                    payload_hash = hashlib.sha256(
                        json.dumps(details.payload, sort_keys=True, default=str).encode("utf-8")
                    ).hexdigest()
                    raw_record = TenderRawRecord(
                        job_id=job.id,
                        tender_source_id=source.id,
                        source_tender_id=details.source_tender_id,
                        raw_payload=details.payload,
                        payload_hash=payload_hash,
                    )
                    self.db.add(raw_record)

                    tender, action = self.tender_service.upsert_from_draft(
                        source_id=source.id,
                        source_code=source.code,
                        draft=draft,
                        payload=details.payload,
                        documents=documents or draft.documents,
                    )

                    if action == "created":
                        job.records_created += 1
                        event_message = "Tender created"
                    elif action == "updated":
                        job.records_updated += 1
                        event_message = "Tender updated"
                    else:
                        job.records_skipped += 1
                        event_message = "Tender skipped"

                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.INFO,
                        message=event_message,
                        context=sanitize_context(
                            {
                                "source_tender_id": details.source_tender_id,
                                "tender_id": str(tender.id),
                                "pages_accessed": pages_accessed,
                            }
                        ),
                    )
                except CollectionError as exc:
                    job.records_failed += 1
                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.WARNING,
                        message=str(exc),
                        error_type=exc.error_type,
                        context=sanitize_context({"source_tender_id": item.source_tender_id}),
                    )
                except Exception:
                    job.records_failed += 1
                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.ERROR,
                        message="Unexpected error while processing tender",
                        error_type=CollectionErrorType.UNEXPECTED,
                        context=sanitize_context({"source_tender_id": item.source_tender_id}),
                    )

            self.db.commit()
            final_status = self._resolve_final_status(job)
            self.job_service.finalize_job(job, source, status=final_status)
            self.job_service.log_event(
                job=job,
                source_id=source.id,
                level=CollectionEventLevel.INFO,
                message="Collection completed",
                context=sanitize_context({"pages_accessed": pages_accessed}),
            )
            await self._close_collector(collector)
            return job
        except CollectionError as exc:
            self.job_service.log_event(
                job=job,
                source_id=source.id,
                level=CollectionEventLevel.ERROR,
                message=str(exc),
                error_type=exc.error_type,
            )
            self.job_service.finalize_job(job, source, status=CollectionJobStatus.FAILED, error_message=str(exc))
            await self._close_collector(collector)
            return job

    @staticmethod
    def _resolve_final_status(job: TenderCollectionJob) -> CollectionJobStatus:
        if job.records_failed and (job.records_created or job.records_updated or job.records_skipped):
            return CollectionJobStatus.PARTIAL
        if job.records_failed and not (job.records_created or job.records_updated or job.records_skipped):
            return CollectionJobStatus.FAILED
        return CollectionJobStatus.COMPLETED

    @staticmethod
    async def _close_collector(collector: TenderCollector) -> None:
        close = getattr(collector, "close", None)
        if callable(close):
            await close()
