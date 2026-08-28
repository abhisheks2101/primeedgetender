#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# Load environment defaults
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source <(python3 - <<'PY'
from pathlib import Path

for line in Path(".env").read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    print(f"export {key}={value!r}")
PY
)
fi

POSTGRES_USER="${POSTGRES_USER:-tender_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-change_me_in_production}"
POSTGRES_DB="${POSTGRES_DB:-tender_intelligence}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

start_postgres() {
  if pg_isready -h localhost -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
    echo "PostgreSQL is already running."
    return 0
  fi

  echo "Starting PostgreSQL..."
  sudo pg_ctlcluster 16 main start || sudo service postgresql start

  for _ in $(seq 1 30); do
    if pg_isready -h localhost -p "$POSTGRES_PORT" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if ! pg_isready -h localhost -p "$POSTGRES_PORT" >/dev/null 2>&1; then
    echo "PostgreSQL failed to start."
    sudo tail -n 50 /var/log/postgresql/postgresql-16-main.log 2>/dev/null || true
    exit 1
  fi
}

ensure_database() {
  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1; then
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"
  fi

  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1; then
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"
  fi

  sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$POSTGRES_DB" -f "$REPO_ROOT/database/init/01-init.sql"
}

run_migrations() {
  # shellcheck disable=SC1091
  source "$REPO_ROOT/backend/.venv/bin/activate"
  cd "$REPO_ROOT/backend"
  alembic upgrade head
}

start_postgres
ensure_database
run_migrations

echo "PostgreSQL and database migrations are ready."
