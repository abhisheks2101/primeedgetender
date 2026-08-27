# Tender Source Architecture (Module 4)

Module 4 introduces the reusable collection framework for future UP and MP collectors. **Actual UP and MP tender collection is NOT implemented in Module 4.**

## Overview

```text
                Tender Source Manager
                          │
         ┌────────────────┼────────────────┐
         ↓                ↓                ↓
   UP Collector      MP Collector      Future Sources
   (Module 5)        (Module 6)
         │                │                │
         └────────────────┼────────────────┘
                          ↓
                 Common Tender Model (future)
                          ↓
                     PostgreSQL
```

## Database Tables

| Table | Purpose |
|-------|---------|
| `tender_sources` | Configurable source definitions |
| `tender_collection_jobs` | Collection attempt history |
| `tender_collection_events` | Structured collection logs |
| `tender_raw_records` | Raw source payloads for later normalization |

## Source Configuration

Source-specific settings are stored as JSON on the source record. Supported fields:

| Field | Description |
|-------|-------------|
| `source_url` | Primary source URL |
| `search_url` | Search/list URL if applicable |
| `detail_url_pattern` | Optional detail URL pattern |
| `document_url_pattern` | Optional document URL pattern |
| `request_timeout_seconds` | Positive timeout in seconds |
| `retry_count` | Non-negative retry count |
| `request_delay_seconds` | Non-negative delay between requests |
| `max_requests_per_collection` | Maximum requests per collection run |
| `pagination` | Optional pagination metadata |

Secrets must **not** be stored in the database. Future authenticated sources should read credentials from environment variables or a secure secret mechanism.

## Collector Interface

All collectors implement `TenderCollector`:

- `discover()`
- `fetch_details()`
- `fetch_documents()`
- `normalize()`
- `validate()`

Registered adapters:

| Code | Class | Status |
|------|-------|--------|
| `MOCK` | `MockTenderCollector` | Test-only |
| `UP_TENDER` | `UPTenderCollector` | Placeholder for Module 5 |
| `MP_TENDER` | `MPTenderCollector` | Placeholder for Module 6 |

## Collection Jobs

Each collection attempt creates a `TenderCollectionJob` with statuses:

`QUEUED`, `RUNNING`, `COMPLETED`, `PARTIAL`, `FAILED`, `CANCELLED`

Jobs record discovered/processed/created/updated/skipped/failed counts, duration, and error messages.

## Retry Architecture

Temporary failures such as network timeouts use a configurable retry policy:

```text
Network timeout → retry → retry → final failure
```

Retry count and delay come from the source configuration. The framework avoids aggressive retrying.

## API Endpoints

| Method | Path | Access |
|--------|------|--------|
| GET | `/api/tender-sources` | Authenticated |
| GET | `/api/tender-sources/{id}` | Authenticated |
| POST | `/api/tender-sources` | Admin |
| PATCH | `/api/tender-sources/{id}` | Admin |
| PATCH | `/api/tender-sources/{id}/status` | Admin |
| GET | `/api/tender-sources/{id}/jobs` | Authenticated |
| GET | `/api/tender-collection/jobs` | Authenticated |
| GET | `/api/tender-collection/jobs/{id}` | Authenticated |

There is **no** live collection trigger endpoint in Module 4.

## Admin UI

- `/admin/tender-sources`
- `/admin/tender-sources/new`
- `/admin/tender-sources/[id]`

## Development Seed Data

```bash
cd backend
python -m app.cli seed-tender-sources
```

Seeds fictional sources `TEST_SOURCE_A` and `TEST_SOURCE_B`.

## Adding a New Source Later

1. Create a source record with a unique code.
2. Implement a collector class extending `TenderCollector`.
3. Register it in `CollectorRegistry`.
4. Wire collection execution in the appropriate future module.

The core framework, job tracking, logging, retry, and raw-record storage remain unchanged.

## Security

- All endpoints require authentication.
- Create/update/deactivate operations require `ADMIN`.
- URLs and numeric configuration values are validated.
- Logs redact sensitive keys such as `token`, `password`, and `secret`.
- Internal stack traces are not exposed through API responses.

## Limitations

- No UP collector implementation
- No MP collector implementation
- No live collection trigger API
- No deduplication engine (Module 7)
- No normalized tender model beyond draft/placeholder structures
- No AI, OCR, matching, alerts, or notifications
