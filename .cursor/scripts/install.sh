#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

mkdir -p storage/uploads

if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
fi

# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install --disable-pip-version-check -q -r backend/requirements-dev.txt

cd frontend
npm ci --no-audit --no-fund
