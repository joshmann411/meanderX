from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, SessionLocal, engine, ensure_postgis
from app.main import app
from app.models import Feeder, FeederSnapshot, IngestionRun
from app.pipelines.conedison.pipeline import ConEdisonPipeline, _dataset_hash


@pytest.fixture(autouse=True)
def fixture_database():
    with engine.begin() as conn:
        ensure_postgis(conn)
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    yield


def test_snapshot_hash_is_deterministic_independent_of_source_order():
    records = [_record("F2", "1.0", "S1"), _record("F1", "2.0", "S1")]

    assert _dataset_hash(records) == _dataset_hash(list(reversed(records)))


def test_ingestion_snapshots_changes_and_unchanged_dataset():
    pipeline = _pipeline()
    first = [
        _record("F1", "2.4", "S1"),
        _record("F2", "1.0", "S1"),
        _record("F4", "4.0", "S1"),
    ]
    second = [
        _record("F1", "2.1", "S2"),
        _record("F3", "3.0", "S1"),
        _record("F4", "4.0", "S1"),
    ]

    pipeline.load(first, extracted_count=len(first), validation_rejected_count=0)
    pipeline.load(second, extracted_count=len(second), validation_rejected_count=0)
    pipeline.load(list(reversed(second)), extracted_count=len(second), validation_rejected_count=0)

    session = SessionLocal()
    try:
        runs = session.query(IngestionRun).order_by(IngestionRun.id).all()
        assert [run.status for run in runs] == ["SUCCESS", "SUCCESS", "UNCHANGED"]
        assert [run.snapshot_created for run in runs] == [True, True, False]
        assert session.query(FeederSnapshot).count() == 6

        first_f1 = (
            session.query(FeederSnapshot)
            .filter_by(feeder_id="F1", ingestion_run_id=runs[0].id)
            .one()
        )
        current_f1 = session.query(Feeder).filter_by(feeder_id="F1").one()
        removed_f2 = session.query(Feeder).filter_by(feeder_id="F2").one()

        assert first_f1.pv_thermal == "2.4"
        assert current_f1.pv_thermal == "2.1"
        assert current_f1.substation.source_substation_id == "S2"
        assert removed_f2.active is False
    finally:
        session.close()


def test_failed_ingestion_does_not_create_snapshot():
    _pipeline().load([], extracted_count=0, validation_rejected_count=0)

    session = SessionLocal()
    try:
        run = session.query(IngestionRun).one()
        assert run.status == "FAILED"
        assert session.query(FeederSnapshot).count() == 0
    finally:
        session.close()


def test_history_api_returns_chronological_snapshots():
    pipeline = _pipeline()
    pipeline.load([_record("F1", "2.4", "S1")], extracted_count=1, validation_rejected_count=0)
    pipeline.load([_record("F1", "2.1", "S1")], extracted_count=1, validation_rejected_count=0)

    response = TestClient(app).get("/api/v1/feeders/F1/history")

    assert response.status_code == 200
    history = response.json()["history"]
    assert [entry["pvThermal"] for entry in history] == [2.4, 2.1]
    assert [entry["substationId"] for entry in history] == ["S1", "S1"]


def test_changes_api_detects_added_modified_removed_and_unchanged():
    pipeline = _pipeline()
    pipeline.load(
        [
            _record("F1", "2.4", "S1"),
            _record("F2", "1.0", "S1"),
            _record("F4", "4.0", "S1"),
        ],
        extracted_count=3,
        validation_rejected_count=0,
    )
    pipeline.load(
        [
            _record("F1", "2.1", "S2"),
            _record("F3", "3.0", "S1"),
            _record("F4", "4.0", "S1"),
        ],
        extracted_count=3,
        validation_rejected_count=0,
    )

    f1_changes = TestClient(app).get("/api/v1/feeders/F1/changes").json()["changes"]
    f2_changes = TestClient(app).get("/api/v1/feeders/F2/changes").json()["changes"]
    f3_changes = TestClient(app).get("/api/v1/feeders/F3/changes").json()["changes"]
    f4_changes = TestClient(app).get("/api/v1/feeders/F4/changes").json()["changes"]

    assert [event["eventType"] for event in f1_changes] == ["added", "modified"]
    assert {change["field"] for change in f1_changes[1]["changes"]} == {"pvThermal", "substationId"}
    assert [event["eventType"] for event in f2_changes] == ["added", "removed"]
    assert [event["eventType"] for event in f3_changes] == ["added"]
    assert [event["eventType"] for event in f4_changes] == ["added", "unchanged"]


def _pipeline() -> ConEdisonPipeline:
    return ConEdisonPipeline(SimpleNamespace(base_url="conedison"))


def _record(feeder_id: str, pv_thermal: str, substation_id: str) -> dict:
    return {
        "feeder_id": feeder_id,
        "pv_thermal": pv_thermal,
        "geometry_ewkt": "SRID=4326;POINT(-73.94 40.7)",
        "source": "conedison",
        "substation_id": substation_id,
        "substation_name": substation_id,
        "raw_attributes": {"FEEDER_ID": feeder_id, "PV_THERMAL": pv_thermal, "SUBSTATION": substation_id},
    }
