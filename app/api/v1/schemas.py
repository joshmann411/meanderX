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


class SubstationResponse(BaseModel):
    substation_id: str = Field(alias="substationId", examples=["SUB001"])
    name: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None
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
