#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  # Enable public registration for local development and Playwright e2e flows.
  sed -i 's/^ALLOW_PUBLIC_REGISTRATION=false/ALLOW_PUBLIC_REGISTRATION=true/' .env
fi

# Backend dependencies
if [[ ! -d backend/.venv ]]; then
  python3 -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements-dev.txt

# Frontend dependencies
cd frontend
npm ci
npx playwright install chromium
cd "$REPO_ROOT"
