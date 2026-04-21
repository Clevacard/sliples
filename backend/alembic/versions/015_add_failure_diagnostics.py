"""Add failure diagnostics fields to test results and playback steps

Revision ID: 015_add_failure_diagnostics
Revises: 014_add_playback_tables
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa


revision = '015_add_failure_diagnostics'
down_revision = '014_add_playback_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add diagnostic fields to test_results
    op.add_column('test_results', sa.Column('console_logs', sa.Text, nullable=True))
    op.add_column('test_results', sa.Column('dom_snapshot_url', sa.String(500), nullable=True))
    op.add_column('test_results', sa.Column('page_url', sa.Text, nullable=True))

    # Add diagnostic fields to playback_step_results
    op.add_column('playback_step_results', sa.Column('console_logs', sa.Text, nullable=True))
    op.add_column('playback_step_results', sa.Column('dom_snapshot_url', sa.String(500), nullable=True))
    op.add_column('playback_step_results', sa.Column('page_url', sa.Text, nullable=True))


def downgrade():
    op.drop_column('playback_step_results', 'page_url')
    op.drop_column('playback_step_results', 'dom_snapshot_url')
    op.drop_column('playback_step_results', 'console_logs')

    op.drop_column('test_results', 'page_url')
    op.drop_column('test_results', 'dom_snapshot_url')
    op.drop_column('test_results', 'console_logs')
