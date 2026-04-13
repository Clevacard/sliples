"""Add recording_sessions and recorded_events tables

Revision ID: 012
Revises: 011
Create Date: 2026-04-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create recording_sessions table
    op.create_table(
        'recording_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('recording', 'stopped', 'converted', name='recordingstatus'), default='recording'),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('viewport_width', sa.Integer(), nullable=True),
        sa.Column('viewport_height', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('stopped_at', sa.DateTime(), nullable=True),
    )

    # Create recorded_events table
    op.create_table(
        'recorded_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recording_sessions.id'), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),

        # Selectors
        sa.Column('selector_css', sa.Text(), nullable=True),
        sa.Column('selector_xpath', sa.Text(), nullable=True),
        sa.Column('selector_text', sa.Text(), nullable=True),
        sa.Column('selector_test_id', sa.String(255), nullable=True),
        sa.Column('selector_aria', sa.String(255), nullable=True),

        # Element metadata
        sa.Column('tag_name', sa.String(50), nullable=True),
        sa.Column('element_id', sa.String(255), nullable=True),
        sa.Column('element_classes', sa.Text(), nullable=True),
        sa.Column('element_name', sa.String(255), nullable=True),
        sa.Column('element_type', sa.String(50), nullable=True),
        sa.Column('element_role', sa.String(50), nullable=True),
        sa.Column('label_text', sa.Text(), nullable=True),
        sa.Column('placeholder', sa.Text(), nullable=True),

        # Event data
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('coordinates', postgresql.JSON(), nullable=True),
        sa.Column('key_info', postgresql.JSON(), nullable=True),
        sa.Column('extra_data', postgresql.JSON(), nullable=True),
    )

    # Create index for faster event lookups
    op.create_index('ix_recorded_events_session_sequence', 'recorded_events', ['session_id', 'sequence'])


def downgrade() -> None:
    op.drop_index('ix_recorded_events_session_sequence')
    op.drop_table('recorded_events')
    op.drop_table('recording_sessions')
    op.execute('DROP TYPE IF EXISTS recordingstatus')
