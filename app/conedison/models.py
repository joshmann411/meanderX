from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ArcGISAttributes(BaseModel):
    # Keep flexible — fields will be inspected from metadata
    FEEDER_ID: Optional[str] = None
    PV_THERMAL: Optional[str] = None
    OBJECTID: Optional[int] = None
    # allow extra
    class Config:
        extra = "allow"


class ArcGISGeometry(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    spatialReference: Optional[Dict[str, Any]] = None


class ArcGISFeature(BaseModel):
    attributes: ArcGISAttributes
    geometry: Optional[ArcGISGeometry]


class ArcGISResponse(BaseModel):
    objectIdFieldName: Optional[str]
    globalIdFieldName: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    features: List[ArcGISFeature]
    exceededTransferLimit: Optional[bool] = False
    spatialReference: Optional[Dict[str, Any]] = None
