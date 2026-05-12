"""Add allowed_domains table and domain/client_ip to recording_sessions

Revision ID: 016_add_allowed_domains_and_session_fields
Revises: 015_add_failure_diagnostics
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = '016_allowed_domains'
down_revision = '015_add_failure_diagnostics'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'allowed_domains',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('is_enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_allowed_domains_domain', 'allowed_domains', ['domain'])
    op.create_index('ix_allowed_domains_project_id', 'allowed_domains', ['project_id'])

    op.add_column('recording_sessions', sa.Column('domain', sa.String(255), nullable=True))
    op.add_column('recording_sessions', sa.Column('client_ip', sa.String(45), nullable=True))


def downgrade():
    op.drop_column('recording_sessions', 'client_ip')
    op.drop_column('recording_sessions', 'domain')
    op.drop_index('ix_allowed_domains_project_id', 'allowed_domains')
    op.drop_index('ix_allowed_domains_domain', 'allowed_domains')
    op.drop_table('allowed_domains')
