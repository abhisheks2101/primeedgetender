"""Collection runner used by tests and future collector modules."""

import hashlib
import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.collectors.base import CollectionContext, TenderCollector
from app.collectors.errors import CollectionError
from app.collectors.mock_collector import MockCollectionScenario, MockTenderCollector
from app.collectors.retry import RetryPolicy, retry_async
from app.core.enums import CollectionErrorType, CollectionEventLevel, CollectionJobStatus, SourceHealthStatus
from app.models.tender_source import TenderRawRecord
from app.schemas.tender_source import SourceConfiguration
from app.services.collection_job_service import CollectionJobService
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

    async def run_with_collector(
        self,
        source_id: UUID,
        collector: TenderCollector,
        *,
        scenario: MockCollectionScenario | None = None,
    ):
        source = self.source_service.get_source_or_404(source_id)
        configuration = self.source_service.parse_configuration(source)
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

        try:
            discovery = await retry_async(lambda: collector.discover(context), policy=policy, operation_name="discover")
            job.records_discovered = len(discovery.items)
            self.job_service.log_event(
                job=job,
                source_id=source.id,
                level=CollectionEventLevel.INFO,
                message=f"{job.records_discovered} tenders discovered",
            )

            if not discovery.items:
                self.job_service.finalize_job(job, source, status=CollectionJobStatus.COMPLETED)
                return job

            for item in discovery.items[: configuration.max_requests_per_collection]:
                job.records_processed += 1
                try:
                    details = await collector.fetch_details(item.source_tender_id, context)
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
                            context=sanitize_context({"errors": validation.errors}),
                        )
                        continue

                    payload_hash = hashlib.sha256(
                        json.dumps(details.payload, sort_keys=True).encode("utf-8")
                    ).hexdigest()
                    raw_record = TenderRawRecord(
                        job_id=job.id,
                        tender_source_id=source.id,
                        source_tender_id=details.source_tender_id,
                        raw_payload=details.payload,
                        payload_hash=payload_hash,
                    )
                    self.db.add(raw_record)
                    job.records_created += 1
                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.INFO,
                        message="Page processed",
                        context=sanitize_context({"source_tender_id": details.source_tender_id}),
                    )
                except CollectionError as exc:
                    job.records_failed += 1
                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.WARNING,
                        message=str(exc),
                        error_type=exc.error_type,
                    )
                except Exception:
                    job.records_failed += 1
                    self.job_service.log_event(
                        job=job,
                        source_id=source.id,
                        level=CollectionEventLevel.ERROR,
                        message="Unexpected error while processing tender",
                        error_type=CollectionErrorType.UNEXPECTED,
                    )

            self.db.commit()
            final_status = (
                CollectionJobStatus.PARTIAL
                if job.records_failed and job.records_created
                else CollectionJobStatus.FAILED
                if job.records_failed and not job.records_created
                else CollectionJobStatus.COMPLETED
            )
            self.job_service.finalize_job(job, source, status=final_status)
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
            return job
