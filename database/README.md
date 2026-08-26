# Database

This directory contains PostgreSQL initialization scripts and database-related documentation for the Tender Intelligence Platform.

## Structure

- `init/` — SQL scripts executed automatically when the PostgreSQL container starts for the first time.

## Local PostgreSQL

The application expects a PostgreSQL 16 database. Connection settings are controlled through environment variables documented in the root `.env.example`.

## Migrations

Schema migrations are managed with Alembic in `/backend/alembic`.

Run migrations locally:

```bash
cd backend
alembic upgrade head
```

## Notes

- `pgvector` will be enabled in a future module when vector search is required.
- No paid database services are used; PostgreSQL runs locally or in Docker.
