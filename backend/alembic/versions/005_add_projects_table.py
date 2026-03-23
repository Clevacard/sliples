"""Add projects and project_members tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project role enum (if not exists for idempotency)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE projectrole AS ENUM ('owner', 'admin', 'member', 'viewer');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Projects table - top-level organizational unit
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Project members association table
    op.create_table(
        "project_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM("owner", "admin", "member", "viewer", name="projectrole", create_type=False),
            default="member",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    # Indexes for fast lookups
    op.create_index("ix_projects_slug", "projects", ["slug"], unique=True)
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_members_user_id")
    op.drop_index("ix_project_members_project_id")
    op.drop_index("ix_projects_slug")
    op.drop_table("project_members")
    op.drop_table("projects")
    op.execute("DROP TYPE IF EXISTS projectrole")
