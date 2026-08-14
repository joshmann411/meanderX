# Design Decisions

- Python: good productivity, testing support, and geospatial/data ecosystem fit.
- FastAPI: exposes clean REST contracts and Swagger without building a frontend.
- PostgreSQL/PostGIS: stores current and historical geometry with spatial indexes.
- Pipeline architecture: lightweight `extract/validate/transform/load` flow keeps source logic pluggable without creating a large ETL framework.
- Ingestion instead of proxying ArcGIS: customer APIs stay stable and history can be preserved locally even when the source overwrites current data.
- Transactional ingestion: current state and snapshots are written consistently; failed runs do not expose partial data.
- Immutable history: append-only snapshots preserve source states for customer-visible change analysis.
- Dataset hashing: normalized domain records are ordered by feeder ID and hashed with SHA-256 so source ordering does not create false changes.
- Source provenance: OSM matches and geometry enrichment include source IDs, confidence, method, and distance when available.
- OSM enrichment: OpenStreetMap is treated as an independent geometry enrichment source, separate from Con Edison identity and hosting-capacity data.
- Confidence-based matching: uncertain or ambiguous Con Edison-to-OSM matches remain unresolved rather than fabricating certainty.
- REST/Swagger instead of frontend: reviewers can demonstrate the complete assessment directly through API docs and curl.
- Demo mode: deterministic fixtures make the system reviewable without external API availability.
- One-command Docker execution: `./run.sh` validates tooling, starts services, migrates, seeds or ingests data, and prints reviewer URLs.
