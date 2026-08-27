"""Create company profile and document management tables."""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_company_profiles"
down_revision: Union[str, None] = "002_users_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

registration_status_enum = postgresql.ENUM(
    "ACTIVE", "EXPIRED", "SUSPENDED", "UNKNOWN", name="registration_status", create_type=False
)
project_status_enum = postgresql.ENUM(
    "COMPLETED", "ONGOING", "CANCELLED", "UNKNOWN", name="project_status", create_type=False
)
ownership_type_enum = postgresql.ENUM(
    "OWNED", "LEASED", "RENTED", "OTHER", name="ownership_type", create_type=False
)
document_entity_type_enum = postgresql.ENUM(
    "COMPANY",
    "REGISTRATION",
    "CONTRACTOR_REGISTRATION",
    "FINANCIAL_RECORD",
    "EXPERIENCE",
    "MACHINERY",
    "PERSONNEL",
    "OTHER",
    name="document_entity_type",
    create_type=False,
)
document_status_enum = postgresql.ENUM(
    "VALID", "EXPIRING_SOON", "EXPIRED", "UNKNOWN", name="document_status", create_type=False
)
financial_record_type_enum = postgresql.ENUM(
    "TURNOVER", "SOLVENCY", "NET_WORTH", "FINANCIAL_CAPACITY", "OTHER",
    name="financial_record_type",
    create_type=False,
)

DOCUMENT_TYPE_SEEDS: list[tuple[str, str]] = [
    ("COMPANY_REGISTRATION", "Company Registration"),
    ("GST_CERTIFICATE", "GST Certificate"),
    ("PAN_DOCUMENT", "PAN Document"),
    ("PWD_REGISTRATION", "PWD Registration"),
    ("CONTRACTOR_REGISTRATION", "Contractor Registration"),
    ("SOLVENCY_CERTIFICATE", "Solvency Certificate"),
    ("TURNOVER_CERTIFICATE", "Turnover Certificate"),
    ("WORK_ORDER", "Work Order"),
    ("COMPLETION_CERTIFICATE", "Completion Certificate"),
    ("EXPERIENCE_CERTIFICATE", "Experience Certificate"),
    ("MACHINERY_DOCUMENT", "Machinery Document"),
    ("STAFF_DOCUMENT", "Staff Document"),
    ("OTHER", "Other"),
]

CAPABILITY_CATEGORY_SEEDS: list[tuple[str, str, str]] = [
    ("ROAD_CONSTRUCTION", "Road Construction", "CIVIL"),
    ("DRAINAGE", "Drainage", "CIVIL"),
    ("EARTHWORK", "Earthwork", "CIVIL"),
    ("CIVIL_CONSTRUCTION", "Civil Construction", "CIVIL"),
    ("PAVER_BLOCK_WORK", "Paver Block Work", "CIVIL"),
    ("ASPHALT_WORK", "Asphalt Work", "CIVIL"),
]


def upgrade() -> None:
    bind = op.get_bind()
    registration_status_enum.create(bind, checkfirst=True)
    project_status_enum.create(bind, checkfirst=True)
    ownership_type_enum.create(bind, checkfirst=True)
    document_entity_type_enum.create(bind, checkfirst=True)
    document_status_enum.create(bind, checkfirst=True)
    financial_record_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("legal_name", sa.String(length=500), nullable=False),
        sa.Column("display_name", sa.String(length=500), nullable=False),
        sa.Column("legal_entity_type", sa.String(length=100), nullable=True),
        sa.Column("registration_number", sa.String(length=100), nullable=True),
        sa.Column("incorporation_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("registered_address", sa.Text(), nullable=True),
        sa.Column("office_address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("pin_code", sa.String(length=20), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_companies_legal_name", "companies", ["legal_name"], unique=False)
    op.create_index("ix_companies_display_name", "companies", ["display_name"], unique=False)
    op.create_index("ix_companies_registration_number", "companies", ["registration_number"], unique=False)
    op.create_index("ix_companies_district", "companies", ["district"], unique=False)
    op.create_index("ix_companies_state", "companies", ["state"], unique=False)

    op.create_table(
        "capability_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_capability_categories_code"),
    )
    op.create_index("ix_capability_categories_code", "capability_categories", ["code"], unique=True)
    op.create_index("ix_capability_categories_category", "capability_categories", ["category"], unique=False)

    op.create_table(
        "document_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("code", name="uq_document_types_code"),
    )
    op.create_index("ix_document_types_code", "document_types", ["code"], unique=True)

    op.create_table(
        "company_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("registration_type", sa.String(length=100), nullable=False),
        sa.Column("registration_number", sa.String(length=150), nullable=True),
        sa.Column("registration_class", sa.String(length=100), nullable=True),
        sa.Column("issuing_authority", sa.String(length=255), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            registration_status_enum,
            nullable=False,
            server_default=sa.text("'UNKNOWN'::registration_status"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_company_registrations_company_id", "company_registrations", ["company_id"], unique=False)
    op.create_index(
        "ix_company_registrations_registration_type", "company_registrations", ["registration_type"], unique=False
    )
    op.create_index(
        "ix_company_registrations_registration_number", "company_registrations", ["registration_number"], unique=False
    )
    op.create_index("ix_company_registrations_expiry_date", "company_registrations", ["expiry_date"], unique=False)

    op.create_table(
        "contractor_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("registration_authority", sa.String(length=255), nullable=True),
        sa.Column("registration_number", sa.String(length=150), nullable=True),
        sa.Column("class_category", sa.String(length=100), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            registration_status_enum,
            nullable=False,
            server_default=sa.text("'UNKNOWN'::registration_status"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_contractor_registrations_company_id", "contractor_registrations", ["company_id"], unique=False)
    op.create_index(
        "ix_contractor_registrations_registration_number",
        "contractor_registrations",
        ["registration_number"],
        unique=False,
    )
    op.create_index("ix_contractor_registrations_expiry_date", "contractor_registrations", ["expiry_date"], unique=False)

    op.create_table(
        "financial_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_type", financial_record_type_enum, nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"),
        sa.Column("financial_year", sa.String(length=20), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_financial_records_company_id", "financial_records", ["company_id"], unique=False)
    op.create_index("ix_financial_records_financial_year", "financial_records", ["financial_year"], unique=False)

    op.create_table(
        "company_capabilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "capability_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("capability_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("years_of_experience", sa.Integer(), nullable=True),
        sa.Column("experience_level", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_projects_count", sa.Integer(), nullable=True),
        sa.Column("total_project_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("company_id", "capability_id", name="uq_company_capability"),
    )
    op.create_index("ix_company_capabilities_company_id", "company_capabilities", ["company_id"], unique=False)
    op.create_index("ix_company_capabilities_capability_id", "company_capabilities", ["capability_id"], unique=False)

    op.create_table(
        "company_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("project_name", sa.String(length=500), nullable=False),
        sa.Column("client_department", sa.String(length=255), nullable=True),
        sa.Column("authority_organization", sa.String(length=255), nullable=True),
        sa.Column("work_category", sa.String(length=100), nullable=True),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("contract_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("awarded_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("completion_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column(
            "project_status",
            project_status_enum,
            nullable=False,
            server_default=sa.text("'UNKNOWN'::project_status"),
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope_of_work", sa.Text(), nullable=True),
        sa.Column("experience_type", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_company_experiences_company_id", "company_experiences", ["company_id"], unique=False)
    op.create_index("ix_company_experiences_category", "company_experiences", ["work_category"], unique=False)
    op.create_index(
        "ix_company_experiences_state_district", "company_experiences", ["state", "district"], unique=False
    )
    op.create_index("ix_company_experiences_completion_date", "company_experiences", ["completion_date"], unique=False)

    op.create_table(
        "company_machinery",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("equipment_name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column(
            "ownership_type",
            ownership_type_enum,
            nullable=False,
            server_default=sa.text("'OTHER'::ownership_type"),
        ),
        sa.Column("registration_number", sa.String(length=150), nullable=True),
        sa.Column("capacity_specification", sa.String(length=255), nullable=True),
        sa.Column("available_from", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_company_machinery_company_id", "company_machinery", ["company_id"], unique=False)

    op.create_table(
        "company_personnel",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("designation", sa.String(length=150), nullable=False),
        sa.Column("qualification", sa.String(length=255), nullable=True),
        sa.Column("specialization", sa.String(length=255), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("employment_type", sa.String(length=100), nullable=True),
        sa.Column("availability", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_company_personnel_company_id", "company_personnel", ["company_id"], unique=False)

    op.create_table(
        "company_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("region", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_company_locations_company_id", "company_locations", ["company_id"], unique=False)
    op.create_index("ix_company_locations_state", "company_locations", ["state"], unique=False)
    op.create_index("ix_company_locations_district", "company_locations", ["district"], unique=False)

    op.create_table(
        "company_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "related_entity_type",
            document_entity_type_enum,
            nullable=False,
            server_default=sa.text("'COMPANY'::document_entity_type"),
        ),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("stored_filename", sa.String(length=500), nullable=False),
        sa.Column("file_extension", sa.String(length=20), nullable=True),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "document_status",
            document_status_enum,
            nullable=False,
            server_default=sa.text("'UNKNOWN'::document_status"),
        ),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("stored_filename", name="uq_company_documents_stored_filename"),
    )
    op.create_index("ix_company_documents_company_id", "company_documents", ["company_id"], unique=False)
    op.create_index("ix_company_documents_document_type_id", "company_documents", ["document_type_id"], unique=False)
    op.create_index("ix_company_documents_related_entity_id", "company_documents", ["related_entity_id"], unique=False)
    op.create_index("ix_company_documents_expiry_date", "company_documents", ["expiry_date"], unique=False)
    op.create_index(
        "ix_company_documents_company_type", "company_documents", ["company_id", "document_type_id"], unique=False
    )

    for code, name in DOCUMENT_TYPE_SEEDS:
        seed_id = uuid.uuid4()
        op.execute(
            f"INSERT INTO document_types (id, code, name, is_active, created_at) "
            f"VALUES ('{seed_id}', '{code}', '{name}', true, now())"
        )

    for code, name, category in CAPABILITY_CATEGORY_SEEDS:
        seed_id = uuid.uuid4()
        op.execute(
            f"INSERT INTO capability_categories (id, code, name, category, is_active, created_at) "
            f"VALUES ('{seed_id}', '{code}', '{name}', '{category}', true, now())"
        )


def downgrade() -> None:
    op.drop_index("ix_company_documents_company_type", table_name="company_documents")
    op.drop_index("ix_company_documents_expiry_date", table_name="company_documents")
    op.drop_index("ix_company_documents_related_entity_id", table_name="company_documents")
    op.drop_index("ix_company_documents_document_type_id", table_name="company_documents")
    op.drop_index("ix_company_documents_company_id", table_name="company_documents")
    op.drop_table("company_documents")

    op.drop_index("ix_company_locations_district", table_name="company_locations")
    op.drop_index("ix_company_locations_state", table_name="company_locations")
    op.drop_index("ix_company_locations_company_id", table_name="company_locations")
    op.drop_table("company_locations")

    op.drop_index("ix_company_personnel_company_id", table_name="company_personnel")
    op.drop_table("company_personnel")

    op.drop_index("ix_company_machinery_company_id", table_name="company_machinery")
    op.drop_table("company_machinery")

    op.drop_index("ix_company_experiences_completion_date", table_name="company_experiences")
    op.drop_index("ix_company_experiences_state_district", table_name="company_experiences")
    op.drop_index("ix_company_experiences_category", table_name="company_experiences")
    op.drop_index("ix_company_experiences_company_id", table_name="company_experiences")
    op.drop_table("company_experiences")

    op.drop_index("ix_company_capabilities_capability_id", table_name="company_capabilities")
    op.drop_index("ix_company_capabilities_company_id", table_name="company_capabilities")
    op.drop_table("company_capabilities")

    op.drop_index("ix_financial_records_financial_year", table_name="financial_records")
    op.drop_index("ix_financial_records_company_id", table_name="financial_records")
    op.drop_table("financial_records")

    op.drop_index("ix_contractor_registrations_expiry_date", table_name="contractor_registrations")
    op.drop_index("ix_contractor_registrations_registration_number", table_name="contractor_registrations")
    op.drop_index("ix_contractor_registrations_company_id", table_name="contractor_registrations")
    op.drop_table("contractor_registrations")

    op.drop_index("ix_company_registrations_expiry_date", table_name="company_registrations")
    op.drop_index("ix_company_registrations_registration_number", table_name="company_registrations")
    op.drop_index("ix_company_registrations_registration_type", table_name="company_registrations")
    op.drop_index("ix_company_registrations_company_id", table_name="company_registrations")
    op.drop_table("company_registrations")

    op.drop_index("ix_document_types_code", table_name="document_types")
    op.drop_table("document_types")

    op.drop_index("ix_capability_categories_category", table_name="capability_categories")
    op.drop_index("ix_capability_categories_code", table_name="capability_categories")
    op.drop_table("capability_categories")

    op.drop_index("ix_companies_state", table_name="companies")
    op.drop_index("ix_companies_district", table_name="companies")
    op.drop_index("ix_companies_registration_number", table_name="companies")
    op.drop_index("ix_companies_display_name", table_name="companies")
    op.drop_index("ix_companies_legal_name", table_name="companies")
    op.drop_table("companies")

    bind = op.get_bind()
    financial_record_type_enum.drop(bind, checkfirst=True)
    document_status_enum.drop(bind, checkfirst=True)
    document_entity_type_enum.drop(bind, checkfirst=True)
    ownership_type_enum.drop(bind, checkfirst=True)
    project_status_enum.drop(bind, checkfirst=True)
    registration_status_enum.drop(bind, checkfirst=True)
