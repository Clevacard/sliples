"""Add project_id to all entities and migrate existing data

Revision ID: 006
Revises: 005
Create Date: 2026-03-22

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add project_id columns (nullable initially)
    op.add_column("environments", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("scenario_repos", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("scenarios", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("custom_steps", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("schedules", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("test_runs", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("api_keys", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Step 2: Create "Default Project" and migrate existing data
    conn = op.get_bind()

    # Generate a UUID for the default project
    default_project_id = str(uuid.uuid4())

    # Create the default project
    conn.execute(
        sa.text("""
            INSERT INTO projects (id, name, slug, description, created_at, updated_at)
            VALUES (:id, 'Default Project', 'default', 'Auto-created project for existing data', NOW(), NOW())
            ON CONFLICT (slug) DO NOTHING
        """),
        {"id": default_project_id}
    )

    # Get the actual project ID (in case it already existed)
    result = conn.execute(sa.text("SELECT id FROM projects WHERE slug = 'default'"))
    row = result.fetchone()
    if row:
        default_project_id = str(row[0])

    # Add all existing users as owners of the default project
    conn.execute(
        sa.text("""
            INSERT INTO project_members (id, project_id, user_id, role, created_at)
            SELECT gen_random_uuid(), :project_id, id, 'owner', NOW()
            FROM users
            WHERE NOT EXISTS (
                SELECT 1 FROM project_members
                WHERE project_id = :project_id AND user_id = users.id
            )
        """),
        {"project_id": default_project_id}
    )

    # Step 3: Update all existing entities to reference the default project
    tables = ["environments", "scenario_repos", "scenarios", "custom_steps", "schedules", "test_runs", "api_keys"]
    for table in tables:
        conn.execute(
            sa.text(f"UPDATE {table} SET project_id = :project_id WHERE project_id IS NULL"),
            {"project_id": default_project_id}
        )

    # Step 4: Add foreign key constraints
    op.create_foreign_key(
        "fk_environments_project_id", "environments", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_scenario_repos_project_id", "scenario_repos", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_scenarios_project_id", "scenarios", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_custom_steps_project_id", "custom_steps", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_schedules_project_id", "schedules", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_test_runs_project_id", "test_runs", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_api_keys_project_id", "api_keys", "projects",
        ["project_id"], ["id"], ondelete="CASCADE"
    )

    # Step 5: Create indexes for fast lookups
    op.create_index("ix_environments_project_id", "environments", ["project_id"])
    op.create_index("ix_scenario_repos_project_id", "scenario_repos", ["project_id"])
    op.create_index("ix_scenarios_project_id", "scenarios", ["project_id"])
    op.create_index("ix_custom_steps_project_id", "custom_steps", ["project_id"])
    op.create_index("ix_schedules_project_id", "schedules", ["project_id"])
    op.create_index("ix_test_runs_project_id", "test_runs", ["project_id"])
    op.create_index("ix_api_keys_project_id", "api_keys", ["project_id"])

    # Step 6: Drop old unique constraint on environments.name and add project-scoped one
    op.drop_constraint("environments_name_key", "environments", type_="unique")
    op.create_unique_constraint("uq_environments_project_name", "environments", ["project_id", "name"])

    # Drop old unique constraint on scenario_repos.name and add project-scoped one
    op.drop_constraint("scenario_repos_name_key", "scenario_repos", type_="unique")
    op.create_unique_constraint("uq_scenario_repos_project_name", "scenario_repos", ["project_id", "name"])


def downgrade() -> None:
    # Remove project-scoped unique constraints and restore original ones
    op.drop_constraint("uq_scenario_repos_project_name", "scenario_repos", type_="unique")
    op.create_unique_constraint("scenario_repos_name_key", "scenario_repos", ["name"])

    op.drop_constraint("uq_environments_project_name", "environments", type_="unique")
    op.create_unique_constraint("environments_name_key", "environments", ["name"])

    # Drop indexes
    op.drop_index("ix_api_keys_project_id")
    op.drop_index("ix_test_runs_project_id")
    op.drop_index("ix_schedules_project_id")
    op.drop_index("ix_custom_steps_project_id")
    op.drop_index("ix_scenarios_project_id")
    op.drop_index("ix_scenario_repos_project_id")
    op.drop_index("ix_environments_project_id")

    # Drop foreign key constraints
    op.drop_constraint("fk_api_keys_project_id", "api_keys", type_="foreignkey")
    op.drop_constraint("fk_test_runs_project_id", "test_runs", type_="foreignkey")
    op.drop_constraint("fk_schedules_project_id", "schedules", type_="foreignkey")
    op.drop_constraint("fk_custom_steps_project_id", "custom_steps", type_="foreignkey")
    op.drop_constraint("fk_scenarios_project_id", "scenarios", type_="foreignkey")
    op.drop_constraint("fk_scenario_repos_project_id", "scenario_repos", type_="foreignkey")
    op.drop_constraint("fk_environments_project_id", "environments", type_="foreignkey")

    # Drop project_id columns
    op.drop_column("api_keys", "project_id")
    op.drop_column("test_runs", "project_id")
    op.drop_column("schedules", "project_id")
    op.drop_column("custom_steps", "project_id")
    op.drop_column("scenarios", "project_id")
    op.drop_column("scenario_repos", "project_id")
    op.drop_column("environments", "project_id")
