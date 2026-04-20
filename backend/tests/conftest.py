"""Shared test fixtures for the Sliples backend test suite.

Works both locally (docker-compose) and in OpenShift (DATABASE_URL env var).
"""

import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base
from app.models import (
    Environment,
    Project,
    RunStatus,
    Scenario,
    Schedule,
    TestRun,
)

# ---------------------------------------------------------------------------
# Database URL resolution
# ---------------------------------------------------------------------------
# 1. DATABASE_URL env var (OpenShift / CI)
# 2. TEST_DATABASE_URL env var (explicit override)
# 3. Fallback to docker-compose default on port 5433 with _test suffix
_DEFAULT_DB_URL = "postgresql://sliples:sliples_dev@localhost:5433/sliples_test"
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", _DEFAULT_DB_URL),
)


# ---------------------------------------------------------------------------
# Engine / session scoped to the test session
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for the test database."""
    eng = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def tables(engine):
    """Create all tables before the first test, drop after the last."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(engine, tables) -> Session:
    """Provide a transactional database session that rolls back after each test.

    This ensures every test starts with a clean slate without having to
    recreate the schema each time.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# Domain object factories
# ---------------------------------------------------------------------------
@pytest.fixture()
def make_project(db: Session):
    """Factory fixture: create and persist a Project."""

    def _make(
        name: str = "Test Project",
        slug: str | None = None,
        description: str = "Auto-created for tests",
    ) -> Project:
        slug = slug or f"test-project-{uuid.uuid4().hex[:8]}"
        project = Project(
            name=name,
            slug=slug,
            description=description,
        )
        db.add(project)
        db.flush()
        return project

    return _make


@pytest.fixture()
def make_environment(db: Session):
    """Factory fixture: create and persist an Environment."""

    def _make(
        project: Project | None = None,
        name: str = "test-env",
        base_url: str = "https://test.example.com",
    ) -> Environment:
        env = Environment(
            project_id=project.id if project else None,
            name=name,
            base_url=base_url,
        )
        db.add(env)
        db.flush()
        return env

    return _make


@pytest.fixture()
def make_scenario(db: Session):
    """Factory fixture: create and persist a Scenario."""

    def _make(
        project: Project | None = None,
        name: str = "Login scenario",
        feature_path: str = "features/login.feature",
        content: str = "Feature: Login\n  Scenario: Success\n    Given I am on the login page",
        tags: list[str] | None = None,
    ) -> Scenario:
        scenario = Scenario(
            project_id=project.id if project else None,
            name=name,
            feature_path=feature_path,
            content=content,
            tags=tags or [],
        )
        db.add(scenario)
        db.flush()
        return scenario

    return _make


@pytest.fixture()
def make_schedule(db: Session):
    """Factory fixture: create and persist a Schedule."""

    def _make(
        project: Project | None = None,
        name: str = "Nightly regression",
        cron_expression: str = "0 0 * * *",
        timezone: str = "UTC",
        enabled: bool = True,
        scenario_ids: list | None = None,
        scenario_tags: list[str] | None = None,
        environment_ids: list | None = None,
        browsers: list[str] | None = None,
        next_run_at: datetime | None = None,
        last_run_at: datetime | None = None,
    ) -> Schedule:
        schedule = Schedule(
            project_id=project.id if project else None,
            name=name,
            cron_expression=cron_expression,
            timezone=timezone,
            enabled=enabled,
            scenario_ids=scenario_ids or [],
            scenario_tags=scenario_tags or [],
            environment_ids=environment_ids or [],
            browsers=browsers or ["chromium"],
            next_run_at=next_run_at,
            last_run_at=last_run_at,
        )
        db.add(schedule)
        db.flush()
        return schedule

    return _make


# ---------------------------------------------------------------------------
# Celery task mocks
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_execute_scheduled_run():
    """Patch execute_scheduled_run.delay() so check_scheduled_runs doesn't
    actually fire a Celery task."""
    from unittest.mock import patch, MagicMock

    with patch("app.workers.scheduled.execute_scheduled_run") as mock_task:
        mock_task.delay = MagicMock()
        yield mock_task


@pytest.fixture()
def mock_execute_test_run():
    """Patch execute_test_run.delay() so execute_scheduled_run doesn't
    actually fire a browser test."""
    from unittest.mock import patch, MagicMock

    with patch("app.workers.tasks.execute_test_run") as mock_task:
        mock_task.delay = MagicMock()
        yield mock_task
