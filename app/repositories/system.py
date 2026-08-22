from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Feeder, FeederSnapshot, IngestionRun, OsmSubstation, Substation, SubstationOsmMatch, SubstationSnapshot


@dataclass(frozen=True)
class SystemCountsRow:
    feeders: int
    active_feeders: int
    substations: int
    feeder_snapshots: int
    substation_snapshots: int
    osm_substations: int
    accepted_osm_matches: int


class SystemRepository:
    def __init__(self, db: Session):
        self.db = db

    def counts(self) -> SystemCountsRow:
        return SystemCountsRow(
            feeders=self.db.query(func.count(Feeder.id)).scalar() or 0,
            active_feeders=self.db.query(func.count(Feeder.id)).filter(Feeder.active.is_(True)).scalar() or 0,
            substations=self.db.query(func.count(Substation.id)).scalar() or 0,
            feeder_snapshots=self.db.query(func.count(FeederSnapshot.id)).scalar() or 0,
            substation_snapshots=self.db.query(func.count(SubstationSnapshot.id)).scalar() or 0,
            osm_substations=self.db.query(func.count(OsmSubstation.id)).scalar() or 0,
            accepted_osm_matches=(
                self.db.query(func.count(SubstationOsmMatch.id)).filter(SubstationOsmMatch.accepted.is_(True)).scalar() or 0
            ),
        )

    def latest_ingestions(self, limit: int = 6) -> list[IngestionRun]:
        return self.db.query(IngestionRun).order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc()).limit(limit).all()
