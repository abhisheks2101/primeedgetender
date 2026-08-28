#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

read_env() {
  local key="$1"
  local default="${2:-}"
  local value
  value="$(grep -E "^${key}=" .env | tail -n1 | cut -d= -f2- || true)"
  if [[ -z "$value" ]]; then
    printf '%s' "$default"
  else
    printf '%s' "$value"
  fi
}

POSTGRES_USER="$(read_env POSTGRES_USER tender_user)"
POSTGRES_PASSWORD="$(read_env POSTGRES_PASSWORD change_me_in_production)"
POSTGRES_DB="$(read_env POSTGRES_DB tender_intelligence)"

sudo service postgresql start

for _ in $(seq 1 30); do
  if sudo -u postgres pg_isready -q; then
    break
  fi
  sleep 1
done

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"

# shellcheck disable=SC1091
source backend/.venv/bin/activate
cd backend
alembic upgrade head

python -m app.cli create-admin \
  --email admin@example.com \
  --full-name "Admin User" \
  --password "Password123!" >/dev/null 2>&1 || true
