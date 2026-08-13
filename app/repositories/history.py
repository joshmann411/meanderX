from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FeederSnapshot, IngestionRun


@dataclass(frozen=True)
class FeederSnapshotRow:
    snapshot: FeederSnapshot
    geometry_geojson: Optional[str]


class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def feeder_history(
        self,
        feeder_id: str,
        captured_from: Optional[datetime] = None,
        captured_to: Optional[datetime] = None,
    ) -> list[FeederSnapshotRow]:
        query = (
            self.db.query(FeederSnapshot, func.ST_AsGeoJSON(FeederSnapshot.geometry))
            .filter(FeederSnapshot.feeder_id == feeder_id)
            .order_by(FeederSnapshot.captured_at, FeederSnapshot.id)
        )
        if captured_from:
            query = query.filter(FeederSnapshot.captured_at >= captured_from)
        if captured_to:
            query = query.filter(FeederSnapshot.captured_at <= captured_to)
        return [
            FeederSnapshotRow(snapshot=snapshot, geometry_geojson=geometry_geojson)
            for snapshot, geometry_geojson in query.all()
        ]

    def snapshot_runs(self) -> list[IngestionRun]:
        return (
            self.db.query(IngestionRun)
            .filter(IngestionRun.status == "SUCCESS", IngestionRun.snapshot_created.is_(True))
            .order_by(IngestionRun.started_at, IngestionRun.id)
            .all()
        )

    def feeder_snapshot_for_run(self, feeder_id: str, run_id: int) -> Optional[FeederSnapshotRow]:
        row = (
            self.db.query(FeederSnapshot, func.ST_AsGeoJSON(FeederSnapshot.geometry))
            .filter(FeederSnapshot.feeder_id == feeder_id, FeederSnapshot.ingestion_run_id == run_id)
            .first()
        )
        if not row:
            return None
        snapshot, geometry_geojson = row
        return FeederSnapshotRow(snapshot=snapshot, geometry_geojson=geometry_geojson)
