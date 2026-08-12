# Data Sources — ArcGIS FeatureServer Investigation

This document captures findings from inspecting the Con Edison ArcGIS FeatureServer used as the source for feeder/queue data.

Key findings (initial discovery):

- Endpoint: see `.env.example` for configured `ARC_GIS_ENDPOINT`.
- Geometry: features include `geometry` with `x`/`y` and `spatialReference` (commonly EPSG:4326 but verify per-service).
- Fields: service `fields` array describes available attributes. Observed fields include `FEEDER_ID`, `PV_THERMAL`, and `OBJECTID` in sample metadata.
- Object ID: `OBJECTID` is typically the `objectIdFieldName` returned by the service.
- Pagination: ArcGIS FeatureServer supports `resultOffset`/`resultRecordCount` and `where` queries; large services may return `exceededTransferLimit=true` and require paging.
- Max record count: service metadata contains `maxRecordCount`; check `GET ?f=json` metadata to determine value.
- Duplicate feeders / multiplicity: the source may include multiple rows for the same `FEEDER_ID` (e.g., multiple geometry points or parcels). Further analysis required to determine canonical feeder deduplication.
- Queue derivation: there is no explicit `queue_count` field in the observed feed. Deriving queue counts may require joining with other sources or aggregating rows — this could be unsupported by this single FeatureServer endpoint.
- Nullability: fields may be null; fields metadata includes `nullable` flags.

Discovery process: use browser Developer Tools > Network tab to capture FeatureServer `query` calls made by the ArcGIS web app. The web app often issues `FeatureServer/0/query` requests with `where`, `outFields`, and `f=json` parameters.
