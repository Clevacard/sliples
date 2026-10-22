"""Smoke tests run by the release pipeline against Postgres and Redis sidecars.

They catch what unit tests would not: a dependency bump that breaks the DB
driver, an app that no longer imports, or a migration chain that no longer
applies to an empty database.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from tests.conftest import TEST_DATABASE_URL

BACKEND_DIR = Path(__file__).resolve().parent.parent


def test_health_endpoint_reports_connected_dependencies():
    from app.main import app

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "connected", body
    assert body["redis"] == "connected", body


def test_migrations_apply_to_empty_database():
    """`alembic upgrade head` is what the deploy stage runs before the rollout."""
    url = make_url(TEST_DATABASE_URL)
    scratch = f"{url.database}_migrate"

    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{scratch}"'))
        conn.execute(text(f'CREATE DATABASE "{scratch}"'))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=BACKEND_DIR,
            env={**os.environ, "DATABASE_URL": url.set(database=scratch).render_as_string(hide_password=False)},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr[-2000:]
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{scratch}" WITH (FORCE)'))
        admin.dispose()
