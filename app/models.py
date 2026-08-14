from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Float,
    JSON,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    id = Column(Integer, primary_key=True)
    pipeline = Column(String, nullable=False)
    source = Column(String, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False)
    extracted_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    loaded_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    error = Column(String, nullable=True)
    dataset_hash = Column(String, nullable=True, index=True)
    snapshot_created = Column(Boolean, default=False)
    metadata_json = Column("metadata", JSON, nullable=True)


class Substation(Base):
    __tablename__ = "substations"
    __table_args__ = (UniqueConstraint("source", "source_substation_id", name="uq_substations_source_source_id"),)

    id = Column(Integer, primary_key=True)
    source_substation_id = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    source = Column(String, nullable=True)
    source_metadata = Column("metadata", JSON, nullable=True)


class Feeder(Base):
    __tablename__ = "feeders"
    __table_args__ = (UniqueConstraint("source", "feeder_id", name="uq_feeders_source_feeder_id"),)

    id = Column(Integer, primary_key=True)
    feeder_id = Column(String, nullable=False, index=True)
    substation_id = Column(Integer, ForeignKey("substations.id"), nullable=True)
    pv_thermal = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    source = Column(String, nullable=True)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    active = Column(Boolean, default=True)

    substation = relationship("Substation", backref="feeders")


class SubstationSnapshot(Base):
    __tablename__ = "substation_snapshots"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "source", "source_substation_id", name="uq_substation_snapshots_run_source_id"),
    )

    id = Column(Integer, primary_key=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False, index=True)
    source_substation_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    source = Column(String, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    source_metadata = Column("metadata", JSON, nullable=True)

    ingestion_run = relationship("IngestionRun", backref="substation_snapshots")


class FeederSnapshot(Base):
    __tablename__ = "feeder_snapshots"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "source", "feeder_id", name="uq_feeder_snapshots_run_source_feeder"),
    )

    id = Column(Integer, primary_key=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=False, index=True)
    feeder_id = Column(String, nullable=False, index=True)
    substation_id = Column(String, nullable=True, index=True)
    pv_thermal = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=True)
    geometry_hash = Column(String, nullable=True)
    source = Column(String, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)

    ingestion_run = relationship("IngestionRun", backref="feeder_snapshots")


class OsmSubstation(Base):
    __tablename__ = "osm_substations"
    __table_args__ = (UniqueConstraint("osm_id", name="uq_osm_substations_osm_id"),)

    id = Column(Integer, primary_key=True)
    osm_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True, index=True)
    operator = Column(String, nullable=True)
    voltage = Column(String, nullable=True)
    substation_type = Column(String, nullable=True)
    geometry = Column(Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False)
    centroid = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    source_tags = Column(JSON, nullable=True)
    source = Column(String, nullable=False, default="osm")
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SubstationOsmMatch(Base):
    __tablename__ = "substation_osm_matches"
    __table_args__ = (
        UniqueConstraint("substation_id", "osm_substation_id", name="uq_substation_osm_matches_pair"),
    )

    id = Column(Integer, primary_key=True)
    substation_id = Column(Integer, ForeignKey("substations.id"), nullable=False, index=True)
    osm_substation_id = Column(Integer, ForeignKey("osm_substations.id"), nullable=False, index=True)
    ingestion_run_id = Column(Integer, ForeignKey("ingestion_runs.id"), nullable=True, index=True)
    confidence = Column(Float, nullable=False)
    match_method = Column(String, nullable=False)
    distance_meters = Column(Float, nullable=True)
    accepted = Column(Boolean, default=False, nullable=False)
    matched_at = Column(DateTime(timezone=True), server_default=func.now())

    substation = relationship("Substation", backref="osm_matches")
    osm_substation = relationship("OsmSubstation", backref="substation_matches")
    ingestion_run = relationship("IngestionRun", backref="substation_osm_matches")
