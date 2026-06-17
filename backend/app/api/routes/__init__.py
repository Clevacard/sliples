"""API routes."""

from app.api.routes import (
    auth,
    browsers,
    environments,
    health,
    recorder,
    repos,
    runs,
    scenarios,
    schedules,
    seed,
    steps,
    stream,
    test_session,
    users,
)

__all__ = [
    "auth",
    "browsers",
    "environments",
    "health",
    "recorder",
    "repos",
    "runs",
    "scenarios",
    "schedules",
    "seed",
    "steps",
    "stream",
    "test_session",
    "users",
]
