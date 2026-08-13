import logging
from typing import Any, Dict, Optional

import httpx

from app.config.settings import settings
from app.conedison.models import ArcGISResponse

logger = logging.getLogger(__name__)


class ConEdisonArcGISClient:
    def __init__(self, base_url: str = None, timeout: Optional[int] = None, retry_count: int = 0):
        self.base_url = str(base_url or settings.arcgis_endpoint).rstrip("/")
        self.timeout = timeout or settings.http_timeout
        self.retry_count = retry_count or settings.http_retry_count
        self._client = httpx.Client(timeout=self.timeout)

    def query_all(self, params: Optional[Dict[str, Any]] = None):
        """Yield ArcGIS features across pages until complete.

        Uses `maxRecordCount` from service metadata when available and
        iterates using `resultOffset`/`resultRecordCount`.
        """
        meta = None
        try:
            meta = self.get_service_metadata()
        except Exception:
            meta = {}

        max_rec = int(meta.get("maxRecordCount") or 1000)
        total_count = self.get_feature_count(params)
        object_id_field = meta.get("objectIdFieldName") or "OBJECTID"
        seen_object_ids = set()
        offset = 0
        page = 0
        params = params or {"where": "1=1", "outFields": "*", "returnGeometry": True}
        params = dict(params)
        params.update({"f": "json", "resultRecordCount": max_rec})

        while True:
            page += 1
            params["resultOffset"] = offset
            logger.debug("Querying ArcGIS page %s offset=%s max=%s", page, offset, max_rec)
            for attempt in range(self.retry_count + 1):
                try:
                    r = self._client.get(self.base_url + "/query", params=params)
                    r.raise_for_status()
                    data = r.json()
                    resp = ArcGISResponse.model_validate(data)
                    features = resp.features or []
                    count = len(features)
                    new_features = []
                    for feature in features:
                        object_id = getattr(feature.attributes, object_id_field, None)
                        if object_id is None:
                            new_features.append(feature)
                            continue
                        if object_id in seen_object_ids:
                            continue
                        seen_object_ids.add(object_id)
                        new_features.append(feature)

                    logger.info("Retrieved page %s: %s features", page, count)
                    if count > 0 and not new_features:
                        logger.warning("ArcGIS page %s repeated previously seen object IDs; finishing pagination", page)
                        return
                    yield from new_features
                    offset += count
                    # Determine completion: no features or below max and service not exceeded transfer
                    if count == 0:
                        logger.debug("No more features returned; finishing pagination")
                        return
                    if total_count is not None and offset >= total_count:
                        logger.debug("Retrieved all %s source features; finishing pagination", total_count)
                        return
                    if not resp.exceededTransferLimit and count < max_rec:
                        logger.debug("Service indicates complete result set; finishing pagination")
                        return
                    break
                except Exception as e:
                    logger.warning("ArcGIS query attempt %s failed: %s", attempt + 1, e)
                    if attempt >= self.retry_count:
                        logger.exception("Exceeded retry attempts for ArcGIS query")
                        raise
                    continue

    def get_service_metadata(self) -> Dict[str, Any]:
        url = f"{self.base_url}?f=json"
        r = self._client.get(url)
        r.raise_for_status()
        return r.json()

    def get_feature_count(self, params: Optional[Dict[str, Any]] = None) -> Optional[int]:
        count_params = {"f": "json", "where": "1=1", "returnCountOnly": True}
        if params and "where" in params:
            count_params["where"] = params["where"]
        try:
            r = self._client.get(self.base_url + "/query", params=count_params)
            r.raise_for_status()
            data = r.json()
            if "count" in data:
                return int(data["count"])
        except Exception:
            logger.debug("ArcGIS count request failed; falling back to page termination", exc_info=True)
        return None

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
