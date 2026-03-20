"""
Test module for Environment Management tests.

This module connects pytest-bdd scenarios from test_environments.feature
to the step definitions in runner/steps/api.py.
"""

import pytest
from pytest_bdd import scenarios

# Import step definitions
from steps import api

# Load all scenarios from the feature file
scenarios("test_environments.feature")


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
    # Clean up environments (in reverse order to handle dependencies)
    for key, value in reversed(list(ctx.created_ids.items())):
        if key.startswith("environment_") or key == "current_environment":
            try:
                requests.delete(
                    f"{ctx.base_url}/api/v1/environments/{value}",
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
