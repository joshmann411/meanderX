from types import SimpleNamespace

from app.pipelines.osm.pipeline import OsmSubstationPipeline
from app.services.osm_matching import name_similarity, normalize_name


def test_osm_tag_filtering():
    pipeline = OsmSubstationPipeline(SimpleNamespace())

    assert pipeline.validate({"tags": {"power": "substation"}}) is True
    assert pipeline.validate({"tags": {"power": "plant"}}) is False


def test_osm_way_geometry_and_tag_normalization():
    pipeline = OsmSubstationPipeline(SimpleNamespace())
    record = {
        "type": "way",
        "id": 10,
        "tags": {
            "power": "substation",
            "name": "Main Substation",
            "operator": "Con Edison",
            "voltage": "138000;34500",
            "substation": "distribution",
        },
        "geometry": [
            {"lat": 40.7, "lon": -73.94},
            {"lat": 40.7, "lon": -73.93},
            {"lat": 40.71, "lon": -73.93},
            {"lat": 40.7, "lon": -73.94},
        ],
    }

    transformed = pipeline.transform(record)

    assert transformed.osm_id == "way/10"
    assert transformed.operator == "Con Edison"
    assert transformed.voltage == "138000;34500"
    assert transformed.substation_type == "distribution"
    assert transformed.geometry_ewkt.startswith("SRID=4326;POLYGON")
    assert transformed.centroid_ewkt.startswith("SRID=4326;POINT")


def test_osm_node_geometry_parsing():
    pipeline = OsmSubstationPipeline(SimpleNamespace())
    record = {
        "type": "node",
        "id": 11,
        "lat": 40.7,
        "lon": -73.94,
        "tags": {"power": "substation", "name": "Tiny Substation"},
    }

    transformed = pipeline.transform(record)

    assert transformed.osm_id == "node/11"
    assert transformed.geometry_ewkt == "SRID=4326;POINT(-73.94 40.7)"


def test_name_normalization_and_similarity():
    assert normalize_name("Main Switching Substation") == "main"
    assert name_similarity("Main", "Main Substation") >= 0.9
    assert name_similarity("Main", "Far Away") < 0.5
