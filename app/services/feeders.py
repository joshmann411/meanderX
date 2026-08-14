import json
from typing import Optional

from app.api.v1.schemas import (
    ConnectedFeederSummary,
    FeederResponse,
    FeederSearchResponse,
    GeometrySource,
    HostingCapacity,
    QueueResponse,
    ResponseData,
    SubstationResponse,
)
from app.repositories.feeders import FeederRepository, FeederRow, SubstationRow

QUEUE_UNAVAILABLE_REASON = "The hosting capacity source does not expose sufficient project queue data."


class NotFoundError(Exception):
    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} '{identifier}' was not found.")


class FeederQueryService:
    def __init__(self, repository: FeederRepository):
        self.repository = repository

    def get_feeder(self, feeder_id: str) -> FeederResponse:
        row = self.repository.get_feeder(feeder_id)
        if row is None:
            raise NotFoundError("feeder", feeder_id)
        return _feeder_response(row)

    def search_feeders(
        self,
        feeder_id: Optional[str],
        substation_id: Optional[str],
        min_pv_thermal: Optional[float],
        limit: int,
        offset: int,
    ) -> FeederSearchResponse:
        rows = self.repository.search_feeders(feeder_id=feeder_id, substation_id=substation_id, limit=limit, offset=offset)
        if min_pv_thermal is not None:
            rows = [row for row in rows if _numeric_or_none(row.feeder.pv_thermal) is not None and _numeric_or_none(row.feeder.pv_thermal) >= min_pv_thermal]
        return FeederSearchResponse(items=[_feeder_response(row) for row in rows], limit=limit, offset=offset)

    def get_substation(self, substation_id: str) -> SubstationResponse:
        row = self.repository.get_substation(substation_id)
        if row is None:
            raise NotFoundError("substation", substation_id)
        return _substation_response(row)

    def get_substation_feeders(self, substation_id: str, limit: int, offset: int) -> FeederSearchResponse:
        if self.repository.get_substation(substation_id) is None:
            raise NotFoundError("substation", substation_id)
        rows = self.repository.get_substation_feeders(substation_id, limit=limit, offset=offset)
        return FeederSearchResponse(items=[_feeder_response(row) for row in rows], limit=limit, offset=offset)

    def get_queue(self, feeder_id: str) -> QueueResponse:
        if self.repository.get_feeder(feeder_id) is None:
            raise NotFoundError("feeder", feeder_id)
        return QueueResponse(
            feederId=feeder_id,
            available=False,
            projectCount=None,
            reason=QUEUE_UNAVAILABLE_REASON,
        )


def _feeder_response(row: FeederRow) -> FeederResponse:
    feeder = row.feeder
    substation_id = row.substation.source_substation_id if row.substation else None
    return FeederResponse(
        feederId=feeder.feeder_id,
        substationId=substation_id,
        hostingCapacity=HostingCapacity(pvThermal=_capacity_value(feeder.pv_thermal)),
        geometry=_geojson(row.geometry_geojson),
        data=ResponseData(source="conedison", capturedAt=feeder.last_seen_at),
    )


def _substation_response(row: SubstationRow) -> SubstationResponse:
    substation = row.substation
    geometry = row.geometry_geojson
    geometry_source = None
    if not geometry and row.osm_geometry_geojson and row.osm_substation and row.osm_match:
        geometry = row.osm_geometry_geojson
        geometry_source = GeometrySource(
            source="osm",
            osmId=row.osm_substation.osm_id,
            matchConfidence=row.osm_match.confidence,
            matchMethod=row.osm_match.match_method,
            distanceMeters=row.osm_match.distance_meters,
        )
    return SubstationResponse(
        substationId=substation.source_substation_id or str(substation.id),
        name=substation.name,
        geometry=_geojson(geometry),
        geometrySource=geometry_source,
        connectedFeeders=ConnectedFeederSummary(count=row.feeder_count),
        sourceMetadata={"source": substation.source},
    )


def _geojson(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    return json.loads(value)


def _capacity_value(value: Optional[str]) -> Optional[float | str]:
    numeric = _numeric_or_none(value)
    return numeric if numeric is not None else value


def _numeric_or_none(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None
