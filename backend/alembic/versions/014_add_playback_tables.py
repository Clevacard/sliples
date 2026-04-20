"""Add playback_runs and playback_step_results tables

Revision ID: 014_add_playback_tables
Revises: 013_add_event_annotations
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '014_add_playback_tables'
down_revision = '013_add_event_annotations'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'playback_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recording_sessions.id'), nullable=False),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('environments.id'), nullable=False),
        sa.Column('browser', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('viewport_width', sa.Integer, nullable=True),
        sa.Column('viewport_height', sa.Integer, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('finished_at', sa.DateTime, nullable=True),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('progress_message', sa.String(500), nullable=True),
        sa.Column('total_steps', sa.Integer, server_default='0'),
        sa.Column('passed_steps', sa.Integer, server_default='0'),
        sa.Column('failed_steps', sa.Integer, server_default='0'),
        sa.Column('report_html', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'playback_step_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('playback_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('playback_runs.id'), nullable=False),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recorded_events.id'), nullable=False),
        sa.Column('sequence', sa.Integer, nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('duration_ms', sa.Integer, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('selector_used', sa.Text, nullable=True),
        sa.Column('screenshot_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index('ix_playback_runs_session_id', 'playback_runs', ['session_id'])
    op.create_index('ix_playback_step_results_playback_run_id', 'playback_step_results', ['playback_run_id'])


def downgrade():
    op.drop_index('ix_playback_step_results_playback_run_id')
    op.drop_index('ix_playback_runs_session_id')
    op.drop_table('playback_step_results')
    op.drop_table('playback_runs')
