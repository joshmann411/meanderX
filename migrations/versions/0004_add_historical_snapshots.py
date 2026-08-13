"""add historical snapshots

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-01 00:30:00.000000
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS dataset_hash VARCHAR")
    op.execute("ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS snapshot_created BOOLEAN DEFAULT false")
    op.execute('ALTER TABLE ingestion_runs ADD COLUMN IF NOT EXISTS "metadata" JSON')
    op.execute("CREATE INDEX IF NOT EXISTS ix_ingestion_runs_dataset_hash ON ingestion_runs (dataset_hash)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS substation_snapshots (
            id SERIAL PRIMARY KEY,
            ingestion_run_id INTEGER NOT NULL REFERENCES ingestion_runs(id),
            source_substation_id VARCHAR NOT NULL,
            name VARCHAR NULL,
            geometry geometry(GEOMETRY, 4326) NULL,
            source VARCHAR NULL,
            captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
            metadata JSON NULL,
            CONSTRAINT uq_substation_snapshots_run_source_id
                UNIQUE (ingestion_run_id, source, source_substation_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS feeder_snapshots (
            id SERIAL PRIMARY KEY,
            ingestion_run_id INTEGER NOT NULL REFERENCES ingestion_runs(id),
            feeder_id VARCHAR NOT NULL,
            substation_id VARCHAR NULL,
            pv_thermal VARCHAR NULL,
            geometry geometry(GEOMETRY, 4326) NULL,
            geometry_hash VARCHAR NULL,
            source VARCHAR NULL,
            captured_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT uq_feeder_snapshots_run_source_feeder
                UNIQUE (ingestion_run_id, source, feeder_id)
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_snapshots_ingestion_run_id ON substation_snapshots (ingestion_run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_snapshots_source_substation_id ON substation_snapshots (source_substation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_ingestion_run_id ON feeder_snapshots (ingestion_run_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_feeder_id ON feeder_snapshots (feeder_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_substation_id ON feeder_snapshots (substation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_feeder_captured ON feeder_snapshots (feeder_id, captured_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_run_feeder ON feeder_snapshots (ingestion_run_id, feeder_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_substation_snapshots_source_captured ON substation_snapshots (source_substation_id, captured_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_feeder_snapshots_geometry_gist ON feeder_snapshots USING gist (geometry)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_geometry_gist")
    op.execute("DROP INDEX IF EXISTS ix_substation_snapshots_source_captured")
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_run_feeder")
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_feeder_captured")
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_substation_id")
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_feeder_id")
    op.execute("DROP INDEX IF EXISTS ix_feeder_snapshots_ingestion_run_id")
    op.execute("DROP INDEX IF EXISTS ix_substation_snapshots_source_substation_id")
    op.execute("DROP INDEX IF EXISTS ix_substation_snapshots_ingestion_run_id")
    op.execute("DROP TABLE IF EXISTS feeder_snapshots")
    op.execute("DROP TABLE IF EXISTS substation_snapshots")
    op.execute("DROP INDEX IF EXISTS ix_ingestion_runs_dataset_hash")
    op.execute('ALTER TABLE ingestion_runs DROP COLUMN IF EXISTS "metadata"')
    op.execute("ALTER TABLE ingestion_runs DROP COLUMN IF EXISTS snapshot_created")
    op.execute("ALTER TABLE ingestion_runs DROP COLUMN IF EXISTS dataset_hash")
