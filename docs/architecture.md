# Tender Intelligence Platform — Architecture (Module 1)

## Overview

The Tender Intelligence Platform is a local-first, modular web application for discovering government tenders, analyzing documents, and evaluating company eligibility using open-source tooling only.

Module 1 establishes the foundation. Business features are intentionally deferred to later modules.

## High-Level Architecture

```text
┌─────────────┐      HTTP       ┌─────────────┐      SQL        ┌─────────────┐
│   Next.js   │ ──────────────► │   FastAPI   │ ──────────────► │ PostgreSQL  │
│  Frontend   │   /api/health   │   Backend   │                 │  Database   │
└─────────────┘                 └─────────────┘                 └─────────────┘
```

Future modules will extend this stack without replacing it:

```text
FastAPI ──► Ollama ──► Local open-source LLM
FastAPI ──► PyMuPDF / Tesseract ──► Document processing
PostgreSQL ──► pgvector (future semantic search)
```

## Repository Layout

```text
/
├── frontend/          Next.js + TypeScript + Tailwind + shadcn/ui
├── backend/           FastAPI + SQLAlchemy + Alembic
├── database/          PostgreSQL init scripts and database docs
├── docs/              Project documentation
├── tests/             Cross-service integration tests
├── docker-compose.yml Development stack
└── docker-compose.prod.yml Production-oriented stack
```

## Backend Structure

```text
backend/app/
├── api/routes/        REST endpoints
├── core/              Database engine and shared infrastructure
├── models/            SQLAlchemy models (future modules)
├── config.py          Environment-driven settings
├── logging_config.py  Structured logging setup
└── main.py            Application factory and lifespan hooks
```

Design principles:

- Configuration is loaded exclusively from environment variables.
- Database access is centralized in `core/database.py`.
- API routes remain thin; business logic will be added in later modules.
- Alembic manages schema migrations.

## Frontend Structure

```text
frontend/src/
├── app/               Next.js App Router pages
├── components/        UI components including shadcn/ui primitives
└── lib/               API helpers and shared utilities
```

The landing page displays live backend and database status by calling `GET /api/health`.

## Health Endpoint

`GET /api/health` returns:

- overall application status
- application name and version
- environment name
- database connectivity status and latency

Status values:

- `healthy` — backend and database are reachable
- `degraded` — reserved for partial failures in future modules
- `unhealthy` — database unreachable

## Cost Constraint

Module 1 uses only free/open-source components:

- Next.js, FastAPI, PostgreSQL, Docker
- No paid APIs, cloud AI services, or hosted SaaS dependencies

## Future Module Boundaries

Not implemented in Module 1:

- Authentication and users (M02)
- Company profiles (M03)
- Tender collectors (M04–M07)
- Document intelligence (M08–M09)
- AI matching and rules engine (M10–M12)
- Dashboard, alerts, admin (M13–M15)

Minimal contracts may be introduced early when required for clean architecture, but no business functionality is implemented ahead of schedule.
