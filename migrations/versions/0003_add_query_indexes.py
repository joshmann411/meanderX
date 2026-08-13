"""add query indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-01-01 00:20:00.000000
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_feeders_substation_id", "feeders", ["substation_id"])
    op.create_index("ix_feed_feeder_source_active", "feeders", ["source", "feeder_id", "active"])
    op.create_index("ix_feed_feeders_geometry_gist", "feeders", ["geometry"], postgresql_using="gist")
    op.create_index("ix_feed_substations_geometry_gist", "substations", ["geometry"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("ix_feed_substations_geometry_gist", table_name="substations", postgresql_using="gist")
    op.drop_index("ix_feed_feeders_geometry_gist", table_name="feeders", postgresql_using="gist")
    op.drop_index("ix_feed_feeder_source_active", table_name="feeders")
    op.drop_index("ix_feeders_substation_id", table_name="feeders")
