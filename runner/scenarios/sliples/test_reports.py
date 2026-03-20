"""
Test module for Reports and Email Notifications tests.

This module connects pytest-bdd scenarios from test_reports.feature
to the step definitions in runner/steps/api.py.

Phase 3 tests cover:
- HTML report generation after test run completion
- Report content validation (pass/fail counts, screenshots, environment info)
- Report download via API endpoints
- Email notification queuing and content verification
- Celery task verification for email delivery
"""

import pytest
from pytest_bdd import scenarios

# Import step definitions
from steps import api

# Load all scenarios from the feature file
scenarios("test_reports.feature")


@pytest.fixture
def api_context():
    """Create API context for tests."""
    ctx = api.APIContext()
    yield ctx
    # Cleanup created resources after each test
    headers = {"Content-Type": "application/json"}
    if ctx.api_key:
        headers["X-API-Key"] = ctx.api_key

    import requests

    # Clean up test runs
    for key, value in ctx.created_ids.items():
        if key.startswith("run") or key == "run":
            try:
                requests.delete(
                    f"{ctx.base_url}/api/v1/runs/{value}",
                    headers=headers
                )
            except Exception:
                pass

    # Clean up environments
    for key, value in ctx.created_ids.items():
        if key.startswith("environment_"):
            try:
                requests.delete(
                    f"{ctx.base_url}/api/v1/environments/{value}",
                    headers=headers
                )
            except Exception:
                pass

    # Clean up notification configs
    if "notification_config" in ctx.created_ids:
        try:
            requests.delete(
                f"{ctx.base_url}/api/v1/notifications/config",
                headers=headers
            )
        except Exception:
            pass


@pytest.fixture
def datatable():
    """Fixture for data tables in Gherkin scenarios.

    This is a placeholder - pytest-bdd handles data tables automatically.
    """
    return []
