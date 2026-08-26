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
| Testing | Pytest, Jest, Testing Library |

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

## Running Tests

### Backend unit and integration tests

```bash
cd backend
source .venv/bin/activate
pytest
```

Integration tests require PostgreSQL. If it is unavailable, database-related tests are skipped.

### Frontend tests

```bash
cd frontend
npm test
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

### Not Implemented (future modules)

- Authentication and users (M02)
- Company profiles and documents (M03)
- Tender source management and collectors (M04–M07)
- Document processing and extraction (M08–M09)
- Eligibility rules and AI matching (M10–M12)
- Dashboard search, alerts, admin (M13–M15)

## License

Add project license before public distribution.
