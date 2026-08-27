# Tender Intelligence Platform

Production-quality, local-first web application for discovering government tenders from Uttar Pradesh and Madhya Pradesh, analyzing tender documents, and evaluating company eligibility.

**Module 1 — Project Foundation** provides the application skeleton, health monitoring, Docker support, and testing infrastructure. Authentication, tender collection, AI matching, and notifications are intentionally deferred to later modules.

## Cost Principle

This project uses **₹0 paid services**. All components are open-source and run locally:

- Next.js, FastAPI, PostgreSQL, Docker
- Future AI via self-hosted Ollama
- No paid LLM, OCR, vector, email, SMS, or hosting dependencies

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 16 |
| Infrastructure | Docker, Docker Compose |
| Testing | Pytest, Playwright, Jest, Testing Library |

## Prerequisites

- Node.js 22+
- Python 3.12+
- PostgreSQL 16+ (local install or Docker)
- Docker & Docker Compose (recommended)
- Git

## Project Structure

```text
/
├── frontend/                 Next.js application
├── backend/                  FastAPI application
├── database/                 PostgreSQL init scripts
├── docs/                     Architecture and configuration docs
├── tests/                    Integration tests
├── docker-compose.yml        Development stack
├── docker-compose.prod.yml   Production stack structure
└── .env.example              Environment template
```

## Environment Setup

1. Clone the repository.
2. Copy the environment template:

```bash
cp .env.example .env
```

3. Update `.env` with your local values. Do not commit secrets.

See [docs/configuration.md](docs/configuration.md) for all variables.

## Running Locally

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

Services:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Health API: http://localhost:8000/api/health
- PostgreSQL: localhost:5432

### Option B — Manual local development

#### 1. Start PostgreSQL

Ensure PostgreSQL is running and create the database/user matching `.env`.

#### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 to view the landing page and system status.

## Authentication

Module 2 adds local authentication with secure HTTP-only session cookies.

### Roles

| Role | Description |
|------|-------------|
| `ADMIN` | Full administrative access |
| `USER` | Standard authenticated access |

Public registration is disabled by default and can only create `USER` accounts when explicitly enabled. There is no public path to create an `ADMIN`.

### First admin creation

Create the initial administrator with the management CLI:

```bash
cd backend
source .venv/bin/activate
python -m app.cli create-admin
```

The command prompts for email, full name, and password securely. It prevents creating a second administrator accidentally.

### Login and logout

- Login page: http://localhost:3000/login
- Protected shell: http://localhost:3000/app
- Login API: `POST /api/auth/login`
- Logout API: `POST /api/auth/logout`
- Current user API: `GET /api/auth/me`

Authentication uses an HTTP-only session cookie (`tip_session`). The frontend sends authenticated requests through same-origin `/api/*` proxy rewrites with `credentials: "include"`.

### Development authentication configuration

Set these values in `.env`:

- `AUTH_SECRET` — long random secret used by the application environment (required)
- `FRONTEND_URL` — browser origin allowed for CORS/cookies
- `ALLOW_PUBLIC_REGISTRATION=false` — keep disabled unless you intentionally want open USER registration
- `COOKIE_SECURE=false` — required for local HTTP development
- `COOKIE_SAMESITE=lax` — appropriate for local development

For production, use `.env.production` with `APP_ENV=production`, `COOKIE_SECURE=true`, and strong secrets.

## Running Tests

### Backend unit and integration tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Integration tests require PostgreSQL. If it is unavailable, database-related tests are skipped.

### Frontend unit tests

```bash
cd frontend
npm test
```

### End-to-end tests (Playwright)

Playwright expects PostgreSQL, backend migrations, and the backend virtual environment to be available.

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

## Docker Commands

```bash
# Start development stack
docker compose up --build

# Stop stack
docker compose down

# Stop and remove volumes
docker compose down -v

# Production-oriented stack
docker compose -f docker-compose.prod.yml up --build
```

Production compose expects `.env.production` with secure credentials.

## API

### `GET /api/health`

Returns application and database health information.

Example response:

```json
{
  "status": "healthy",
  "application": "Tender Intelligence Platform",
  "version": "0.1.0",
  "environment": "development",
  "database": {
    "status": "connected",
    "latency_ms": 4.21
  }
}
```

When `APP_DEBUG=true`, OpenAPI docs are available at `/api/docs`.

### Authentication APIs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/register` | Create a USER account when public registration is enabled |
| `POST` | `/api/auth/login` | Authenticate and establish a session cookie |
| `POST` | `/api/auth/logout` | Invalidate the current session |
| `GET` | `/api/auth/me` | Return the current authenticated user |
| `GET` | `/api/auth/session-check` | Authenticated endpoint for USER and ADMIN |
| `GET` | `/api/admin/status` | Admin-only authorization check |

## Architecture

See [docs/architecture.md](docs/architecture.md) for module boundaries, directory layout, and future extension points.

## Module Status

### Implemented (Module 1)

- Monorepo foundation with frontend, backend, database, docs, and tests
- FastAPI application with structured logging and environment config
- PostgreSQL connection via SQLAlchemy
- Alembic migration scaffold
- Health endpoint
- Next.js landing/dashboard shell with backend/database status
- Docker Compose for development and production structure
- Automated tests and documentation

### Implemented (Module 2)

- User model with secure password hashing (bcrypt)
- Roles: `ADMIN`, `USER`
- Database-backed session authentication with HTTP-only cookies
- Login, logout, current-user, and restricted registration APIs
- Reusable authorization dependencies for authenticated users and admins
- Admin creation CLI (`python -m app.cli create-admin`)
- Login page (`/login`) and protected shell (`/app`)
- PostgreSQL-backed login rate limiting
- Pytest and Playwright test coverage

### Implemented (Module 3)

- Multi-company profile system (Company A / Company B / …)
- Structured registrations, contractor registrations, financial history
- Normalized capability categories and company capability assignments
- Project/work experience with structured categories
- Machinery, personnel, and geographic operating locations
- Generic company document upload with local filesystem storage abstraction
- Company management UI under `/app/companies`
- Admin write access and authenticated user read access
- Optional demo seed CLI (`python -m app.cli seed-companies`)
- See [docs/companies.md](docs/companies.md)

### Implemented (Module 4)

- Generic tender source architecture with adapter pattern
- `TenderSource`, `TenderCollectionJob`, `TenderCollectionEvent`, and raw record storage
- Extensible source types and collection methods
- Validated source configuration (URLs, timeouts, retry, request politeness)
- Async `TenderCollector` interface with UP/MP placeholders and mock collector
- Retry framework for temporary failures
- Source management and collection job history APIs
- Admin UI under `/admin/tender-sources`
- Fictional seed sources (`TEST_SOURCE_A`, `TEST_SOURCE_B`)
- See [docs/tender_sources.md](docs/tender_sources.md)

**Note:** Actual UP and MP tender collection is **not** implemented in Module 4.

### Not Implemented (future modules)

- UP tender collector (M05)
- MP tender collector (M06)
- Tender deduplication and normalized tender pipeline (M07)
- Document processing and extraction (M08–M09)
- Eligibility rules and AI matching (M10–M12)
- Dashboard search, alerts, admin (M13–M15)

## License

Add project license before public distribution.
