from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ArcGISAttributes(BaseModel):
    # Keep flexible because source-specific fields are discovered from metadata.
    FEEDER_ID: Optional[str] = None
    PV_THERMAL: Optional[Any] = None
    OBJECTID: Optional[int] = None

    model_config = {"extra": "allow"}


class ArcGISGeometry(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    paths: Optional[List[List[List[float]]]] = None
    rings: Optional[List[List[List[float]]]] = None
    spatialReference: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}


class ArcGISFeature(BaseModel):
    attributes: ArcGISAttributes
    geometry: Optional[ArcGISGeometry] = None


class ArcGISResponse(BaseModel):
    objectIdFieldName: Optional[str] = None
    globalIdFieldName: Optional[str] = None
    fields: Optional[List[Dict[str, Any]]] = None
    features: List[ArcGISFeature]
    exceededTransferLimit: Optional[bool] = False
    spatialReference: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}
