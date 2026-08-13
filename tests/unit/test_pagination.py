import json

from app.conedison.client import ConEdisonArcGISClient


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_query_all_paginates(monkeypatch):
    # service metadata says maxRecordCount is 1 to force paging
    page1 = {
        "maxRecordCount": 1,
        "features": [
            {"attributes": {"FEEDER_ID": "FDR-1", "OBJECTID": 1}, "geometry": {"x": 0, "y": 0}}
        ],
        "exceededTransferLimit": True,
    }
    page2 = {
        "features": [
            {"attributes": {"FEEDER_ID": "FDR-2", "OBJECTID": 2}, "geometry": {"x": 1, "y": 1}}
        ],
        "exceededTransferLimit": False,
    }

    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0")

    def fake_metadata():
        return {"maxRecordCount": 1, "objectIdFieldName": "OBJECTID"}

    calls = {"count": 0}

    def fake_get(url, params=None):
        # first page then second
        calls["count"] += 1
        if calls["count"] == 1:
            return DummyResponse(page1)
        return DummyResponse(page2)

    monkeypatch.setattr(client, "get_service_metadata", fake_metadata)
    monkeypatch.setattr(client, "get_feature_count", lambda params=None: None)
    monkeypatch.setattr(client._client, "get", fake_get)

    features = list(client.query_all())
    assert len(features) == 2
    assert features[0].attributes.FEEDER_ID == "FDR-1"
    assert features[1].attributes.FEEDER_ID == "FDR-2"
import json
from app.conedison.client import ConEdisonArcGISClient


def test_query_all_pagination(monkeypatch):
    # mock metadata
    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0", timeout=1, retry_count=0)

    def fake_get_metadata():
        return {"maxRecordCount": 1, "objectIdFieldName": "OBJECTID"}

    # two pages of features
    page1 = {"features": [{"attributes": {"FEEDER_ID": "F1", "OBJECTID": 1}}], "exceededTransferLimit": False}
    page2 = {"features": [{"attributes": {"FEEDER_ID": "F2", "OBJECTID": 2}}], "exceededTransferLimit": False}

    calls = {"count": 0}

    def fake_get(url, params=None):
        if url.endswith("?f=json"):
            return DummyResponse(fake_get_metadata())
        # return page based on offset
        offset = int(params.get("resultOffset", 0))
        calls["count"] += 1
        if offset == 0:
            return DummyResponse(page1)
        else:
            return DummyResponse(page2)

    monkeypatch.setattr(client._client, "get", fake_get)
    monkeypatch.setattr(client, "get_feature_count", lambda params=None: 2)
    got = list(client.query_all())
    assert len(got) == 2
    assert got[0].attributes.FEEDER_ID == "F1"
    assert got[1].attributes.FEEDER_ID == "F2"
