# Tender Document Processing (Module 8)

Module 8 downloads publicly available tender documents, validates them safely, extracts page-level text, and stores metadata for Module 9.

**Module 8 prepares documents for information extraction. It does not determine tender eligibility or company suitability.**

## Architecture

```text
NORMALIZED TENDER
  → document references (from collectors)
  → URL validation / SSRF checks
  → safe download
  → file signature validation
  → checksum + storage
  → text extraction (PDF/TXT/HTML/DOCX)
  → optional OCR fallback
  → page-level text + metadata
```

## Supported File Types

| Type | Support |
|------|---------|
| PDF | Primary target via PyMuPDF |
| TXT | UTF-8 / Latin-1 text |
| HTML | BeautifulSoup text extraction |
| DOCX | python-docx paragraph extraction |

Unsupported or rejected: executables, macro-enabled formats, HTML disguised as PDF.

## Download Safety

- HTTPS/HTTP with timeout, retry, delay, and max size (default 50 MB)
- Streaming download with size cap
- Access-restricted responses (401/403/CAPTCHA-like content) are not bypassed

## SSRF Protection

Document URLs must resolve to public addresses. Blocked targets include localhost, loopback, private IP ranges, and link-local addresses. Domains must match `DOCUMENT_ALLOWED_DOMAINS` (plus source portal domains).

## File Validation

Magic-byte inspection is used instead of trusting filenames or `Content-Type`.

## OCR

Optional Tesseract OCR runs only when direct PDF extraction yields text below `OCR_MIN_TEXT_THRESHOLD`. Controlled by `OCR_ENABLED` and `OCR_LANGUAGES`.

## Local Storage

```
storage/tenders/{tender_id}/documents/{document_id}/document.pdf
storage/tenders/{tender_id}/documents/{document_id}/extracted_text/pages.json
```

Configure with `DOCUMENT_STORAGE_PATH`.

## APIs

| Endpoint | Access |
|----------|--------|
| `GET /api/tender-documents` | Authenticated |
| `GET /api/tenders/{id}/documents` | Authenticated |
| `GET /api/tender-documents/{id}` | Authenticated |
| `POST /api/tender-documents/{id}/process` | Admin |
| `POST /api/tenders/{id}/process-documents` | Admin |
| `GET /api/tender-document-jobs/{id}` | Authenticated |

## Configuration

See `.env.example` for `DOCUMENT_STORAGE_PATH`, `MAX_DOCUMENT_SIZE_MB`, `DOWNLOAD_*`, and `OCR_*` variables.
