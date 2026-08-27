# Company Profile & Document Management (Module 3)

## Overview

Module 3 introduces a multi-company profile system with structured registrations, financial history, capabilities, project experience, machinery, personnel, operating locations, and local document storage.

AI document extraction is **NOT** implemented in Module 3.

## Data Model

```text
Company
├── CompanyRegistration
├── ContractorRegistration
├── FinancialRecord
├── CompanyCapability -> CapabilityCategory
├── CompanyExperience
├── CompanyMachinery
├── CompanyPersonnel
├── CompanyLocation
└── CompanyDocument -> DocumentType
```

## Relationships

- Every child record belongs to exactly one `company_id`.
- Documents can optionally reference a related entity through `related_entity_type` + `related_entity_id`.
- Capability categories and document types are normalized lookup tables seeded by migration.

## Document Storage

- Interface: `StorageService`
- Default implementation: `LocalStorageService`
- Files stored under `UPLOAD_STORAGE_PATH` (default `storage/uploads`)
- PostgreSQL stores metadata only

## Authorization

| Role | Access |
|------|--------|
| ADMIN | Create, edit, archive companies and upload/manage documents |
| USER | Read company profiles and download documents |

## Seed Data

Optional fictional demo data:

```bash
cd backend
source .venv/bin/activate
python -m app.cli seed-companies
```

Marked as `DEVELOPMENT/DEMO DATA ONLY`.

## Upload Limits

Configured through environment variables:

- `MAX_UPLOAD_SIZE_BYTES` (default 10 MB)
- `ALLOWED_UPLOAD_MIME_TYPES`
- Executable uploads are blocked

## API Summary

Base path: `/api/companies`

Nested resources include registrations, contractor registrations, financial records, capabilities, experiences, machinery, personnel, locations, and documents.

Document download: `GET /api/documents/{id}/download`

## Migrations

```bash
cd backend
alembic upgrade head
```

Latest company migration: `003_company_profiles`
