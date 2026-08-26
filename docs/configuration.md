# Configuration Guide

All secrets and environment-specific values are supplied through environment variables. Never commit real credentials.

## Environment Files

| File | Purpose |
|------|---------|
| `.env.example` | Template with safe defaults for local development |
| `.env` | Local development values (gitignored) |
| `.env.production` | Production values (gitignored, used by `docker-compose.prod.yml`) |

Copy the example file before starting:

```bash
cp .env.example .env
```

## Core Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Application display name | `Tender Intelligence Platform` |
| `APP_ENV` | Runtime environment | `development` |
| `APP_DEBUG` | Enables API docs and debug behavior | `true` |
| `APP_VERSION` | Application version string | `0.1.0` |
| `BACKEND_HOST` | Backend bind host | `0.0.0.0` |
| `BACKEND_PORT` | Backend port | `8000` |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:3000` |
| `POSTGRES_USER` | PostgreSQL username | `tender_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | change in production |
| `POSTGRES_DB` | PostgreSQL database name | `tender_intelligence` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` or `postgres` in Docker |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `DATABASE_URL` | SQLAlchemy connection URL | `postgresql+psycopg://...` |
| `NEXT_PUBLIC_API_URL` | Backend URL used by the frontend | `http://localhost:8000` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

## Docker Notes

### Development (`docker-compose.yml`)

Inside Docker Compose, services communicate over the internal network:

- Backend should use `POSTGRES_HOST=postgres`
- Frontend server-side requests should use `NEXT_PUBLIC_API_URL=http://backend:8000`

When accessing the app from your browser on the host machine, the backend is still exposed at `http://localhost:8000`.

### Production (`docker-compose.prod.yml`)

Production compose expects:

- `.env.production` with strong credentials
- `APP_DEBUG=false`
- production Dockerfiles with multi-stage builds

## Security Rules

- Do not hardcode secrets in source code.
- Do not commit `.env` or `.env.production`.
- Replace all example passwords before any shared deployment.

## Future Configuration

Later modules will add configuration for:

- Ollama model selection
- OCR/Tesseract paths
- n8n webhook URLs
- Background worker settings

These are intentionally absent from Module 1.
