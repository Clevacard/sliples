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
    steps,
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
    "steps",
    "users",
]
