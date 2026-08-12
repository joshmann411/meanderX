import logging
from typing import Any, Dict, Optional

import httpx

from app.config.settings import settings
from app.conedison.models import ArcGISResponse

logger = logging.getLogger(__name__)


class ConEdisonArcGISClient:
    def __init__(self, base_url: str = None, timeout: Optional[int] = None, retry_count: int = 0):
        self.base_url = base_url or settings.arcgis_endpoint
        self.timeout = timeout or settings.http_timeout
        self.retry_count = retry_count or settings.http_retry_count
        self._client = httpx.Client(timeout=self.timeout)

    def get_service_metadata(self) -> Dict[str, Any]:
        url = f"{self.base_url}?f=json"
        r = self._client.get(url)
        r.raise_for_status()
        return r.json()

    def query(self, params: Optional[Dict[str, Any]] = None) -> ArcGISResponse:
        params = params or {"f": "json", "where": "1=1", "outFields": "*"}
        r = self._client.get(self.base_url + "/query", params=params)
        r.raise_for_status()
        data = r.json()
        try:
            return ArcGISResponse.model_validate(data)
        except Exception as e:
            logger.exception("Failed to parse ArcGIS response")
            raise
