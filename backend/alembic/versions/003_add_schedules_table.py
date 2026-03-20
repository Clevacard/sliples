"""Add schedules table for test run scheduling

Revision ID: 003
Revises: 002
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schedules table for cron-like test run scheduling
    op.create_table(
        "schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),

        # What to run
        sa.Column("scenario_tags", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("scenario_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default="{}"),

        # Where and how to run
        sa.Column(
            "environment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("environments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("browsers", postgresql.ARRAY(sa.String), server_default="{chromium}"),

        # Status
        sa.Column("enabled", sa.Boolean, default=True, nullable=False),

        # Tracking
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("last_run_at", sa.DateTime, nullable=True),
        sa.Column("next_run_at", sa.DateTime, nullable=True),
        sa.Column("last_run_id", postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # Indexes for fast lookups
    op.create_index("ix_schedules_environment_id", "schedules", ["environment_id"])
    op.create_index("ix_schedules_enabled", "schedules", ["enabled"])
    op.create_index("ix_schedules_next_run_at", "schedules", ["next_run_at"])


def downgrade() -> None:
    op.drop_index("ix_schedules_next_run_at")
    op.drop_index("ix_schedules_enabled")
    op.drop_index("ix_schedules_environment_id")
    op.drop_table("schedules")
