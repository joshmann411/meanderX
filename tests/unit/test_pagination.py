from app.conedison.client import ConEdisonArcGISClient


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_query_all_paginates(monkeypatch):
    page1 = {
        "features": [{"attributes": {"FEEDER_ID": "FDR-1", "OBJECTID": 1}, "geometry": {"x": 0, "y": 0}}],
        "exceededTransferLimit": True,
    }
    page2 = {
        "features": [{"attributes": {"FEEDER_ID": "FDR-2", "OBJECTID": 2}, "geometry": {"x": 1, "y": 1}}],
        "exceededTransferLimit": False,
    }
    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0")
    calls = {"count": 0}

    def fake_get(url, params=None):
        calls["count"] += 1
        return DummyResponse(page1 if calls["count"] == 1 else page2)

    monkeypatch.setattr(client, "get_service_metadata", lambda: {"maxRecordCount": 1, "objectIdFieldName": "OBJECTID"})
    monkeypatch.setattr(client, "get_feature_count", lambda params=None: None)
    monkeypatch.setattr(client._client, "get", fake_get)

    features = list(client.query_all())

    assert [feature.attributes.FEEDER_ID for feature in features] == ["FDR-1", "FDR-2"]


def test_query_all_uses_count_to_stop(monkeypatch):
    page1 = {"features": [{"attributes": {"FEEDER_ID": "F1", "OBJECTID": 1}}], "exceededTransferLimit": False}
    page2 = {"features": [{"attributes": {"FEEDER_ID": "F2", "OBJECTID": 2}}], "exceededTransferLimit": False}
    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0", timeout=1, retry_count=0)

    def fake_get(url, params=None):
        offset = int(params.get("resultOffset", 0))
        return DummyResponse(page1 if offset == 0 else page2)

    monkeypatch.setattr(client, "get_service_metadata", lambda: {"maxRecordCount": 1, "objectIdFieldName": "OBJECTID"})
    monkeypatch.setattr(client, "get_feature_count", lambda params=None: 2)
    monkeypatch.setattr(client._client, "get", fake_get)

    got = list(client.query_all())

    assert [feature.attributes.FEEDER_ID for feature in got] == ["F1", "F2"]
