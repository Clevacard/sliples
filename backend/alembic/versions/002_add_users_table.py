"""Add users table for Google Workspace SSO

Revision ID: 002
Revises: 001
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table for Google Workspace SSO authentication
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("picture_url", sa.String(500), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=False, unique=True),
        sa.Column("workspace_domain", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "user", name="userrole"),
            default="user",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("last_login", sa.DateTime, nullable=True),
    )

    # Indexes for fast lookups
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)
    op.create_index("ix_users_workspace_domain", "users", ["workspace_domain"])


def downgrade() -> None:
    op.drop_index("ix_users_workspace_domain")
    op.drop_index("ix_users_google_id")
    op.drop_index("ix_users_email")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS userrole")
