import json
from app.conedison.models import ArcGISResponse


def test_models_parse_fixture():
    data = json.loads(open("tests/fixtures/arcgis_feature.json").read())
    resp = ArcGISResponse.model_validate(data)
    assert resp.objectIdFieldName == "OBJECTID"
    assert len(resp.features) == 1
    f = resp.features[0]
    assert f.attributes.FEEDER_ID == "FDR-001"
