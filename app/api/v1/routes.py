from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.schemas import (
    FeederChangesResponse,
    FeederHistoryResponse,
    FeederResponse,
    FeederSearchResponse,
    QueueResponse,
    SubstationResponse,
)
from app.core.database import get_db
from app.repositories.feeders import FeederRepository
from app.repositories.history import HistoryRepository
from app.services.feeders import FeederQueryService, NotFoundError
from app.services.history import FeederHistoryService

router = APIRouter(prefix="/api/v1", tags=["Customer Query API"])


def get_query_service(db: Session = Depends(get_db)) -> FeederQueryService:
    return FeederQueryService(FeederRepository(db))


def get_history_service(db: Session = Depends(get_db)) -> FeederHistoryService:
    return FeederHistoryService(HistoryRepository(db))


@router.get(
    "/feeders",
    response_model=FeederSearchResponse,
    summary="Search feeders",
    description="Search current feeders by feeder ID, substation ID, and optional minimum PV thermal hosting capacity.",
)
def search_feeders(
    feeder_id: Optional[str] = Query(default=None, alias="feederId", description="Partial feeder ID match."),
    substation_id: Optional[str] = Query(default=None, alias="substationId", description="Exact source substation ID."),
    min_pv_thermal: Optional[float] = Query(default=None, alias="minPvThermal", description="Minimum numeric PV_THERMAL value."),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of feeders to return."),
    offset: int = Query(default=0, ge=0, description="Number of feeders to skip."),
    service: FeederQueryService = Depends(get_query_service),
):
    if min_pv_thermal is not None and min_pv_thermal < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="minPvThermal must be greater than or equal to 0.")
    return service.search_feeders(feeder_id, substation_id, min_pv_thermal, limit, offset)


@router.get(
    "/feeders/{feeder_id}/queue",
    response_model=QueueResponse,
    summary="Get feeder queue information",
    description="Return project queue information when the source supports it; otherwise return a stable unavailable response.",
)
def get_feeder_queue(
    feeder_id: str,
    service: FeederQueryService = Depends(get_query_service),
):
    try:
        return service.get_queue(feeder_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/feeders/{feeder_id}/history",
    response_model=FeederHistoryResponse,
    summary="Get feeder history",
    description="Return immutable historical snapshots for a feeder in chronological order.",
)
def get_feeder_history(
    feeder_id: str,
    captured_from: Optional[datetime] = Query(default=None, alias="capturedFrom", description="Inclusive ISO timestamp lower bound."),
    captured_to: Optional[datetime] = Query(default=None, alias="capturedTo", description="Inclusive ISO timestamp upper bound."),
    service: FeederHistoryService = Depends(get_history_service),
):
    try:
        return service.get_history(feeder_id, captured_from, captured_to)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/feeders/{feeder_id}/changes",
    response_model=FeederChangesResponse,
    summary="Get feeder changes",
    description="Compare feeder snapshots and return added, removed, modified, and unchanged events.",
)
def get_feeder_changes(
    feeder_id: str,
    service: FeederHistoryService = Depends(get_history_service),
):
    try:
        return service.get_changes(feeder_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/feeders/{feeder_id}",
    response_model=FeederResponse,
    summary="Get feeder",
    description="Return a domain-oriented feeder response with hosting capacity, geometry, source, and timestamp metadata.",
)
def get_feeder(
    feeder_id: str,
    service: FeederQueryService = Depends(get_query_service),
):
    try:
        return service.get_feeder(feeder_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/substations/{substation_id}",
    response_model=SubstationResponse,
    summary="Get substation",
    description="Return a normalized substation response with nullable geometry and connected feeder summary.",
)
def get_substation(
    substation_id: str,
    service: FeederQueryService = Depends(get_query_service),
):
    try:
        return service.get_substation(substation_id)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


@router.get(
    "/substations/{substation_id}/feeders",
    response_model=FeederSearchResponse,
    summary="List feeders connected to a substation",
    description="Return current feeders associated with the normalized substation relationship.",
)
def get_substation_feeders(
    substation_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of feeders to return."),
    offset: int = Query(default=0, ge=0, description="Number of feeders to skip."),
    service: FeederQueryService = Depends(get_query_service),
):
    try:
        return service.get_substation_feeders(substation_id, limit, offset)
    except NotFoundError as exc:
        raise _not_found(exc) from exc


def _not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{exc.resource.title()} '{exc.identifier}' was not found.",
    )
