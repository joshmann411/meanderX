from typing import Any, Dict, Optional

import httpx

from app.config.settings import settings


class OsmOverpassClient:
    def __init__(self, overpass_url: Optional[str] = None, bbox: Optional[str] = None, timeout: Optional[int] = None):
        self.overpass_url = overpass_url or settings.osm_overpass_url
        self.bbox = bbox or settings.osm_bbox
        self.timeout = timeout or settings.http_timeout
        self._client = httpx.Client(timeout=self.timeout)

    def query_substations(self) -> Dict[str, Any]:
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          node["power"="substation"]({self.bbox});
          way["power"="substation"]({self.bbox});
          relation["power"="substation"]({self.bbox});
        );
        out tags geom;
        """
        response = self._client.post(self.overpass_url, data={"data": query})
        response.raise_for_status()
        return response.json()
