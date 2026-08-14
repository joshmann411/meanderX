# Data Sources

## Con Edison ArcGIS

The Con Edison ingestion source is an ArcGIS FeatureServer layer configured by `ARC_GIS_ENDPOINT`.

Endpoint discovery approach:

- Open the public ArcGIS/Experience page in a browser.
- Use Developer Tools Network requests.
- Look for `FeatureServer/.../query` calls.
- Inspect service metadata with `?f=json`.
- Confirm fields, geometry type, spatial reference, maximum record count, and object ID field.

Fields used by the application:

- `FEEDER_ID`: required feeder identifier.
- `PV_THERMAL`: hosting-capacity value.
- `OBJECTID`: ArcGIS object identifier used for pagination duplicate protection when available.
- `SUBSTATION`, `SUBSTATION_ID`, `SUBSTN_ID`, `SUBSTATION_NAME`: optional substation relationship candidates when present.

Pagination:

- Uses ArcGIS `resultOffset` and `resultRecordCount`.
- Uses service `maxRecordCount` when available.
- Uses `returnCountOnly=true` when available.
- Tracks object IDs to avoid repeated-page loops.

Geometry:

- Source geometry may be point, polyline, or polygon-like ArcGIS JSON.
- Application normalizes supported geometry to SRID 4326 EWKT for PostGIS.
- Public APIs return GeoJSON via PostGIS.

Queue limitation:

- The configured hosting-capacity source does not expose enough project queue information to derive reliable queue counts.
- The queue endpoint returns `available: false` with a stable reason instead of inventing data.

## OpenStreetMap

OpenStreetMap substation enrichment uses `power=substation`.

Relevant tags:

- `name`
- `operator`
- `voltage`
- `substation`
- `location`
- `ref`

Extraction strategy:

- Uses a bounded Overpass query over the configured `OSM_BBOX`.
- Fetches nodes, ways, and relations tagged `power=substation`.
- Normalizes OSM ID, geometry, centroid, name, operator, voltage, substation type, and source tags.

## OpenInfraMap

OpenInfraMap is useful for investigation because it visualizes selected infrastructure data from OpenStreetMap. It is not used as the runtime source; the application ingests OpenStreetMap-style records directly.

References:

- https://wiki.openstreetmap.org/wiki/Tag:power%3Dsubstation
- https://wiki.openstreetmap.org/wiki/Key:substation
- https://github.com/openinframap/openinframap

## Known Data Limitations

- Con Edison substation identifiers may not match OSM names exactly.
- OSM operator/name tags can be missing, abbreviated, or inconsistent.
- OSM geometry may be node, way, or relation.
- Feeder geometry proximity is inferential.
- Low-confidence or ambiguous OSM matches are intentionally rejected.
