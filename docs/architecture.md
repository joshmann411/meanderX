# Architecture

```mermaid
flowchart LR
  subgraph source[Con Edison ArcGIS]
    A[ArcGIS FeatureServer]
  end
  Customer[Customer] --> API[FastAPI /api/v1]
  API --> Service[Query Service]
  Service --> Repo[Repository]
  Repo --> F[PostgreSQL + PostGIS]
  A --> B[ArcGIS Client]
  B --> C[Pipeline]
  C --> D[Validation]
  C --> E[Transformation]
  E --> Current[Current State]
  E --> History[Immutable Snapshot History]
  Current --> F
  History --> F
```

The public API exposes stable domain contracts for feeders, substations, geometry, hosting capacity, and queue availability. ArcGIS query syntax and raw source attributes stay inside the ingestion/client layers.

Historical capture is owned by ingestion because the source endpoint overwrites current data. Each successful changed ingestion stores current state and snapshot state transactionally. Identical normalized datasets are recorded as unchanged ingestion attempts without duplicating snapshot rows.
