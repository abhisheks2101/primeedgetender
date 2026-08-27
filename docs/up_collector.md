# UP Tender Collector (Module 5)

Module 5 connects the generic tender-source architecture from Module 4 to the official Uttar Pradesh NIC GeP portal and stores normalized tenders in PostgreSQL.

**Automated tests use mocked HTTP responses and do not access the live UP portal.**

## Source

| Item | Value |
|------|-------|
| Source code | `UP_TENDER` |
| Official portal | https://etender.up.nic.in/nicgep/app |
| Public listing used | Home page `#activeTenders` table (`?page=Home&service=page`) |
| Detail pages | `FrontEndViewTender` direct links (`sp=` tender parameter) |
| Collection method | HTML parsing via `UPTenderCollector` |

Configure the source through the existing `TenderSource.configuration` JSON (seeded by `python -m app.cli seed-tender-sources`).

## Collection Architecture

```text
UPPortalClient (httpx, session cookies, honest User-Agent)
    ↓
UP HTML parsers (listing, detail, dates, amounts, status, documents)
    ↓
UPTenderCollector (discover → fetch_details → fetch_documents → normalize → validate)
    ↓
CollectionRunner (jobs, events, raw records, tender upsert)
    ↓
PostgreSQL (`tenders`, `tender_documents`, `tender_raw_records`)
```

## Supported Fields

| Field | Status | Notes |
|-------|--------|-------|
| Source tender ID | Available | From detail page Tender ID / listing `sp` parameter |
| Reference number | Available | Detail page |
| Title | Available | Listing + detail |
| Work description | Available | Detail page |
| Organization / department | Available | Organisation Chain on detail page |
| Tender type / category | Available | Detail page when present |
| Location / district / state | Available | Location text preserved; state defaulted to Uttar Pradesh |
| Estimated tender value | Partial | Often `NA` on portal |
| EMD | Available | Detail page when present |
| Tender fee | Available | Detail page when present |
| Publication date | Available | Detail page |
| Document sale start/end | Available | Detail page |
| Submission start/end | Available | Detail page / listing closing date |
| Opening date | Available | Listing + detail |
| Tender status | Derived | Inferred OPEN/CLOSED from submission end date; no explicit portal status field |
| Tender URL | Available | Listing direct link |
| Document URLs | Available | Public `docDownoad` links on detail page |
| Technical eligibility | Not available | Only inside downloaded documents |
| Full paginated search | Not available without CAPTCHA | See limitations below |

## Collection Process

1. Admin triggers `POST /api/tender-sources/{source_id}/collect` or runs the CLI manual command.
2. A `TenderCollectionJob` is created (QUEUED → RUNNING).
3. The collector fetches the public home listing (one page).
4. For each discovered tender (up to `max_requests_per_collection`), the collector fetches the detail page sequentially with configurable delay.
5. Data is validated, raw payload stored, and normalized tender upserted by `(tender_source_id, source_tender_id)`.
6. Job statistics and events are recorded; frontend polls job status.

## Rate / Request Configuration

Configured per source (`SourceConfiguration`):

- `request_timeout_seconds` (default 30)
- `retry_count` (default 2; retries temporary network/timeout/5xx errors)
- `request_delay_seconds` (default 1.5 between requests)
- `max_requests_per_collection` (default 50)
- `pagination.page_size` (limits home listing items processed; default 10)

User-Agent:

```text
TenderIntelligencePlatform/{version} (+https://github.com/abhisheks2101/primeedgetender; UP-tender-collector)
```

## Limitations

### Portal access

- **Home listing**: publicly accessible without CAPTCHA (~10 latest active tenders).
- **Full paginated listing / filters** (`FrontEndLatestActiveTenders`, organisation, location, classification): require CAPTCHA — **not automated**.
- **Detail pages**: require session cookies; collector uses a persistent httpx client.
- **No CAPTCHA bypass, login bypass, or anti-bot evasion** is attempted.

### Field gaps

Fields not exposed on the public listing/detail HTML are stored as `NULL` / `UNKNOWN`. The collector never guesses missing values.

## Manual Live Collection Procedure

This is for developer verification only — not CI.

```bash
cd backend
. .venv/bin/activate
alembic upgrade head
python -m app.cli seed-tender-sources
python -m app.cli collect-up
```

The command prints discovered/created/updated/skipped/failed counts and duration.

Admin UI: open `/admin/tender-sources/{id}` for the `UP_TENDER` source and click **Collect Now**.

## Testing

- Unit tests: `backend/tests/unit/test_up_parsers.py`
- Integration tests (mocked HTTP): `backend/tests/integration/test_up_collector.py`
- Mock fixtures: `backend/tests/fixtures/up/`

Run:

```bash
cd backend && pytest
```

## Duplicate Handling

Upsert key: `tender_source_id + source_tender_id`.

If payload hash is unchanged, the tender is **skipped** (not duplicated). Changed payloads update the existing row and replace document references.

## Module Boundaries

Module 5 does **not** include:

- MP collector (Module 6)
- Matching, AI, OCR, recommendations, dashboard, notifications
