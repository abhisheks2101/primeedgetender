# Tests

This directory contains cross-service integration tests for the Tender Intelligence Platform.

## Layout

```text
tests/
├── conftest.py
└── integration/
    ├── test_health_api.py
    └── test_database_connectivity.py
```

Backend unit tests live in `backend/tests/`.

Frontend tests live alongside components in `frontend/src/`.

## Running Tests

Integration tests require a running PostgreSQL instance configured through environment variables.

```bash
# From repository root
cp .env.example .env

# Backend unit + integration tests
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest

# Frontend tests
cd ../frontend
npm test
```

If PostgreSQL is unavailable, integration tests are skipped automatically.

## Markers

Integration tests use `@pytest.mark.integration`.
