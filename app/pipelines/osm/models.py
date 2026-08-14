from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class OsmSubstationRecord:
    osm_id: str
    name: Optional[str]
    operator: Optional[str]
    voltage: Optional[str]
    substation_type: Optional[str]
    geometry_ewkt: str
    centroid_ewkt: str
    source_tags: dict[str, Any]
