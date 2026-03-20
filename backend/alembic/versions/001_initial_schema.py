"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Scenario Repos
    op.create_table(
        "scenario_repos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("git_url", sa.String(500), nullable=False),
        sa.Column("branch", sa.String(100), default="main"),
        sa.Column("sync_path", sa.String(255), default="scenarios"),
        sa.Column("last_synced", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Scenarios
    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_repos.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("feature_path", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String), default=[]),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Environments
    op.create_table(
        "environments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("credentials_env", sa.String(100), nullable=True),
        sa.Column("variables", postgresql.JSON, default={}),
        sa.Column("retention_days", sa.Integer, default=365),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Browser Configs
    op.create_table(
        "browser_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("environment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("environments.id"), nullable=False),
        sa.Column("browser", sa.String(50), nullable=False),
        sa.Column("version", sa.String(50), default="latest"),
        sa.Column("channel", sa.String(50), default="stable"),
    )

    # Test Runs
    op.create_table(
        "test_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scenario_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column("environment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("environments.id"), nullable=False),
        sa.Column("status", sa.String(20), default="queued"),
        sa.Column("browser", sa.String(50), nullable=False),
        sa.Column("browser_version", sa.String(50), default="latest"),
        sa.Column("triggered_by", sa.String(100), nullable=True),
        sa.Column("parallel", sa.Boolean, default=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("report_html", sa.Text, nullable=True),
        sa.Column("email_sent", sa.Boolean, default=False),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # Test Results
    op.create_table(
        "test_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_runs.id"), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("step_name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("duration_ms", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("screenshot_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("environment_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        sa.Column("active", sa.Boolean, default=True),
    )

    # Custom Steps
    op.create_table(
        "custom_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_repos.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("pattern", sa.String(500), nullable=False),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("committed", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_scenarios_tags", "scenarios", ["tags"], postgresql_using="gin")
    op.create_index("ix_test_runs_status", "test_runs", ["status"])
    op.create_index("ix_test_runs_expires_at", "test_runs", ["expires_at"])


def downgrade() -> None:
    op.drop_table("custom_steps")
    op.drop_table("api_keys")
    op.drop_table("test_results")
    op.drop_table("test_runs")
    op.drop_table("browser_configs")
    op.drop_table("environments")
    op.drop_table("scenarios")
    op.drop_table("scenario_repos")
