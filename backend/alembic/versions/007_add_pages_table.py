"""Add pages and page_environment_overrides tables.

Revision ID: 007
Revises: 006
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create pages table
    op.create_table(
        'pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('project_id', 'name', name='uq_page_project_name'),
    )
    op.create_index('ix_pages_project_id', 'pages', ['project_id'])

    # Create page_environment_overrides table
    op.create_table(
        'page_environment_overrides',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('page_id', UUID(as_uuid=True), sa.ForeignKey('pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('environment_id', UUID(as_uuid=True), sa.ForeignKey('environments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('page_id', 'environment_id', name='uq_page_env_override'),
    )
    op.create_index('ix_page_overrides_page_id', 'page_environment_overrides', ['page_id'])
    op.create_index('ix_page_overrides_environment_id', 'page_environment_overrides', ['environment_id'])


def downgrade() -> None:
    op.drop_table('page_environment_overrides')
    op.drop_table('pages')
