#!/usr/bin/env bash
set -euo pipefail

COMPOSE="${COMPOSE:-docker-compose}"
APP_MODE="${APP_MODE:-demo}"

echo "Con Edison Hosting Capacity Platform"
echo

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required but was not found on PATH."
  exit 1
fi

if ! command -v "${COMPOSE}" >/dev/null 2>&1; then
  echo "${COMPOSE} is required but was not found on PATH."
  exit 1
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Mode: ${APP_MODE}"
echo "Building Docker image..."
"${COMPOSE}" build app

echo "Starting PostgreSQL/PostGIS..."
"${COMPOSE}" up -d db

echo "Waiting for database readiness..."
for attempt in $(seq 1 30); do
  if "${COMPOSE}" exec -T db pg_isready -U postgres -d meanderx >/dev/null 2>&1; then
    echo "Database: ready"
    break
  fi
  if [ "${attempt}" = "30" ]; then
    echo "Database did not become ready in time."
    exit 1
  fi
  sleep 2
done

echo "Applying migrations..."
"${COMPOSE}" run --rm app alembic -c migrations/alembic.ini upgrade head
echo "Migrations: complete"

if [ "${APP_MODE}" = "demo" ]; then
  echo "Seeding deterministic demo data..."
  "${COMPOSE}" run --rm app python -m app.cli demo seed
  echo "Demo ingestion: complete"
elif [ "${APP_MODE}" = "live" ]; then
  echo "Running live Con Edison ingestion..."
  "${COMPOSE}" run --rm app python -m app.cli ingest conedison
  echo "Con Edison ingestion: complete"
  echo "Running live OSM enrichment..."
  if "${COMPOSE}" run --rm app python -m app.cli ingest osm; then
    echo "OSM ingestion: complete"
    echo "Substation matching: complete"
  else
    echo "OSM ingestion: unavailable; core Con Edison API remains available."
  fi
else
  echo "Unknown APP_MODE '${APP_MODE}'. Use APP_MODE=demo or APP_MODE=live."
  exit 1
fi

echo "Starting FastAPI..."
"${COMPOSE}" up -d app

echo
echo "API: http://localhost:8000"
echo "Swagger: http://localhost:8000/docs"
echo
echo "Demo examples:"
echo "  curl http://localhost:8000/api/v1/feeders/DEMO-F1"
echo "  curl http://localhost:8000/api/v1/substations/DEMO-SUB-A"
echo "  curl http://localhost:8000/api/v1/feeders/DEMO-F1/history"
echo "  curl http://localhost:8000/api/v1/feeders/DEMO-F1/changes"
