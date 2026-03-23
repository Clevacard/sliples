"""add_locale_timezone_to_environment

Revision ID: ed0c23bfddfb
Revises: 007
Create Date: 2026-03-23 13:31:44.342618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ed0c23bfddfb'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('environments', sa.Column('locale', sa.String(length=20), nullable=True, server_default='en-GB'))
    op.add_column('environments', sa.Column('timezone_id', sa.String(length=50), nullable=True, server_default='Europe/London'))


def downgrade() -> None:
    op.drop_column('environments', 'timezone_id')
    op.drop_column('environments', 'locale')
