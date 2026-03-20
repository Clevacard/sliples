"""Add test_sessions table for interactive testing.

Revision ID: 004
Revises: 003
Create Date: 2026-03-20 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create session status enum
    session_status_enum = postgresql.ENUM(
        'active', 'paused', 'completed', 'terminated',
        name='sessionstatus',
        create_type=False,
    )
    session_status_enum.create(op.get_bind(), checkfirst=True)

    # Create test_sessions table
    op.create_table(
        'test_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('environment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', 'terminated', name='sessionstatus'), nullable=True),
        sa.Column('browser_type', sa.String(50), nullable=True, server_default='chromium'),
        sa.Column('current_step_index', sa.String(50), nullable=True, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('last_activity', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('step_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]'),
        sa.Column('current_url', sa.String(2000), nullable=True),
        sa.Column('current_title', sa.String(500), nullable=True),
        sa.Column('last_screenshot_url', sa.String(500), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes
    op.create_index('ix_test_sessions_user_id', 'test_sessions', ['user_id'])
    op.create_index('ix_test_sessions_environment_id', 'test_sessions', ['environment_id'])
    op.create_index('ix_test_sessions_status', 'test_sessions', ['status'])
    op.create_index('ix_test_sessions_started_at', 'test_sessions', ['started_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_test_sessions_started_at', table_name='test_sessions')
    op.drop_index('ix_test_sessions_status', table_name='test_sessions')
    op.drop_index('ix_test_sessions_environment_id', table_name='test_sessions')
    op.drop_index('ix_test_sessions_user_id', table_name='test_sessions')

    # Drop table
    op.drop_table('test_sessions')

    # Drop enum type
    sa.Enum(name='sessionstatus').drop(op.get_bind(), checkfirst=True)
