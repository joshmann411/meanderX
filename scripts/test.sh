#!/usr/bin/env bash
set -euo pipefail

COMPOSE="${COMPOSE:-docker-compose}"

if [ ! -f .env ]; then
  cp .env.example .env
fi

"${COMPOSE}" build app
"${COMPOSE}" up -d db
"${COMPOSE}" run --rm app ruff check .
"${COMPOSE}" run --rm app pytest -q
