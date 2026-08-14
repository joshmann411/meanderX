import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from geoalchemy2 import WKTElement

from app.core.database import SessionLocal, engine, ensure_postgis
from app.models import IngestionRun, OsmSubstation
from app.pipelines.core import Pipeline
from app.pipelines.osm.client import OsmOverpassClient
from app.pipelines.osm.models import OsmSubstationRecord
from app.services.osm_matching import SubstationMatcher

logger = logging.getLogger(__name__)


class OsmSubstationPipeline(Pipeline):
    def __init__(self, client: OsmOverpassClient):
        super().__init__("osm_substations")
        self.client = client

    def run(self):
        logger.info("Starting pipeline %s", self.name)
        extracted = list(self.extract())
        valid = []
        rejected = 0
        for record in extracted:
            try:
                if self.validate(record):
                    valid.append(self.transform(record))
                else:
                    rejected += 1
            except Exception:
                rejected += 1
                logger.exception("OSM validation or transformation failed")
        self.load(valid, extracted_count=len(extracted), rejected_count=rejected)
        logger.info("OSM extraction finished extracted=%s valid=%s rejected=%s", len(extracted), len(valid), rejected)

    def extract(self) -> Iterable[dict[str, Any]]:
        return self.client.query_substations().get("elements", [])

    def validate(self, record: dict[str, Any]) -> bool:
        tags = record.get("tags") or {}
        return tags.get("power") == "substation"

    def transform(self, record: dict[str, Any]) -> OsmSubstationRecord:
        tags = record.get("tags") or {}
        geometry = _geometry_to_ewkt(record)
        if not geometry:
            raise ValueError(f"OSM substation {record.get('id')} has no usable geometry")
        centroid = _centroid_to_ewkt(record)
        return OsmSubstationRecord(
            osm_id=f"{record.get('type')}/{record.get('id')}",
            name=tags.get("name"),
            operator=tags.get("operator"),
            voltage=tags.get("voltage"),
            substation_type=tags.get("substation"),
            geometry_ewkt=geometry,
            centroid_ewkt=centroid,
            source_tags=tags,
        )

    def load(self, records: list[OsmSubstationRecord], extracted_count: Optional[int] = None, rejected_count: int = 0):
        started_at = _utcnow()
        with engine.begin() as conn:
            ensure_postgis(conn)

        with SessionLocal() as session:
            run = IngestionRun(
                pipeline=self.name,
                source="osm",
                started_at=started_at,
                status="RUNNING",
                extracted_count=len(records) if extracted_count is None else extracted_count,
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            run_id = run.id

        try:
            with SessionLocal() as session:
                with session.begin():
                    run = session.get(IngestionRun, run_id)
                    loaded = 0
                    for record in records:
                        osm_substation = session.query(OsmSubstation).filter_by(osm_id=record.osm_id).one_or_none()
                        if osm_substation is None:
                            osm_substation = OsmSubstation(osm_id=record.osm_id)
                            session.add(osm_substation)
                        osm_substation.name = record.name
                        osm_substation.operator = record.operator
                        osm_substation.voltage = record.voltage
                        osm_substation.substation_type = record.substation_type
                        osm_substation.geometry = _to_wkt(record.geometry_ewkt)
                        osm_substation.centroid = _to_wkt(record.centroid_ewkt)
                        osm_substation.source_tags = record.source_tags
                        osm_substation.source = "osm"
                        loaded += 1

                    session.flush()
                    matcher = SubstationMatcher(session)
                    summary = matcher.match_all(run_id=run_id)

                    run.status = "SUCCESS"
                    run.valid_count = loaded
                    run.loaded_count = loaded
                    run.rejected_count = rejected_count
                    run.completed_at = _utcnow()
                    run.metadata_json = {"match_summary": summary}

            logger.info("OSM ingestion completed loaded=%s matches=%s", loaded, summary)
        except Exception as exc:
            with SessionLocal() as session:
                run = session.get(IngestionRun, run_id)
                if run:
                    run.status = "FAILED"
                    run.error = str(exc)
                    run.completed_at = _utcnow()
                session.commit()
            raise


def _geometry_to_ewkt(record: dict[str, Any]) -> Optional[str]:
    if record.get("type") == "node" and "lat" in record and "lon" in record:
        return f"SRID=4326;POINT({_coord(record['lon'])} {_coord(record['lat'])})"

    coords = _record_coords(record)
    if len(coords) < 2:
        return None
    if coords[0] == coords[-1] and len(coords) >= 4:
        return f"SRID=4326;POLYGON(({','.join(coords)}))"
    return f"SRID=4326;LINESTRING({','.join(coords)})"


def _centroid_to_ewkt(record: dict[str, Any]) -> str:
    if record.get("type") == "node" and "lat" in record and "lon" in record:
        return f"SRID=4326;POINT({_coord(record['lon'])} {_coord(record['lat'])})"

    points = []
    for point in record.get("geometry") or []:
        if "lat" in point and "lon" in point:
            points.append((float(point["lon"]), float(point["lat"])))
    if not points:
        raise ValueError("Cannot calculate OSM centroid without coordinates")
    lon = sum(point[0] for point in points) / len(points)
    lat = sum(point[1] for point in points) / len(points)
    return f"SRID=4326;POINT({_coord(lon)} {_coord(lat)})"


def _record_coords(record: dict[str, Any]) -> list[str]:
    coords = []
    for point in record.get("geometry") or []:
        if "lat" in point and "lon" in point:
            coords.append(f"{_coord(point['lon'])} {_coord(point['lat'])}")
    return coords


def _coord(value: Any) -> str:
    return f"{float(value):.12g}"


def _to_wkt(ewkt: str):
    return WKTElement(ewkt, srid=4326, extended=True)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
