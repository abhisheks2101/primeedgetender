"""Create tender source and collection architecture tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_tender_sources"
down_revision: Union[str, None] = "003_company_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tender_source_type_enum = postgresql.ENUM(
    "GOVERNMENT_PORTAL", "API", "PUBLIC_DATA", "OTHER", name="tender_source_type", create_type=False
)
collection_method_enum = postgresql.ENUM(
    "HTTP", "API", "HTML", "DOCUMENT", "OTHER", name="collection_method", create_type=False
)
collection_job_status_enum = postgresql.ENUM(
    "QUEUED", "RUNNING", "COMPLETED", "PARTIAL", "FAILED", "CANCELLED",
    name="collection_job_status",
    create_type=False,
)
source_health_status_enum = postgresql.ENUM(
    "HEALTHY", "DEGRADED", "FAILED", "UNKNOWN", name="source_health_status", create_type=False
)
collection_event_level_enum = postgresql.ENUM(
    "INFO", "WARNING", "ERROR", name="collection_event_level", create_type=False
)
collection_error_type_enum = postgresql.ENUM(
    "NETWORK", "TIMEOUT", "HTTP", "PARSING", "VALIDATION", "SOURCE_UNAVAILABLE", "UNEXPECTED",
    name="collection_error_type",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    tender_source_type_enum.create(bind, checkfirst=True)
    collection_method_enum.create(bind, checkfirst=True)
    collection_job_status_enum.create(bind, checkfirst=True)
    source_health_status_enum.create(bind, checkfirst=True)
    collection_event_level_enum.create(bind, checkfirst=True)
    collection_error_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "tender_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("authority", sa.String(length=255), nullable=True),
        sa.Column("portal_url", sa.String(length=500), nullable=True),
        sa.Column("source_type", tender_source_type_enum, nullable=False),
        sa.Column("collection_method", collection_method_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("health_status", source_health_status_enum, nullable=False, server_default="UNKNOWN"),
        sa.Column("last_collection_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_collection_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_tender_sources_code"),
    )
    op.create_index("ix_tender_sources_code", "tender_sources", ["code"], unique=True)
    op.create_index("ix_tender_sources_state", "tender_sources", ["state"])
    op.create_index("ix_tender_sources_is_active", "tender_sources", ["is_active"])
    op.create_index("ix_tender_sources_health_status", "tender_sources", ["health_status"])

    op.create_table(
        "tender_collection_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", collection_job_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_discovered", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_collection_jobs_source_id", "tender_collection_jobs", ["tender_source_id"])
    op.create_index("ix_tender_collection_jobs_status", "tender_collection_jobs", ["status"])
    op.create_index("ix_tender_collection_jobs_started_at", "tender_collection_jobs", ["started_at"])
    op.create_index("ix_tender_collection_jobs_completed_at", "tender_collection_jobs", ["completed_at"])

    op.create_table(
        "tender_collection_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_collection_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tender_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", collection_event_level_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("error_type", collection_error_type_enum, nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_collection_events_job_id", "tender_collection_events", ["job_id"])

    op.create_table(
        "tender_raw_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_collection_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tender_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_tender_id", sa.String(length=255), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_raw_records_source_id", "tender_raw_records", ["tender_source_id"])
    op.create_index("ix_tender_raw_records_source_tender_id", "tender_raw_records", ["source_tender_id"])


def downgrade() -> None:
    op.drop_table("tender_raw_records")
    op.drop_table("tender_collection_events")
    op.drop_table("tender_collection_jobs")
    op.drop_table("tender_sources")

    bind = op.get_bind()
    collection_error_type_enum.drop(bind, checkfirst=True)
    collection_event_level_enum.drop(bind, checkfirst=True)
    source_health_status_enum.drop(bind, checkfirst=True)
    collection_job_status_enum.drop(bind, checkfirst=True)
    collection_method_enum.drop(bind, checkfirst=True)
    tender_source_type_enum.drop(bind, checkfirst=True)
