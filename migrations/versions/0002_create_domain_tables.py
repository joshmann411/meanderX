"""create domain tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-01 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('pipeline', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('extracted_count', sa.Integer, server_default='0'),
        sa.Column('valid_count', sa.Integer, server_default='0'),
        sa.Column('loaded_count', sa.Integer, server_default='0'),
        sa.Column('rejected_count', sa.Integer, server_default='0'),
        sa.Column('error', sa.String(), nullable=True),
    )

    op.create_table(
        'substations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('source_substation_id', sa.String(), nullable=True, index=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.UniqueConstraint('source', 'source_substation_id', name='uq_substations_source_source_id'),
    )

    op.create_table(
        'feeders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('feeder_id', sa.String(), nullable=False, index=True),
        sa.Column('substation_id', sa.Integer, sa.ForeignKey('substations.id'), nullable=True),
        sa.Column('pv_thermal', sa.String(), nullable=True),
        sa.Column('geometry', Geometry(geometry_type='GEOMETRY', srid=4326), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true')),
        sa.UniqueConstraint('source', 'feeder_id', name='uq_feeders_source_feeder_id'),
    )

def downgrade() -> None:
    op.drop_table('feeders')
    op.drop_table('substations')
    op.drop_table('ingestion_runs')
