from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class HostingCapacity(BaseModel):
    pv_thermal: Optional[float | str] = Field(
        default=None,
        alias="pvThermal",
        description="PV thermal hosting capacity from the source when parseable.",
        examples=[2.4],
    )

    model_config = ConfigDict(populate_by_name=True)


class ResponseData(BaseModel):
    source: Optional[str] = Field(default=None, examples=["conedison"])
    captured_at: Optional[datetime] = Field(default=None, alias="capturedAt")

    model_config = ConfigDict(populate_by_name=True)


class FeederResponse(BaseModel):
    feeder_id: str = Field(alias="feederId", examples=["ABC123"])
    substation_id: Optional[str] = Field(default=None, alias="substationId", examples=["SUB001"])
    hosting_capacity: HostingCapacity = Field(alias="hostingCapacity")
    geometry: Optional[dict[str, Any]] = None
    data: ResponseData

    model_config = ConfigDict(populate_by_name=True)


class FeederSearchResponse(BaseModel):
    items: list[FeederResponse]
    limit: int
    offset: int


class ConnectedFeederSummary(BaseModel):
    count: int


class GeometrySource(BaseModel):
    source: str
    osm_id: Optional[str] = Field(default=None, alias="osmId")
    match_confidence: Optional[float] = Field(default=None, alias="matchConfidence")
    match_method: Optional[str] = Field(default=None, alias="matchMethod")
    distance_meters: Optional[float] = Field(default=None, alias="distanceMeters")

    model_config = ConfigDict(populate_by_name=True)


class SubstationResponse(BaseModel):
    substation_id: str = Field(alias="substationId", examples=["SUB001"])
    name: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None
    geometry_source: Optional[GeometrySource] = Field(default=None, alias="geometrySource")
    connected_feeders: ConnectedFeederSummary = Field(alias="connectedFeeders")
    source_metadata: dict[str, Any] = Field(default_factory=dict, alias="sourceMetadata")

    model_config = ConfigDict(populate_by_name=True)


class QueueResponse(BaseModel):
    feeder_id: str = Field(alias="feederId", examples=["ABC123"])
    available: bool
    project_count: Optional[int] = Field(default=None, alias="projectCount")
    reason: Optional[str] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class FeederHistoryEntry(BaseModel):
    captured_at: datetime = Field(alias="capturedAt")
    pv_thermal: Optional[float | str] = Field(default=None, alias="pvThermal")
    substation_id: Optional[str] = Field(default=None, alias="substationId")
    geometry: Optional[dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True)


class FeederHistoryResponse(BaseModel):
    feeder_id: str = Field(alias="feederId")
    history: list[FeederHistoryEntry]

    model_config = ConfigDict(populate_by_name=True)


class FieldChange(BaseModel):
    field: str
    old_value: Any = Field(default=None, alias="oldValue")
    new_value: Any = Field(default=None, alias="newValue")

    model_config = ConfigDict(populate_by_name=True)


class FeederChangeEvent(BaseModel):
    captured_at: datetime = Field(alias="capturedAt")
    event_type: str = Field(alias="eventType", examples=["modified"])
    changes: list[FieldChange]

    model_config = ConfigDict(populate_by_name=True)


class FeederChangesResponse(BaseModel):
    feeder_id: str = Field(alias="feederId")
    changes: list[FeederChangeEvent]

    model_config = ConfigDict(populate_by_name=True)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class SystemCounts(BaseModel):
    feeders: int
    active_feeders: int = Field(alias="activeFeeders")
    substations: int
    feeder_snapshots: int = Field(alias="feederSnapshots")
    substation_snapshots: int = Field(alias="substationSnapshots")
    osm_substations: int = Field(alias="osmSubstations")
    accepted_osm_matches: int = Field(alias="acceptedOsmMatches")

    model_config = ConfigDict(populate_by_name=True)


class IngestionRunSummary(BaseModel):
    id: int
    pipeline: str
    source: str
    status: str
    extracted_count: int = Field(alias="extractedCount")
    valid_count: int = Field(alias="validCount")
    loaded_count: int = Field(alias="loadedCount")
    rejected_count: int = Field(alias="rejectedCount")
    snapshot_created: bool = Field(alias="snapshotCreated")
    dataset_hash_prefix: Optional[str] = Field(default=None, alias="datasetHashPrefix")
    completed_at: Optional[datetime] = Field(default=None, alias="completedAt")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class SourceCapability(BaseModel):
    available: bool
    note: str


class SystemSources(BaseModel):
    conedison: SourceCapability
    osm: SourceCapability
    queue: SourceCapability


class SystemSummaryResponse(BaseModel):
    mode: str
    environment: str
    counts: SystemCounts
    latest_ingestions: list[IngestionRunSummary] = Field(alias="latestIngestions")
    sources: SystemSources
    pipeline_stages: list[str] = Field(alias="pipelineStages")

    model_config = ConfigDict(populate_by_name=True)
