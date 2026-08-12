import json
import httpx
from app.conedison.client import ConEdisonArcGISClient
from app.conedison.models import ArcGISResponse


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_client_parses_fixture(monkeypatch):
    data = json.loads(open("tests/fixtures/arcgis_feature.json").read())

    def fake_get(url, params=None):
        return DummyResponse(data)

    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0")
    monkeypatch.setattr(client._client, "get", fake_get)
    resp = client.query()
    assert isinstance(resp, ArcGISResponse)
    assert resp.features[0].attributes.FEEDER_ID == "FDR-001"
