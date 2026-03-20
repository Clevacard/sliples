"""API routes."""

from app.api.routes import (
    auth,
    browsers,
    environments,
    health,
    repos,
    runs,
    scenarios,
    schedules,
    seed,
    steps,
    test_session,
    users,
)

__all__ = [
    "auth",
    "browsers",
    "environments",
    "health",
    "repos",
    "runs",
    "scenarios",
    "schedules",
    "seed",
    "steps",
    "test_session",
    "users",
]
