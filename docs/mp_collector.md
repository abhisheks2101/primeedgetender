# MP Tender Collector (Module 6)

Module 6 connects the generic tender-source architecture to the official Madhya Pradesh NIC GeP portal and stores normalized tenders in PostgreSQL.

**Automated tests use mocked HTTP responses and do not access the live MP portal.**

## Source

| Item | Value |
|------|-------|
| Source code | `MP_TENDER` |
| Official portal | https://mptenders.gov.in/nicgep/app |
| Public listing used | Home page `#activeTenders` table (`?page=Home&service=page`) |
| Detail pages | `DirectLink` URLs with `sp=` session parameter |
| Collection method | HTML parsing via `MPTenderCollector` |

## Collection Architecture

```text
MPPortalClient (httpx, session cookies, honest User-Agent)
    ↓
MP HTML parsers (listing, detail, dates, amounts, status, documents)
    ↓
MPTenderCollector (discover → fetch_details → fetch_documents → normalize → validate)
    ↓
CollectionRunner (jobs, events, raw records, tender upsert)
    ↓
PostgreSQL (`tenders`, `tender_documents`, `tender_raw_records`)
```

## Supported Fields

| Field | Status | Notes |
|-------|--------|-------|
| Source tender ID | Available | Tender ID from detail page (e.g. `2026_UAD_532631_1`) |
| Reference number | Available | Listing + detail |
| Title | Available | MP detail uses `Title` caption |
| Work description | Available | Detail page |
| Organization / department | Available | Organisation Chain |
| Tender type / category | Available | Includes Form of Contract on MP portal |
| Location / district / state | Available | State defaulted to Madhya Pradesh |
| Estimated tender value | Available | Often present as Tender Value |
| EMD | Available | Detail page |
| Tender fee | Available | Detail page |
| Publication date | Available | Detail page |
| Document sale dates | Available | MP uses "Document Download / Sale" captions |
| Submission dates | Available | Listing closing date + detail |
| Opening date | Available | Listing + detail |
| Tender status | Derived | OPEN/CLOSED from submission end date |
| Tender URL | Available | Listing direct link |
| Document URLs | Available | Public `docDownoad` links |
| Processing fee | Not stored | MP portal shows separate processing fee; not mapped to tender model |
| Technical eligibility | Not available | Inside documents only |
| Full paginated search | Not available | CAPTCHA on `FrontEndLatestActiveTenders` |

## Configuration

Seeded via `python -m app.cli seed-tender-sources`:

- `request_timeout_seconds`: 90
- `retry_count`: 3
- `request_delay_seconds`: 2.0
- `max_requests_per_collection`: 50
- `pagination.page_size`: 10

## Manual Live Collection

```bash
cd backend
. .venv/bin/activate
alembic upgrade head
python -m app.cli seed-tender-sources
python -m app.cli collect-mp
```

Or use **Collect Now** on the `MP_TENDER` source in `/admin/tender-sources`.

## Limitations

- Home listing only (~10 latest active tenders without CAPTCHA)
- Full search/filter pages require CAPTCHA — not automated
- Detail pages require portal session cookie (handled automatically)
- Same NIC GeP platform as UP but MP-specific parsers are maintained separately

## Cross-Source Isolation

Tenders are unique per `(tender_source_id, source_tender_id)`. A UP tender and MP tender with the same ID string remain separate records.

## Testing

- Unit: `backend/tests/unit/test_mp_parsers.py`
- Integration: `backend/tests/integration/test_mp_collector.py`
- Fixtures: `backend/tests/fixtures/mp/`

## Module Boundaries

Module 6 does **not** include matching, AI, OCR, recommendations, or Module 7 deduplication.
