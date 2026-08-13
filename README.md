# MeanderX

Python/FastAPI service for ingesting Con Edison ArcGIS feeder data into PostgreSQL/PostGIS.

## Current Status

- Phase 1 foundation is in place: FastAPI app, environment config, ArcGIS source models/client, Alembic, PostgreSQL/PostGIS, and offline tests.
- Phase 2 ingestion path is in place: extract, validate, transform, load, domain tables, ingestion run tracking, feeder/substation persistence, and repeat-ingestion upserts.
- Phase 3 customer query API is in place: feeder lookup/search, substation lookup, substation feeders, queue limitation response, Swagger/OpenAPI docs, and API tests.
- Phase 4 historical snapshots are in place: immutable feeder/substation snapshots, deterministic dataset hashes, unchanged dataset handling, and history/change APIs.
- Live ingestion requires a real Con Edison ArcGIS FeatureServer layer URL in `.env`.

## Local Setup

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set `ARC_GIS_ENDPOINT` to the real FeatureServer layer URL. The checked-in value is a placeholder.

Keep the database URL using the Psycopg 3 SQLAlchemy driver:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/meanderx
```

## Start And Run Locally

Build the application image:

```powershell
docker-compose build app
```

Start PostgreSQL/PostGIS:

```powershell
docker-compose up -d db
```

Run migrations:

```powershell
docker-compose run --rm app alembic -c migrations/alembic.ini upgrade head
```

Run tests:

```powershell
docker-compose run --rm app pytest -q
```

Start the API:

```powershell
docker-compose up -d app
```

Check health:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

Expected response includes:

```json
{"status":"healthy","env":"development"}
```

## Run Ingestion

After migrations are applied and `ARC_GIS_ENDPOINT` points to the real source:

```powershell
docker-compose run --rm app python -m app.cli ingest conedison
```

The pipeline retrieves ArcGIS pages, validates feeder records, transforms geometry to SRID 4326 EWKT for PostGIS, upserts current feeders/substations, marks missing feeders inactive, and records the ingestion run.

Successful changed ingestions also create immutable snapshot rows. If the normalized dataset hash matches the latest captured dataset, the ingestion run is marked `UNCHANGED` and duplicate snapshot rows are skipped.

## Phase 1 Customer API Usage

Swagger/OpenAPI docs are available after startup:

```text
http://localhost:8000/docs
```

Search feeders:

```powershell
curl "http://localhost:8000/api/v1/feeders?feederId=ABC&limit=20&offset=0"
```

Get a feeder:

```powershell
curl "http://localhost:8000/api/v1/feeders/ABC123"
```

Get a substation:

```powershell
curl "http://localhost:8000/api/v1/substations/SUB001"
```

List feeders connected to a substation:

```powershell
curl "http://localhost:8000/api/v1/substations/SUB001/feeders?limit=50&offset=0"
```

Get feeder queue information:

```powershell
curl "http://localhost:8000/api/v1/feeders/ABC123/queue"
```

Queue response note: the current hosting-capacity source does not expose enough project queue data to derive a reliable project count. The API returns `available: false` and a stable explanatory reason instead of inventing a value.

Get feeder history:

```powershell
curl "http://localhost:8000/api/v1/feeders/ABC123/history"
```

Optionally filter by capture time:

```powershell
curl "http://localhost:8000/api/v1/feeders/ABC123/history?capturedFrom=2026-01-01T00:00:00Z"
```

Get feeder changes:

```powershell
curl "http://localhost:8000/api/v1/feeders/ABC123/changes"
```

Change events include `added`, `removed`, `modified`, and `unchanged` where the available snapshots support those comparisons.

## Historical Data

The upstream ArcGIS source represents the latest known state and does not preserve every previous version for this application. MeanderX captures history at ingestion time:

- `feeders` and `substations` hold the current query state.
- `feeder_snapshots` and `substation_snapshots` hold immutable historical state per successful changed ingestion run.
- `ingestion_runs.dataset_hash` stores a SHA-256 hash of normalized domain values sorted by feeder ID, so source ordering does not create false changes.
- Failed ingestions do not create snapshots.
- Unchanged ingestions are recorded as attempts with status `UNCHANGED` but do not duplicate snapshot rows.

## Useful Commands

View running containers:

```powershell
docker-compose ps
```

View app logs:

```powershell
docker-compose logs -f app
```

Stop services:

```powershell
docker-compose down
```

Reset the local database volume if you need a clean database:

```powershell
docker-compose down -v
docker-compose up -d db
docker-compose run --rm app alembic -c migrations/alembic.ini upgrade head
```

## Source Notes

See [docs/data-sources.md](docs/data-sources.md) for ArcGIS source findings and limitations. Queue information is not currently derived unless it exists in the configured source layer.
