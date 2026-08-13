import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from geoalchemy2 import WKTElement

from app.conedison.client import ConEdisonArcGISClient
from app.conedison.models import ArcGISFeature, ArcGISGeometry
from app.core.database import SessionLocal, engine, ensure_postgis
from app.models import Feeder, FeederSnapshot, IngestionRun, Substation, SubstationSnapshot
from app.pipelines.core import Pipeline

logger = logging.getLogger(__name__)


class ConEdisonPipeline(Pipeline):
    def __init__(self, client: ConEdisonArcGISClient):
        super().__init__("conedison_arcgis")
        self.client = client

    def run(self):
        logger.info("Starting pipeline %s source=%s", self.name, self.client.base_url)
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
                logger.exception("Validation or transformation failed for record")

        logger.info(
            "Validation finished extracted=%s valid=%s rejected=%s",
            len(extracted),
            len(valid),
            rejected,
        )
        self.load(valid, extracted_count=len(extracted), validation_rejected_count=rejected)

    def extract(self) -> Iterable[ArcGISFeature]:
        yield from self.client.query_all()

    def validate(self, record: ArcGISFeature) -> bool:
        attrs = record.attributes
        feeder_id = (getattr(attrs, "FEEDER_ID", None) or "").strip()
        if not feeder_id:
            logger.warning("Record missing usable FEEDER_ID: %s", attrs)
            return False

        pv_thermal = getattr(attrs, "PV_THERMAL", None)
        if pv_thermal is not None and not _is_parseable_pv_thermal(pv_thermal):
            logger.warning("Record has unparseable PV_THERMAL feeder_id=%s value=%s", feeder_id, pv_thermal)
            return False

        if record.geometry and not _geometry_to_ewkt(record.geometry):
            logger.warning("Record has unusable geometry feeder_id=%s", feeder_id)
            return False

        return True

    def transform(self, record: ArcGISFeature) -> Dict[str, Any]:
        attrs = record.attributes
        raw_attributes = attrs.model_dump()
        substation_id = (
            raw_attributes.get("SUBSTATION")
            or raw_attributes.get("SUBSTATION_ID")
            or raw_attributes.get("SUBSTN_ID")
            or raw_attributes.get("SUBSTATION_NAME")
        )

        return {
            "feeder_id": raw_attributes["FEEDER_ID"].strip(),
            "pv_thermal": _normalize_pv_thermal(raw_attributes.get("PV_THERMAL")),
            "geometry_ewkt": _geometry_to_ewkt(record.geometry) if record.geometry else None,
            "source": self.client.base_url,
            "substation_id": str(substation_id).strip() if substation_id else None,
            "substation_name": raw_attributes.get("SUBSTATION_NAME") or raw_attributes.get("SUBSTATION"),
            "raw_attributes": raw_attributes,
        }

    def load(
        self,
        records: List[Dict[str, Any]],
        extracted_count: Optional[int] = None,
        validation_rejected_count: int = 0,
    ):
        extracted = len(records) if extracted_count is None else extracted_count
        started_at = _utcnow()

        with engine.begin() as conn:
            ensure_postgis(conn)

        run_id = self._create_run(started_at)
        if extracted == 0 or not records:
            self._mark_run_failed(
                run_id,
                extracted,
                0,
                0,
                validation_rejected_count,
                "No valid records extracted from source",
            )
            logger.error("Ingestion aborted: no valid records extracted")
            return

        duplicate_rejected = 0
        loaded = 0
        seen = set()
        unique_records = []

        for record in records:
            feeder_id = record["feeder_id"]
            if feeder_id in seen:
                logger.warning("Duplicate feeder in source payload: %s", feeder_id)
                duplicate_rejected += 1
                continue
            seen.add(feeder_id)
            unique_records.append(record)

        dataset_hash = _dataset_hash(unique_records)
        latest_hash = self._latest_dataset_hash()
        if latest_hash == dataset_hash:
            self._mark_run_unchanged(
                run_id,
                extracted,
                len(unique_records),
                validation_rejected_count + duplicate_rejected,
                dataset_hash,
            )
            logger.info("Ingestion run %s unchanged dataset_hash=%s", run_id, dataset_hash)
            return

        try:
            with SessionLocal() as session:
                with session.begin():
                    run = session.get(IngestionRun, run_id)
                    captured_at = started_at
                    substations_for_snapshot = {}
                    for record in unique_records:
                        feeder_id = record["feeder_id"]
                        substation = self._upsert_substation(session, record)
                        if record.get("substation_id"):
                            substations_for_snapshot[record["substation_id"]] = {
                                "name": record.get("substation_name"),
                                "source": record["source"],
                                "source_metadata": {"raw_attributes": record.get("raw_attributes", {})},
                            }
                        feeder = (
                            session.query(Feeder)
                            .filter_by(feeder_id=feeder_id, source=record["source"])
                            .one_or_none()
                        )
                        geometry = _to_wkt_element(record.get("geometry_ewkt"))
                        if feeder is None:
                            feeder = Feeder(
                                feeder_id=feeder_id,
                                pv_thermal=record.get("pv_thermal"),
                                geometry=geometry,
                                source=record["source"],
                                substation=substation,
                                active=True,
                            )
                            session.add(feeder)
                        else:
                            feeder.pv_thermal = record.get("pv_thermal")
                            feeder.geometry = geometry
                            feeder.substation = substation
                            feeder.active = True
                        loaded += 1
                        session.add(
                            FeederSnapshot(
                                ingestion_run_id=run_id,
                                feeder_id=feeder_id,
                                substation_id=record.get("substation_id"),
                                pv_thermal=record.get("pv_thermal"),
                                geometry=_to_wkt_element(record.get("geometry_ewkt")),
                                geometry_hash=_stable_hash(record.get("geometry_ewkt") or ""),
                                source=record["source"],
                                captured_at=captured_at,
                            )
                        )

                    session.query(Feeder).filter(
                        Feeder.source == self.client.base_url,
                        ~Feeder.feeder_id.in_(list(seen)),
                    ).update({"active": False}, synchronize_session=False)

                    for source_substation_id, substation_snapshot in substations_for_snapshot.items():
                        session.add(
                            SubstationSnapshot(
                                ingestion_run_id=run_id,
                                source_substation_id=source_substation_id,
                                name=substation_snapshot.get("name"),
                                geometry=None,
                                source=substation_snapshot.get("source"),
                                captured_at=captured_at,
                                source_metadata=substation_snapshot.get("source_metadata"),
                            )
                        )

                    run.extracted_count = extracted
                    run.valid_count = loaded
                    run.loaded_count = loaded
                    run.rejected_count = validation_rejected_count + duplicate_rejected
                    run.status = "SUCCESS"
                    run.completed_at = _utcnow()
                    run.dataset_hash = dataset_hash
                    run.snapshot_created = True
                    run.metadata_json = {"snapshot_count": loaded}

            logger.info(
                "Ingestion run %s succeeded extracted=%s loaded=%s rejected=%s",
                run_id,
                extracted,
                loaded,
                validation_rejected_count + duplicate_rejected,
            )
        except Exception as exc:
            self._mark_run_failed(
                run_id,
                extracted,
                0,
                0,
                validation_rejected_count + duplicate_rejected,
                str(exc),
            )
            logger.exception("Ingestion failed run_id=%s", run_id)
            raise

    def _create_run(self, started_at: datetime) -> int:
        with SessionLocal() as session:
            run = IngestionRun(
                pipeline=self.name,
                source=self.client.base_url,
                started_at=started_at,
                status="RUNNING",
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            return run.id

    def _mark_run_failed(
        self,
        run_id: int,
        extracted: int,
        valid: int,
        loaded: int,
        rejected: int,
        error: str,
    ) -> None:
        with SessionLocal() as session:
            run = session.get(IngestionRun, run_id)
            if run:
                run.extracted_count = extracted
                run.valid_count = valid
                run.loaded_count = loaded
                run.rejected_count = rejected
                run.status = "FAILED"
                run.error = error
                run.completed_at = _utcnow()
            session.commit()

    def _latest_dataset_hash(self) -> Optional[str]:
        with SessionLocal() as session:
            run = (
                session.query(IngestionRun)
                .filter(
                    IngestionRun.pipeline == self.name,
                    IngestionRun.source == self.client.base_url,
                    IngestionRun.dataset_hash.isnot(None),
                    IngestionRun.status.in_(["SUCCESS", "UNCHANGED"]),
                )
                .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
                .first()
            )
            return run.dataset_hash if run else None

    def _mark_run_unchanged(
        self,
        run_id: int,
        extracted: int,
        valid: int,
        rejected: int,
        dataset_hash: str,
    ) -> None:
        with SessionLocal() as session:
            run = session.get(IngestionRun, run_id)
            if run:
                run.extracted_count = extracted
                run.valid_count = valid
                run.loaded_count = 0
                run.rejected_count = rejected
                run.status = "UNCHANGED"
                run.completed_at = _utcnow()
                run.dataset_hash = dataset_hash
                run.snapshot_created = False
                run.metadata_json = {"reason": "Dataset hash matched latest captured source state."}
            session.commit()

    def _upsert_substation(self, session, record: Dict[str, Any]) -> Optional[Substation]:
        substation_id = record.get("substation_id")
        if not substation_id:
            return None

        substation = (
            session.query(Substation)
            .filter_by(source=record["source"], source_substation_id=substation_id)
            .one_or_none()
        )
        if substation is None:
            substation = Substation(
                source_substation_id=substation_id,
                name=record.get("substation_name"),
                source=record["source"],
                source_metadata={"raw_attributes": record.get("raw_attributes", {})},
            )
            session.add(substation)
            session.flush()
        else:
            substation.name = record.get("substation_name") or substation.name
            substation.source_metadata = {"raw_attributes": record.get("raw_attributes", {})}
        return substation

def _normalize_pv_thermal(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    return str(value)


def _is_parseable_pv_thermal(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return True
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if normalized == "":
        return False
    if normalized.upper() in {"Y", "N", "YES", "NO", "TRUE", "FALSE"}:
        return True
    try:
        float(normalized.replace(",", ""))
        return True
    except ValueError:
        return False


def _geometry_to_ewkt(geometry: ArcGISGeometry) -> Optional[str]:
    if geometry.x is not None and geometry.y is not None:
        return f"SRID=4326;POINT({_coord(geometry.x)} {_coord(geometry.y)})"

    if geometry.paths:
        lines = [_line_wkt(path) for path in geometry.paths]
        lines = [line for line in lines if line]
        if not lines:
            return None
        if len(lines) == 1:
            return f"SRID=4326;LINESTRING{lines[0]}"
        return f"SRID=4326;MULTILINESTRING({','.join(lines)})"

    if geometry.rings:
        rings = [_line_wkt(ring) for ring in geometry.rings]
        rings = [ring for ring in rings if ring]
        if rings:
            return f"SRID=4326;POLYGON({','.join(rings)})"

    return None


def _line_wkt(points: List[List[float]]) -> Optional[str]:
    if len(points) < 2:
        return None
    coords = []
    for point in points:
        if len(point) < 2:
            return None
        coords.append(f"{_coord(point[0])} {_coord(point[1])}")
    return f"({','.join(coords)})"


def _coord(value: float) -> str:
    return f"{float(value):.12g}"


def _to_wkt_element(ewkt: Optional[str]):
    if not ewkt:
        return None
    return WKTElement(ewkt, srid=4326, extended=True)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dataset_hash(records: List[Dict[str, Any]]) -> str:
    normalized = [
        {
            "feeder_id": record.get("feeder_id"),
            "substation_id": record.get("substation_id"),
            "pv_thermal": record.get("pv_thermal"),
            "geometry": record.get("geometry_ewkt"),
        }
        for record in records
    ]
    normalized.sort(key=lambda item: item["feeder_id"] or "")
    return _stable_hash(json.dumps(normalized, sort_keys=True, separators=(",", ":")))


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
