from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from geoalchemy2 import WKTElement

from app.core.database import Base, SessionLocal, engine, ensure_postgis
from app.main import app
from app.models import Feeder, OsmSubstation, Substation, SubstationOsmMatch
from app.services.osm_matching import SubstationMatcher


@pytest.fixture(autouse=True)
def fixture_database():
    with engine.begin() as conn:
        ensure_postgis(conn)
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    yield


def test_accepted_match_stores_confidence_and_api_provenance():
    session = SessionLocal()
    try:
        substation = _substation(session, "SUB001", "Main Substation")
        session.add(
            Feeder(
                feeder_id="F1",
                substation_id=substation.id,
                pv_thermal="2.4",
                geometry=WKTElement("SRID=4326;POINT(-73.94 40.7)", srid=4326, extended=True),
                source="conedison",
                last_seen_at=datetime(2026, 1, 1, 12, 0, 0),
                active=True,
            )
        )
        osm = _osm_substation(session, "way/1", "Main Substation", "Con Edison", -73.94, 40.7)
        summary = SubstationMatcher(session, threshold=0.72).match_all(run_id=None)
        session.commit()

        match = session.query(SubstationOsmMatch).filter_by(substation_id=substation.id, osm_substation_id=osm.id).one()
        assert summary["accepted"] == 1
        assert match.accepted is True
        assert match.confidence >= 0.72

        response = TestClient(app).get("/api/v1/substations/SUB001")
        body = response.json()
        assert response.status_code == 200
        assert body["geometry"]["type"] == "Point"
        assert body["geometrySource"]["source"] == "osm"
        assert body["geometrySource"]["osmId"] == "way/1"
        assert body["geometrySource"]["matchConfidence"] >= 0.72
    finally:
        session.close()


def test_low_confidence_match_is_rejected():
    session = SessionLocal()
    try:
        substation = _substation(session, "SUB001", "Main Substation")
        osm = _osm_substation(session, "way/2", "Unrelated Facility", "Other Utility", -73.0, 41.0)
        SubstationMatcher(session, threshold=0.72).match_all(run_id=None)
        session.commit()

        match = session.query(SubstationOsmMatch).filter_by(substation_id=substation.id, osm_substation_id=osm.id).one()
        assert match.accepted is False
    finally:
        session.close()


def test_ambiguous_matches_are_not_accepted():
    session = SessionLocal()
    try:
        substation = _substation(session, "SUB001", "Main Substation")
        first = _osm_substation(session, "way/3", "Main Substation", "Con Edison", -73.94, 40.7)
        second = _osm_substation(session, "way/4", "Main Substation", "Con Edison", -73.95, 40.71)

        summary = SubstationMatcher(session, threshold=0.72).match_all(run_id=None)
        session.commit()

        matches = session.query(SubstationOsmMatch).filter(SubstationOsmMatch.substation_id == substation.id).all()
        assert summary["accepted"] == 0
        assert len(matches) == 1
        assert matches[0].osm_substation_id in {first.id, second.id}
        assert matches[0].accepted is False
    finally:
        session.close()


def _substation(session, source_id: str, name: str) -> Substation:
    substation = Substation(source_substation_id=source_id, name=name, source="conedison")
    session.add(substation)
    session.flush()
    return substation


def _osm_substation(session, osm_id: str, name: str, operator: str, lon: float, lat: float) -> OsmSubstation:
    substation = OsmSubstation(
        osm_id=osm_id,
        name=name,
        operator=operator,
        voltage="138000",
        substation_type="distribution",
        geometry=WKTElement(f"SRID=4326;POINT({lon} {lat})", srid=4326, extended=True),
        centroid=WKTElement(f"SRID=4326;POINT({lon} {lat})", srid=4326, extended=True),
        source_tags={"power": "substation", "name": name, "operator": operator},
        source="osm",
    )
    session.add(substation)
    session.flush()
    return substation
