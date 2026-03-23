"""Add missing columns to test_runs and test_results

Revision ID: 009
Revises: 008
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add progress_message to test_runs
    op.add_column(
        "test_runs",
        sa.Column("progress_message", sa.String(500), nullable=True)
    )

    # Add scenario_name to test_results
    op.add_column(
        "test_results",
        sa.Column("scenario_name", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("test_results", "scenario_name")
    op.drop_column("test_runs", "progress_message")
