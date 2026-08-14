from sqlalchemy import text

from app.core.database import Base, SessionLocal, engine, ensure_postgis
from app.pipelines.conedison.pipeline import ConEdisonPipeline
from app.pipelines.osm.models import OsmSubstationRecord
from app.pipelines.osm.pipeline import OsmSubstationPipeline


DEMO_FEEDER_ID = "DEMO-F1"
DEMO_SUBSTATION_ID = "DEMO-SUB-A"


def seed_demo_data() -> None:
    with engine.begin() as conn:
        ensure_postgis(conn)
        Base.metadata.drop_all(bind=conn)
        Base.metadata.create_all(bind=conn)

    conedison = ConEdisonPipeline(_DemoClient("demo-conedison"))
    conedison.load(
        [
            _conedison_record("DEMO-F1", "2.4", "DEMO-SUB-A", -73.94, 40.70),
            _conedison_record("DEMO-F2", "1.2", "DEMO-SUB-A", -73.941, 40.701),
        ],
        extracted_count=2,
        validation_rejected_count=0,
    )
    conedison.load(
        [
            _conedison_record("DEMO-F1", "2.1", "DEMO-SUB-A", -73.94, 40.70),
            _conedison_record("DEMO-F3", "3.0", "DEMO-SUB-B", -73.95, 40.71),
        ],
        extracted_count=2,
        validation_rejected_count=0,
    )

    osm = OsmSubstationPipeline(_DemoClient("demo-osm"))
    osm.load(
        [
            OsmSubstationRecord(
                osm_id="way/demo-sub-a",
                name="Demo A",
                operator="Con Edison",
                voltage="138000",
                substation_type="distribution",
                geometry_ewkt="SRID=4326;POLYGON((-73.941 40.699,-73.939 40.699,-73.939 40.701,-73.941 40.699))",
                centroid_ewkt="SRID=4326;POINT(-73.94 40.7)",
                source_tags={
                    "power": "substation",
                    "name": "Demo A",
                    "operator": "Con Edison",
                    "voltage": "138000",
                    "substation": "distribution",
                    "demo": "true",
                },
            )
        ],
        extracted_count=1,
        rejected_count=0,
    )

    with SessionLocal() as session:
        counts = {
            "feeders": session.execute(text("SELECT count(*) FROM feeders")).scalar_one(),
            "feederSnapshots": session.execute(text("SELECT count(*) FROM feeder_snapshots")).scalar_one(),
            "osmSubstations": session.execute(text("SELECT count(*) FROM osm_substations")).scalar_one(),
            "acceptedMatches": session.execute(text("SELECT count(*) FROM substation_osm_matches WHERE accepted = true")).scalar_one(),
        }
    print(f"Demo data seeded: {counts}")


def _conedison_record(feeder_id: str, pv_thermal: str, substation_id: str, lon: float, lat: float) -> dict:
    return {
        "feeder_id": feeder_id,
        "pv_thermal": pv_thermal,
        "geometry_ewkt": f"SRID=4326;POINT({lon} {lat})",
        "source": "demo-conedison",
        "substation_id": substation_id,
        "substation_name": "Demo A" if substation_id == "DEMO-SUB-A" else "Brooklyn East",
        "raw_attributes": {
            "FEEDER_ID": feeder_id,
            "PV_THERMAL": pv_thermal,
            "SUBSTATION": substation_id,
            "DEMO_DATA": True,
        },
    }


class _DemoClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
