"""Convert schedules from single environment_id to multiple environment_ids

Revision ID: 008
Revises: ed0c23bfddfb
Create Date: 2026-03-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "ed0c23bfddfb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new environment_ids array column
    op.add_column(
        "schedules",
        sa.Column(
            "environment_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            server_default="{}",
            nullable=True,
        ),
    )

    # Migrate existing data: copy environment_id into environment_ids array
    op.execute(
        """
        UPDATE schedules
        SET environment_ids = ARRAY[environment_id]
        WHERE environment_id IS NOT NULL
        """
    )

    # Drop the old foreign key constraint and index
    op.drop_constraint("schedules_environment_id_fkey", "schedules", type_="foreignkey")
    op.drop_index("ix_schedules_environment_id", table_name="schedules")

    # Drop the old column
    op.drop_column("schedules", "environment_id")


def downgrade() -> None:
    # Add back the old environment_id column
    op.add_column(
        "schedules",
        sa.Column(
            "environment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # Migrate data back: take first element from environment_ids array
    op.execute(
        """
        UPDATE schedules
        SET environment_id = environment_ids[1]
        WHERE environment_ids IS NOT NULL AND array_length(environment_ids, 1) > 0
        """
    )

    # Create the index
    op.create_index("ix_schedules_environment_id", "schedules", ["environment_id"])

    # Add foreign key constraint back
    op.create_foreign_key(
        "schedules_environment_id_fkey",
        "schedules",
        "environments",
        ["environment_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Drop the new column
    op.drop_column("schedules", "environment_ids")
