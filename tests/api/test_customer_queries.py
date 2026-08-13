from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from geoalchemy2 import WKTElement

from app.core.database import Base, SessionLocal, engine, ensure_postgis
from app.main import app
from app.models import Feeder, Substation


@pytest.fixture(autouse=True)
def fixture_database():
    with engine.begin() as conn:
        ensure_postgis(conn)
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)

    session = SessionLocal()
    try:
        substation = Substation(
            source_substation_id="SUB001",
            name="Main Substation",
            source="conedison",
            source_metadata={"source": "conedison"},
        )
        empty_substation = Substation(
            source_substation_id="SUB002",
            name="No Geometry Substation",
            source="conedison",
        )
        session.add_all([substation, empty_substation])
        session.flush()
        session.add_all(
            [
                Feeder(
                    feeder_id="ABC123",
                    substation_id=substation.id,
                    pv_thermal="2.4",
                    geometry=WKTElement("SRID=4326;POINT(-73.94 40.7)", srid=4326, extended=True),
                    source="conedison",
                    last_seen_at=datetime(2026, 1, 1, 12, 0, 0),
                    active=True,
                ),
                Feeder(
                    feeder_id="XYZ999",
                    substation_id=empty_substation.id,
                    pv_thermal=None,
                    geometry=None,
                    source="conedison",
                    last_seen_at=datetime(2026, 1, 2, 12, 0, 0),
                    active=True,
                ),
            ]
        )
        session.commit()
    finally:
        session.close()

    yield


def test_get_existing_feeder():
    response = TestClient(app).get("/api/v1/feeders/ABC123")

    assert response.status_code == 200
    body = response.json()
    assert body["feederId"] == "ABC123"
    assert body["substationId"] == "SUB001"
    assert body["hostingCapacity"]["pvThermal"] == 2.4
    assert body["geometry"]["type"] == "Point"
    assert body["data"]["source"] == "conedison"
    assert "attributes" not in body


def test_get_missing_feeder_returns_error_contract():
    response = TestClient(app).get("/api/v1/feeders/MISSING")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Feeder 'MISSING' was not found."}}


def test_search_feeders_by_substation_and_min_capacity():
    response = TestClient(app).get("/api/v1/feeders", params={"substationId": "SUB001", "minPvThermal": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert [item["feederId"] for item in body["items"]] == ["ABC123"]


def test_get_existing_substation():
    response = TestClient(app).get("/api/v1/substations/SUB001")

    assert response.status_code == 200
    body = response.json()
    assert body["substationId"] == "SUB001"
    assert body["name"] == "Main Substation"
    assert body["geometry"] is None
    assert body["connectedFeeders"]["count"] == 1


def test_get_missing_substation_returns_error_contract():
    response = TestClient(app).get("/api/v1/substations/MISSING")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Substation 'MISSING' was not found."}}


def test_list_substation_feeders():
    response = TestClient(app).get("/api/v1/substations/SUB001/feeders")

    assert response.status_code == 200
    assert [item["feederId"] for item in response.json()["items"]] == ["ABC123"]


def test_queue_limitation_response():
    response = TestClient(app).get("/api/v1/feeders/ABC123/queue")

    assert response.status_code == 200
    assert response.json() == {
        "feederId": "ABC123",
        "available": False,
        "projectCount": None,
        "reason": "The hosting capacity source does not expose sufficient project queue data.",
    }


def test_nullable_feeder_geometry():
    response = TestClient(app).get("/api/v1/feeders/XYZ999")

    assert response.status_code == 200
    assert response.json()["geometry"] is None


def test_invalid_query_returns_422_validation_error():
    response = TestClient(app).get("/api/v1/feeders", params={"limit": 0})

    assert response.status_code == 422
