"""Add user annotation fields to recorded events

Revision ID: 013
Revises: 012
Create Date: 2026-04-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recorded_events', sa.Column('step_label', sa.Text(), nullable=True))
    op.add_column('recorded_events', sa.Column('should_screenshot', sa.Boolean(), default=False))
    op.add_column('recorded_events', sa.Column('parameters', sa.JSON(), nullable=True))
    op.add_column('recorded_events', sa.Column('notes', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('recorded_events', 'notes')
    op.drop_column('recorded_events', 'parameters')
    op.drop_column('recorded_events', 'should_screenshot')
    op.drop_column('recorded_events', 'step_label')
