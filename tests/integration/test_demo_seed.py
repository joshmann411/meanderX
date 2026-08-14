import pytest

from app.core.database import Base, SessionLocal, engine, ensure_postgis
from app.demo import DEMO_FEEDER_ID, DEMO_SUBSTATION_ID, seed_demo_data
from app.models import Feeder, FeederSnapshot, Substation, SubstationOsmMatch


@pytest.fixture(autouse=True)
def fixture_database():
    with engine.begin() as conn:
        ensure_postgis(conn)
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)
    yield


def test_demo_seed_creates_reviewer_dataset():
    seed_demo_data()

    session = SessionLocal()
    try:
        assert session.query(Feeder).filter_by(feeder_id=DEMO_FEEDER_ID, active=True).one()
        assert session.query(Substation).filter_by(source_substation_id=DEMO_SUBSTATION_ID).one()
        assert session.query(FeederSnapshot).filter_by(feeder_id=DEMO_FEEDER_ID).count() == 2
        assert session.query(SubstationOsmMatch).filter_by(accepted=True).count() == 1
    finally:
        session.close()
