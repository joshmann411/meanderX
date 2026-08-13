# Design Decisions

- Language: Python 3.12 — productivity, typing, ecosystem compatibility.
- Framework: FastAPI — lightweight async web framework with excellent developer UX.
- DB: PostgreSQL + PostGIS — spatial storage and queries for geometry data.
- Separation: External source models (ArcGIS) are modeled separately from internal domain models to avoid leaking external schema and to allow migration and validation layers.

Additional Phase 2 decisions:

- Pipeline abstraction: a small `extract/validate/transform/load` pipeline keeps source logic isolated and testable without building a heavyweight ETL framework.
- Transactional loading: ingestion persists data inside a DB transaction and records an `ingestion_runs` entry to allow safe rollbacks and auditing.
- Missing/deleted records: current approach marks missing feeders as `active=false` rather than deleting, preserving historical context and avoiding accidental data loss.

Additional Phase 3 decisions:

- REST API rather than UI: the assessment can be demonstrated through Swagger and curl while keeping the implementation focused on stable data access.
- Domain-oriented contracts: customer responses use feeder, substation, hosting-capacity, geometry, and source metadata concepts instead of database rows or ArcGIS payloads.
- ArcGIS structures are hidden: raw source attributes are persisted for traceability but are not returned by public endpoints, allowing source schema changes without breaking customers.
- Queue-data limitations: the current hosting-capacity source does not expose sufficient project queue data, so the API returns a stable unavailable response instead of fabricating counts.

Additional Phase 4 decisions:

- Immutable snapshots: feeder and substation snapshots are append-only records tied to ingestion runs so customers can audit how values changed over time.
- Separate current and historical state: current tables stay optimized for customer lookup while snapshot tables preserve past captured states without being overwritten by repeat ingestion.
- Dataset hash strategy: SHA-256 is calculated from normalized domain values ordered by feeder ID, including feeder ID, source substation ID, PV_THERMAL, and normalized geometry EWKT. Raw source ordering is intentionally ignored.
- Unchanged datasets: when a new ingestion hash matches the latest captured dataset hash, the run is marked `UNCHANGED`; no duplicate snapshot rows are written.
- ArcGIS history limitation: historical change tracking cannot be delegated to the upstream FeatureServer because the configured hosting-capacity source exposes the current state, not immutable prior versions.
