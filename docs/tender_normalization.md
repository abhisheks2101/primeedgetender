# Tender Normalization and Deduplication (Module 7)

Module 7 converts UP and MP collector output into a consistent internal tender representation and identifies duplicate records conservatively.

## Normalization Pipeline

```text
RAW DATA
  → source validation
  → field normalization
  → date normalization
  → money normalization
  → text normalization
  → location normalization
  → status normalization
  → identity resolution
  → duplicate detection
  → upsert
  → NORMALIZED TENDER
```

Each stage lives in `backend/app/normalization/` as a small, testable module. Collectors remain responsible for parsing source HTML; the shared normalization layer handles common behavior.

## Identity Strategy

Preferred identity hierarchy:

1. `source + source_tender_id` (primary upsert key)
2. `source + official reference number` (fallback identity key only)
3. No title-only identity

Exact duplicates from the same source are prevented by the unique constraint on `(tender_source_id, source_tender_id)`.

## Deduplication

### Exact duplicates

When the same source tender ID is collected again, the existing tender is updated instead of creating a new row.

### Fuzzy duplicates

Fuzzy comparison uses normalized text, reference numbers, organization, estimated value, and submission dates. Results are classified as:

- `EXACT_DUPLICATE`
- `LIKELY_DUPLICATE`
- `POSSIBLE_DUPLICATE`
- `NOT_DUPLICATE`

Cross-source matches are capped at a lower confidence threshold and are never merged automatically.

## Conservative Merge Policy

Uncertain matches are stored as `TenderDuplicateCandidate` records with `PENDING` review status. Administrators review them at `/admin/tender-duplicates`. The system does not auto-merge when confidence is ambiguous.

## Raw Data Preservation

`Tender.raw_payload` stores the original collector payload. Normalized fields are stored separately. Raw records also remain available in `tender_raw_records`.

## Reprocessing

Re-run normalization against stored raw payloads:

```bash
cd backend
python -m app.cli reprocess-normalization
python -m app.cli reprocess-normalization --source-code UP_TENDER --limit 100
```

`normalization_version` on each tender allows future rule changes without forcing immediate full reprocessing.

## Administrative APIs

| Endpoint | Access | Purpose |
|----------|--------|---------|
| `GET /api/tenders` | Authenticated | List normalized tenders |
| `GET /api/tenders/{id}` | Authenticated | Tender detail |
| `GET /api/tender-duplicates` | Admin | List duplicate candidates |
| `GET /api/tender-duplicates/{id}` | Admin | Candidate detail |
| `PATCH /api/tender-duplicates/{id}` | Admin | Review candidate |

## Database Changes

Migration `006_normalization` adds:

- Normalization fields on `tenders`
- `tender_change_history`
- `tender_duplicate_candidates`
- Supporting indexes on state, organization, department, and normalization status
