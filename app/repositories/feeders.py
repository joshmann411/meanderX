from dataclasses import dataclass
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Feeder, OsmSubstation, Substation, SubstationOsmMatch


@dataclass(frozen=True)
class FeederRow:
    feeder: Feeder
    substation: Optional[Substation]
    geometry_geojson: Optional[str]


@dataclass(frozen=True)
class SubstationRow:
    substation: Substation
    geometry_geojson: Optional[str]
    osm_geometry_geojson: Optional[str]
    osm_substation: Optional[OsmSubstation]
    osm_match: Optional[SubstationOsmMatch]
    feeder_count: int


class FeederRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_feeder(self, feeder_id: str) -> Optional[FeederRow]:
        row = (
            self.db.query(Feeder, Substation, func.ST_AsGeoJSON(Feeder.geometry))
            .outerjoin(Substation, Feeder.substation_id == Substation.id)
            .filter(Feeder.feeder_id == feeder_id, Feeder.active.is_(True))
            .first()
        )
        if not row:
            return None
        feeder, substation, geometry_geojson = row
        return FeederRow(feeder=feeder, substation=substation, geometry_geojson=geometry_geojson)

    def search_feeders(
        self,
        feeder_id: Optional[str] = None,
        substation_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FeederRow]:
        query = (
            self.db.query(Feeder, Substation, func.ST_AsGeoJSON(Feeder.geometry))
            .outerjoin(Substation, Feeder.substation_id == Substation.id)
            .filter(Feeder.active.is_(True))
            .order_by(Feeder.feeder_id)
        )
        if feeder_id:
            query = query.filter(Feeder.feeder_id.ilike(f"%{feeder_id}%"))
        if substation_id:
            query = query.filter(Substation.source_substation_id == substation_id)

        return [
            FeederRow(feeder=feeder, substation=substation, geometry_geojson=geometry_geojson)
            for feeder, substation, geometry_geojson in query.offset(offset).limit(limit).all()
        ]

    def get_substation(self, substation_id: str) -> Optional[SubstationRow]:
        row = (
            self.db.query(
                Substation,
                func.ST_AsGeoJSON(Substation.geometry),
                func.ST_AsGeoJSON(OsmSubstation.geometry),
                OsmSubstation,
                SubstationOsmMatch,
                func.count(Feeder.id),
            )
            .outerjoin(Feeder, Feeder.substation_id == Substation.id)
            .outerjoin(
                SubstationOsmMatch,
                (SubstationOsmMatch.substation_id == Substation.id) & (SubstationOsmMatch.accepted.is_(True)),
            )
            .outerjoin(OsmSubstation, OsmSubstation.id == SubstationOsmMatch.osm_substation_id)
            .filter(Substation.source_substation_id == substation_id)
            .group_by(Substation.id, OsmSubstation.id, SubstationOsmMatch.id)
            .first()
        )
        if not row:
            return None
        substation, geometry_geojson, osm_geometry_geojson, osm_substation, osm_match, feeder_count = row
        return SubstationRow(
            substation=substation,
            geometry_geojson=geometry_geojson,
            osm_geometry_geojson=osm_geometry_geojson,
            osm_substation=osm_substation,
            osm_match=osm_match,
            feeder_count=feeder_count,
        )

    def get_substation_feeders(self, substation_id: str, limit: int = 50, offset: int = 0) -> list[FeederRow]:
        return [
            FeederRow(feeder=feeder, substation=substation, geometry_geojson=geometry_geojson)
            for feeder, substation, geometry_geojson in (
                self.db.query(Feeder, Substation, func.ST_AsGeoJSON(Feeder.geometry))
                .join(Substation, Feeder.substation_id == Substation.id)
                .filter(
                    Substation.source_substation_id == substation_id,
                    Feeder.active.is_(True),
                )
                .order_by(Feeder.feeder_id)
                .offset(offset)
                .limit(limit)
                .all()
            )
        ]
