"""add osm substation enrichment

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-01 00:40:00.000000
"""
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS osm_substations (
            id SERIAL PRIMARY KEY,
            osm_id VARCHAR NOT NULL,
            name VARCHAR NULL,
            operator VARCHAR NULL,
            voltage VARCHAR NULL,
            substation_type VARCHAR NULL,
            geometry geometry(GEOMETRY, 4326) NOT NULL,
            centroid geometry(POINT, 4326) NULL,
            source_tags JSON NULL,
            source VARCHAR NOT NULL DEFAULT 'osm',
            first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            CONSTRAINT uq_osm_substations_osm_id UNIQUE (osm_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS substation_osm_matches (
            id SERIAL PRIMARY KEY,
            substation_id INTEGER NOT NULL REFERENCES substations(id),
            osm_substation_id INTEGER NOT NULL REFERENCES osm_substations(id),
            ingestion_run_id INTEGER NULL REFERENCES ingestion_runs(id),
            confidence DOUBLE PRECISION NOT NULL,
            match_method VARCHAR NOT NULL,
            distance_meters DOUBLE PRECISION NULL,
            accepted BOOLEAN NOT NULL DEFAULT false,
            matched_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
            CONSTRAINT uq_substation_osm_matches_pair UNIQUE (substation_id, osm_substation_id)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_osm_substations_osm_id ON osm_substations (osm_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_osm_substations_name ON osm_substations (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_osm_substations_geometry_gist ON osm_substations USING gist (geometry)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_osm_substations_centroid_gist ON osm_substations USING gist (centroid)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_osm_matches_substation_id ON substation_osm_matches (substation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_osm_matches_osm_substation_id ON substation_osm_matches (osm_substation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_osm_matches_ingestion_run_id ON substation_osm_matches (ingestion_run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_osm_matches_accepted ON substation_osm_matches (accepted)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_substation_osm_matches_accepted")
    op.execute("DROP INDEX IF EXISTS ix_substation_osm_matches_ingestion_run_id")
    op.execute("DROP INDEX IF EXISTS ix_substation_osm_matches_osm_substation_id")
    op.execute("DROP INDEX IF EXISTS ix_substation_osm_matches_substation_id")
    op.execute("DROP INDEX IF EXISTS ix_osm_substations_centroid_gist")
    op.execute("DROP INDEX IF EXISTS ix_osm_substations_geometry_gist")
    op.execute("DROP INDEX IF EXISTS ix_osm_substations_name")
    op.execute("DROP INDEX IF EXISTS ix_osm_substations_osm_id")
    op.execute("DROP TABLE IF EXISTS substation_osm_matches")
    op.execute("DROP TABLE IF EXISTS osm_substations")
