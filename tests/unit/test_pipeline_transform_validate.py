from app.pipelines.conedison.pipeline import ConEdisonPipeline
from app.conedison.client import ConEdisonArcGISClient
from app.conedison.models import ArcGISFeature, ArcGISAttributes, ArcGISGeometry


def test_validate_and_transform():
    client = ConEdisonArcGISClient(base_url="https://example.com/FeatureServer/0")
    pipeline = ConEdisonPipeline(client)
    feat = ArcGISFeature(attributes=ArcGISAttributes(FEEDER_ID="FDR-1", PV_THERMAL="Y"), geometry=ArcGISGeometry(x=-73.9, y=40.7))
    assert pipeline.validate(feat) is True
    out = pipeline.transform(feat)
    assert out["feeder_id"] == "FDR-1"
    assert out["pv_thermal"] == "Y"
    assert out["geometry_ewkt"] == "SRID=4326;POINT(-73.9 40.7)"
