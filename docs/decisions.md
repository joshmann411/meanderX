# Design Decisions

- Language: Python 3.12 — productivity, typing, ecosystem compatibility.
- Framework: FastAPI — lightweight async web framework with excellent developer UX.
- DB: PostgreSQL + PostGIS — spatial storage and queries for geometry data.
- Separation: External source models (ArcGIS) are modeled separately from internal domain models to avoid leaking external schema and to allow migration and validation layers.
