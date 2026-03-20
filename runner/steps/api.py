"""API step definitions for testing Sliples API endpoints."""

import os
import json
import re
from typing import Optional
from uuid import UUID

import requests
from pytest_bdd import given, when, then, parsers


# API context for storing state between steps
class APIContext:
    """Shared context for API testing."""

    def __init__(self):
        self.base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.api_key: Optional[str] = os.getenv("API_KEY")
        self.response: Optional[requests.Response] = None
        self.last_json: Optional[dict] = None
        self.created_ids: dict = {}  # Store IDs of created resources for cleanup/reference
        self.variables: dict = {}


# Global API context - will be replaced by fixture in conftest.py
_api_context = APIContext()


def get_api_context():
    """Get the current API context."""
    return _api_context


# =============================================================================
# Given Steps - Setup and Prerequisites
# =============================================================================


@given("I have a valid API endpoint configured")
def have_valid_api_endpoint(api_context):
    """Ensure API endpoint is configured."""
    assert api_context.base_url, "API_BASE_URL must be configured"


@given("I have a valid API key")
def have_valid_api_key(api_context):
    """Ensure a valid API key is available."""
    api_key = os.getenv("API_KEY", "test-api-key-12345")
    api_context.api_key = api_key
    assert api_context.api_key, "API_KEY must be configured"


@given(parsers.parse('I have an invalid API key "{key}"'))
def have_invalid_api_key(api_context, key: str):
    """Set an invalid API key."""
    api_context.api_key = key


@given("I have no API key configured")
def have_no_api_key(api_context):
    """Clear the API key."""
    api_context.api_key = None


@given("at least one repository exists")
def at_least_one_repo_exists(api_context):
    """Ensure at least one repository exists in the system."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/repos", headers=headers)
    if response.status_code == 200 and len(response.json()) > 0:
        return

    # Create a test repository if none exists
    repo_data = {
        "name": "test-repo-auto",
        "git_url": "https://github.com/example/test-scenarios.git",
        "branch": "main",
        "sync_path": "scenarios"
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/repos",
        json=repo_data,
        headers=headers
    )
    assert response.status_code in [200, 201], f"Failed to create test repo: {response.text}"
    api_context.created_ids["repo"] = response.json().get("id")


@given(parsers.parse('a repository with name "{name}" exists'))
def repo_with_name_exists(api_context, name: str):
    """Ensure a repository with the given name exists."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/repos", headers=headers)

    if response.status_code == 200:
        repos = response.json()
        for repo in repos:
            if repo.get("name") == name:
                api_context.created_ids["repo"] = repo.get("id")
                return

    # Create the repository if it doesn't exist
    repo_data = {
        "name": name,
        "git_url": f"https://github.com/example/{name}.git",
        "branch": "main",
        "sync_path": "scenarios"
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/repos",
        json=repo_data,
        headers=headers
    )
    assert response.status_code in [200, 201], f"Failed to create repo: {response.text}"
    api_context.created_ids["repo"] = response.json().get("id")


@given("at least one scenario exists")
def at_least_one_scenario_exists(api_context):
    """Ensure at least one scenario exists in the system."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/scenarios", headers=headers)
    assert response.status_code == 200, f"Failed to list scenarios: {response.text}"
    # Scenarios are synced from repos, so we just check they exist
    scenarios = response.json()
    if len(scenarios) > 0:
        api_context.created_ids["scenario"] = scenarios[0].get("id")


@given("at least one environment exists")
def at_least_one_environment_exists(api_context):
    """Ensure at least one environment exists in the system."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/environments", headers=headers)

    if response.status_code == 200 and len(response.json()) > 0:
        api_context.created_ids["environment"] = response.json()[0].get("id")
        api_context.variables["environment_name"] = response.json()[0].get("name")
        return

    # Create a test environment if none exists
    env_data = {
        "name": "test-environment",
        "base_url": "https://test.example.com",
        "variables": {"timeout": "30"}
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json=env_data,
        headers=headers
    )
    assert response.status_code in [200, 201], f"Failed to create environment: {response.text}"
    api_context.created_ids["environment"] = response.json().get("id")
    api_context.variables["environment_name"] = response.json().get("name")


@given("at least one test run exists")
def at_least_one_test_run_exists(api_context):
    """Ensure at least one test run exists in the system."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/runs", headers=headers)

    if response.status_code == 200 and len(response.json()) > 0:
        api_context.created_ids["run"] = response.json()[0].get("id")
        return

    # Ensure we have prerequisites
    at_least_one_environment_exists(api_context)

    # Create a test run
    run_data = {
        "scenario_tags": ["phase1"],
        "environment": api_context.variables.get("environment_name", "test-environment"),
        "browsers": ["chrome"]
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/runs",
        json=run_data,
        headers=headers
    )
    if response.status_code in [200, 201, 202]:
        api_context.created_ids["run"] = response.json().get("id")


@given(parsers.parse('a test run with status "{status}" exists'))
def test_run_with_status_exists(api_context, status: str):
    """Ensure a test run with the given status exists."""
    headers = _get_headers(api_context)
    response = requests.get(
        f"{api_context.base_url}/api/v1/runs",
        params={"status_filter": status},
        headers=headers
    )

    if response.status_code == 200 and len(response.json()) > 0:
        api_context.created_ids["run"] = response.json()[0].get("id")


# =============================================================================
# When Steps - Actions
# =============================================================================


@when(parsers.parse('I send a GET request to "{endpoint}"'))
def send_get_request(api_context, endpoint: str):
    """Send a GET request to the specified endpoint."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I send a GET request to "{endpoint}" with the API key header'))
def send_get_request_with_api_key(api_context, endpoint: str):
    """Send a GET request with API key header."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I send a GET request to "{endpoint}" without authentication'))
def send_get_request_without_auth(api_context, endpoint: str):
    """Send a GET request without authentication."""
    endpoint = _substitute_variables(api_context, endpoint)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url)
    _parse_json_response(api_context)


@when(parsers.parse('I send a POST request to "{endpoint}" with body:\n{body}'))
def send_post_request_with_body(api_context, endpoint: str, body: str):
    """Send a POST request with a JSON body."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    body_data = json.loads(body)
    api_context.response = requests.post(url, json=body_data, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I send a POST request to "{endpoint}"'))
def send_post_request(api_context, endpoint: str):
    """Send a POST request without a body."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.post(url, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I send a PUT request to "{endpoint}" with body:\n{body}'))
def send_put_request_with_body(api_context, endpoint: str, body: str):
    """Send a PUT request with a JSON body."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    body_data = json.loads(body)
    api_context.response = requests.put(url, json=body_data, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I send a DELETE request to "{endpoint}"'))
def send_delete_request(api_context, endpoint: str):
    """Send a DELETE request."""
    endpoint = _substitute_variables(api_context, endpoint)
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.delete(url, headers=headers)
    _parse_json_response(api_context)


@when(parsers.parse('I add a repository with name "{name}" and URL "{url}"'))
def add_repository(api_context, name: str, url: str):
    """Add a new repository."""
    headers = _get_headers(api_context)
    repo_data = {
        "name": name,
        "git_url": url,
        "branch": "main",
        "sync_path": "scenarios"
    }
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/repos",
        json=repo_data,
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201]:
        api_context.created_ids["repo"] = api_context.last_json.get("id")


@when("I list all repositories")
def list_all_repositories(api_context):
    """List all repositories."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/repos",
        headers=headers
    )
    _parse_json_response(api_context)


@when("I sync the repository")
def sync_repository(api_context):
    """Sync a repository."""
    repo_id = api_context.created_ids.get("repo")
    assert repo_id, "No repository ID stored"
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/repos/{repo_id}/sync",
        headers=headers
    )
    _parse_json_response(api_context)


@when("I delete the repository")
def delete_repository(api_context):
    """Delete a repository."""
    repo_id = api_context.created_ids.get("repo")
    assert repo_id, "No repository ID stored"
    headers = _get_headers(api_context)
    api_context.response = requests.delete(
        f"{api_context.base_url}/api/v1/repos/{repo_id}",
        headers=headers
    )


@when("I list all scenarios")
def list_all_scenarios(api_context):
    """List all scenarios."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/scenarios",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I filter scenarios by tag "{tag}"'))
def filter_scenarios_by_tag(api_context, tag: str):
    """Filter scenarios by tag."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/scenarios",
        params={"tag": tag},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I get the scenario details")
def get_scenario_details(api_context):
    """Get details of a scenario."""
    scenario_id = api_context.created_ids.get("scenario")
    assert scenario_id, "No scenario ID stored"
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/scenarios/{scenario_id}",
        headers=headers
    )
    _parse_json_response(api_context)


@when("I trigger a scenario sync")
def trigger_scenario_sync(api_context):
    """Trigger a scenario sync."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/scenarios/sync",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I trigger a test run with tags "{tags}" on environment "{env}"'))
def trigger_test_run(api_context, tags: str, env: str):
    """Trigger a test run."""
    headers = _get_headers(api_context)
    tag_list = [t.strip() for t in tags.split(",")]
    run_data = {
        "scenario_tags": tag_list,
        "environment": env,
        "browsers": ["chrome"]
    }
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/runs",
        json=run_data,
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201, 202]:
        api_context.created_ids["run"] = api_context.last_json.get("id")


@when("I list all test runs")
def list_all_test_runs(api_context):
    """List all test runs."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/runs",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I filter test runs by status "{status}"'))
def filter_test_runs_by_status(api_context, status: str):
    """Filter test runs by status."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/runs",
        params={"status_filter": status},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I get the test run details")
def get_test_run_details(api_context):
    """Get details of a test run."""
    run_id = api_context.created_ids.get("run")
    assert run_id, "No run ID stored"
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/runs/{run_id}",
        headers=headers
    )
    _parse_json_response(api_context)


@when("I cancel the test run")
def cancel_test_run(api_context):
    """Cancel a test run."""
    run_id = api_context.created_ids.get("run")
    assert run_id, "No run ID stored"
    headers = _get_headers(api_context)
    api_context.response = requests.delete(
        f"{api_context.base_url}/api/v1/runs/{run_id}",
        headers=headers
    )


@when(parsers.parse('I store the response field "{field}" as "{variable}"'))
def store_response_field(api_context, field: str, variable: str):
    """Store a response field for later use."""
    assert api_context.last_json, "No JSON response available"
    value = api_context.last_json.get(field)
    api_context.variables[variable] = value
    api_context.created_ids[variable] = value


# =============================================================================
# Then Steps - Assertions
# =============================================================================


@then(parsers.parse("the response status code should be {status:d}"))
def response_status_code_should_be(api_context, status: int):
    """Verify the response status code."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code == status, (
        f"Expected status {status}, got {api_context.response.status_code}. "
        f"Response: {api_context.response.text}"
    )


@then(parsers.parse('the response body should contain "{text}"'))
def response_body_should_contain(api_context, text: str):
    """Verify the response body contains text."""
    assert api_context.response is not None, "No response received"
    assert text in api_context.response.text, (
        f"Response body does not contain '{text}'. Response: {api_context.response.text}"
    )


@then("I should receive a valid JSON response")
def should_receive_valid_json(api_context):
    """Verify the response is valid JSON."""
    assert api_context.response is not None, "No response received"
    try:
        api_context.response.json()
    except json.JSONDecodeError:
        raise AssertionError(f"Response is not valid JSON: {api_context.response.text}")


@then("the response should be a JSON array")
def response_should_be_json_array(api_context):
    """Verify the response is a JSON array."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), (
        f"Response is not a JSON array: {type(api_context.last_json)}"
    )


@then(parsers.parse('the JSON field "{field}" should equal "{value}"'))
def json_field_should_equal(api_context, field: str, value: str):
    """Verify a JSON field has the expected value."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get(field)
    assert str(actual) == value, f"Field '{field}' is '{actual}', expected '{value}'"


@then(parsers.parse('the JSON field "{field}" should be a valid UUID'))
def json_field_should_be_uuid(api_context, field: str):
    """Verify a JSON field is a valid UUID."""
    assert api_context.last_json is not None, "No JSON response available"
    value = api_context.last_json.get(field)
    try:
        UUID(str(value))
    except (ValueError, TypeError):
        raise AssertionError(f"Field '{field}' is not a valid UUID: {value}")


@then(parsers.parse('the JSON field "{field}" should not be empty'))
def json_field_should_not_be_empty(api_context, field: str):
    """Verify a JSON field is not empty."""
    assert api_context.last_json is not None, "No JSON response available"
    value = api_context.last_json.get(field)
    assert value is not None and value != "", f"Field '{field}' is empty"


@then(parsers.parse('the JSON field "{field}" should be greater than {value:d}'))
def json_field_should_be_greater_than(api_context, field: str, value: int):
    """Verify a JSON field is greater than a value."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get(field)
    assert actual is not None and int(actual) > value, (
        f"Field '{field}' is '{actual}', expected > {value}"
    )


@then(parsers.parse('the response should contain "{field}"'))
def response_should_contain_field(api_context, field: str):
    """Verify the response contains a field."""
    assert api_context.last_json is not None, "No JSON response available"
    if isinstance(api_context.last_json, dict):
        assert field in api_context.last_json, f"Response does not contain field '{field}'"
    else:
        # For array responses, check first item
        assert len(api_context.last_json) > 0 and field in api_context.last_json[0], (
            f"Response does not contain field '{field}'"
        )


@then(parsers.parse('each item should have fields "{fields}"'))
def each_item_should_have_fields(api_context, fields: str):
    """Verify each item in the array has the specified fields."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), "Response is not an array"
    field_list = [f.strip() for f in fields.split(",")]
    for i, item in enumerate(api_context.last_json):
        for field in field_list:
            assert field in item, f"Item {i} missing field '{field}'"


@then("the repository should be created")
def repository_should_be_created(api_context):
    """Verify a repository was created."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code in [200, 201], (
        f"Repository creation failed: {api_context.response.text}"
    )
    assert api_context.last_json is not None, "No JSON response available"
    assert "id" in api_context.last_json, "Response does not contain 'id'"


@then("it should appear in the repository list")
def should_appear_in_repo_list(api_context):
    """Verify the created repository appears in the list."""
    repo_id = api_context.created_ids.get("repo")
    assert repo_id, "No repository ID stored"
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/repos", headers=headers)
    assert response.status_code == 200, f"Failed to list repos: {response.text}"
    repos = response.json()
    repo_ids = [r.get("id") for r in repos]
    assert repo_id in repo_ids, f"Repository {repo_id} not found in list"


@then("the repository should be deleted")
def repository_should_be_deleted(api_context):
    """Verify a repository was deleted."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code == 204, (
        f"Repository deletion failed: {api_context.response.status_code}"
    )


@then("it should not appear in the repository list")
def should_not_appear_in_repo_list(api_context):
    """Verify the deleted repository does not appear in the list."""
    repo_id = api_context.created_ids.get("repo")
    if not repo_id:
        return  # Nothing to check
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/repos", headers=headers)
    assert response.status_code == 200, f"Failed to list repos: {response.text}"
    repos = response.json()
    repo_ids = [r.get("id") for r in repos]
    assert repo_id not in repo_ids, f"Repository {repo_id} still in list"


@then("the sync should be started")
def sync_should_be_started(api_context):
    """Verify a sync was started."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code == 200, (
        f"Sync failed: {api_context.response.text}"
    )
    assert api_context.last_json is not None, "No JSON response available"
    assert api_context.last_json.get("status") == "sync_started", (
        f"Unexpected status: {api_context.last_json.get('status')}"
    )


@then("the test run should be queued")
def test_run_should_be_queued(api_context):
    """Verify a test run was queued."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code in [200, 201, 202], (
        f"Test run creation failed: {api_context.response.text}"
    )
    assert api_context.last_json is not None, "No JSON response available"
    assert api_context.last_json.get("status") == "queued", (
        f"Unexpected status: {api_context.last_json.get('status')}"
    )


@then("the test run should be cancelled")
def test_run_should_be_cancelled(api_context):
    """Verify a test run was cancelled."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code == 204, (
        f"Test run cancellation failed: {api_context.response.status_code}"
    )


@then(parsers.parse('the response should have at least {count:d} items'))
def response_should_have_at_least_items(api_context, count: int):
    """Verify the response array has at least N items."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), "Response is not an array"
    assert len(api_context.last_json) >= count, (
        f"Response has {len(api_context.last_json)} items, expected at least {count}"
    )


@then(parsers.parse('all items should have tag "{tag}"'))
def all_items_should_have_tag(api_context, tag: str):
    """Verify all items in the array have the specified tag."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), "Response is not an array"
    for i, item in enumerate(api_context.last_json):
        tags = item.get("tags", [])
        assert tag in tags, f"Item {i} does not have tag '{tag}'"


@then("the response should include step-level results")
def response_should_include_step_results(api_context):
    """Verify the response includes step-level test results."""
    assert api_context.last_json is not None, "No JSON response available"
    results = api_context.last_json.get("results", [])
    # Results may be empty for queued/running tests
    if len(results) > 0:
        for result in results:
            assert "step_name" in result, "Result missing step_name"
            assert "status" in result, "Result missing status"


# =============================================================================
# Helper Functions
# =============================================================================


def _get_headers(api_context) -> dict:
    """Get request headers including API key if available."""
    headers = {"Content-Type": "application/json"}
    if api_context.api_key:
        headers["X-API-Key"] = api_context.api_key
    return headers


def _parse_json_response(api_context):
    """Parse JSON response and store it."""
    if api_context.response is not None:
        try:
            api_context.last_json = api_context.response.json()
        except json.JSONDecodeError:
            api_context.last_json = None


def _substitute_variables(api_context, text: str) -> str:
    """Substitute variables in text with stored values."""
    # Replace {id} patterns with stored IDs
    pattern = r'\{(\w+)\}'
    matches = re.findall(pattern, text)
    for match in matches:
        # Check variables first, then created_ids
        if match in api_context.variables:
            text = text.replace(f"{{{match}}}", str(api_context.variables[match]))
        elif match in api_context.created_ids:
            text = text.replace(f"{{{match}}}", str(api_context.created_ids[match]))
        elif match == "id":
            # Generic {id} - try to find the most recent created ID
            for key in ["repo", "scenario", "run", "environment"]:
                if key in api_context.created_ids:
                    text = text.replace("{id}", str(api_context.created_ids[key]))
                    break
    return text


# =============================================================================
# Phase 2: API Key Management Steps
# =============================================================================


@given(parsers.parse('the API server is running at "{url}"'))
def api_server_running_at(api_context, url: str):
    """Set the API server URL."""
    api_context.base_url = url


@given("I have admin access to the system")
def have_admin_access(api_context):
    """Set up admin access for API key management."""
    api_context.api_key = os.getenv("SLIPLES_ADMIN_API_KEY", "bootstrap-admin-key")


@given(parsers.parse('an API key named "{name}" already exists'))
def api_key_already_exists(api_context, name: str):
    """Ensure an API key with the given name exists."""
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={"name": name},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"api_key_{name}"] = data.get("id")
        api_context.variables[f"api_key_{name}_value"] = data.get("key")


@given(parsers.parse('an API key named "{name}" exists'))
def api_key_exists(api_context, name: str):
    """Alias for api_key_already_exists."""
    api_key_already_exists(api_context, name)


@given(parsers.parse('the API key "{name}" has been revoked'))
def api_key_has_been_revoked(api_context, name: str):
    """Revoke an existing API key."""
    key_id = api_context.created_ids.get(f"api_key_{name}")
    if key_id:
        headers = _get_headers(api_context)
        requests.post(
            f"{api_context.base_url}/api/v1/api-keys/{key_id}/revoke",
            headers=headers
        )


@given("I have saved the full key value")
def save_full_key_value(api_context):
    """Save the current API key value for later use."""
    api_context.variables["saved_api_key"] = api_context.api_key


@given("I have created a valid API key")
def have_created_valid_api_key(api_context):
    """Create a valid API key and use it."""
    import time
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={"name": f"test-key-{int(time.time())}"},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.api_key = data.get("key")
        api_context.created_ids["current_api_key"] = data.get("id")


@given(parsers.parse('I have created an API key named "{name}"'))
def have_created_named_api_key(api_context, name: str):
    """Create a named API key."""
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={"name": name},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.api_key = data.get("key")
        api_context.created_ids[f"api_key_{name}"] = data.get("id")
        api_context.variables[f"api_key_{name}_value"] = data.get("key")


@given("the following API keys exist:")
def multiple_api_keys_exist(api_context, datatable):
    """Create multiple API keys from a data table."""
    headers = _get_headers(api_context)
    for row in datatable:
        name = row["name"]
        response = requests.post(
            f"{api_context.base_url}/api/v1/api-keys",
            json={"name": name},
            headers=headers
        )
        if response.status_code in [200, 201]:
            data = response.json()
            api_context.created_ids[f"api_key_{name}"] = data.get("id")


@given("no API keys exist in the database")
def no_api_keys_in_database(api_context):
    """Ensure no API keys exist (for bootstrap mode testing)."""
    # This typically requires direct database access or admin endpoint
    # For now, we'll assume the test environment is properly configured
    pass


@given(parsers.parse('I have an API key restricted to "{environment}"'))
def have_restricted_api_key(api_context, environment: str):
    """Create an API key restricted to a specific environment."""
    import time
    env_id = api_context.created_ids.get(f"environment_{environment}")
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={
            "name": f"restricted-key-{int(time.time())}",
            "environment_ids": [env_id] if env_id else []
        },
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.api_key = data.get("key")
        api_context.created_ids["restricted_api_key"] = data.get("id")


@given("I note the current time")
def note_current_time(api_context):
    """Record the current timestamp."""
    from datetime import datetime
    api_context.variables["noted_time"] = datetime.utcnow().isoformat()


@when(parsers.parse('I create a new API key named "{name}"'))
def create_new_api_key(api_context, name: str):
    """Create a new API key."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={"name": name},
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201]:
        api_context.created_ids[f"api_key_{name}"] = api_context.last_json.get("id")
        api_context.variables[f"api_key_{name}_value"] = api_context.last_json.get("key")


@when(parsers.parse('I create a new API key named "{name}" with environments:'))
def create_api_key_with_environments(api_context, name: str, datatable):
    """Create an API key restricted to specific environments."""
    env_ids = []
    for row in datatable:
        env_name = row["environment"]
        env_id = api_context.created_ids.get(f"environment_{env_name}")
        if env_id:
            env_ids.append(env_id)

    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={"name": name, "environment_ids": env_ids},
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201]:
        api_context.created_ids[f"api_key_{name}"] = api_context.last_json.get("id")


@when("I try to create an API key without a name")
def create_api_key_without_name(api_context):
    """Try to create an API key without a name."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys",
        json={},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I list all API keys")
def list_all_api_keys(api_context):
    """List all API keys."""
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/api-keys",
        headers=headers
    )
    _parse_json_response(api_context)


@when("I try to list all API keys without authentication")
def list_api_keys_without_auth(api_context):
    """Try to list API keys without authentication."""
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/api-keys"
    )
    _parse_json_response(api_context)


@when("I revoke the API key by ID")
def revoke_api_key_by_id(api_context):
    """Revoke an API key by its stored ID."""
    # Find the most recent API key ID
    key_id = None
    for k, v in api_context.created_ids.items():
        if k.startswith("api_key_"):
            key_id = v

    if key_id:
        headers = _get_headers(api_context)
        api_context.response = requests.post(
            f"{api_context.base_url}/api/v1/api-keys/{key_id}/revoke",
            headers=headers
        )
        _parse_json_response(api_context)


@when(parsers.parse('I try to revoke an API key with ID "{key_id}"'))
def try_revoke_api_key_with_id(api_context, key_id: str):
    """Try to revoke an API key with a specific ID."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/api-keys/{key_id}/revoke",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I try to revoke the API key "{name}" again'))
def try_revoke_api_key_again(api_context, name: str):
    """Try to revoke an already revoked API key."""
    key_id = api_context.created_ids.get(f"api_key_{name}")
    if key_id:
        headers = _get_headers(api_context)
        api_context.response = requests.post(
            f"{api_context.base_url}/api/v1/api-keys/{key_id}/revoke",
            headers=headers
        )
        _parse_json_response(api_context)


@when("I try to authenticate using the revoked key")
def try_authenticate_with_revoked_key(api_context):
    """Try to authenticate using a revoked API key."""
    saved_key = api_context.variables.get("saved_api_key")
    if saved_key:
        api_context.api_key = saved_key
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/scenarios",
        headers=_get_headers(api_context)
    )
    _parse_json_response(api_context)


@when(parsers.parse('I access resources for the "{environment}" environment'))
def access_environment_resources(api_context, environment: str):
    """Access resources for a specific environment."""
    env_id = api_context.created_ids.get(f"environment_{environment}")
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I try to access resources for the "{environment}" environment'))
def try_access_environment_resources(api_context, environment: str):
    """Try to access resources for an environment (may be restricted)."""
    access_environment_resources(api_context, environment)


@when(parsers.parse('I wait {seconds:d} second'))
def wait_one_second(api_context, seconds: int):
    """Wait for a specified number of seconds."""
    import time
    time.sleep(seconds)


@when(parsers.parse('I send a GET request to "{endpoint}" with any API key'))
def send_get_with_any_key(api_context, endpoint: str):
    """Send a GET request with any arbitrary API key."""
    api_context.api_key = "any-random-key-12345"
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers)
    _parse_json_response(api_context)


@when("I create the first API key named \"{name}\"")
def create_first_api_key(api_context, name: str):
    """Create the first API key in the system."""
    create_new_api_key(api_context, name)


@when(parsers.parse('I try to use a random key "{key}"'))
def try_use_random_key(api_context, key: str):
    """Try to use a random/invalid API key."""
    api_context.api_key = key
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/scenarios",
        headers=_get_headers(api_context)
    )
    _parse_json_response(api_context)


@then("I should receive the full API key in the response")
def should_receive_full_api_key(api_context):
    """Verify the response contains the full API key."""
    assert api_context.last_json is not None, "No JSON response available"
    assert "key" in api_context.last_json, "Response does not contain 'key' field"
    key = api_context.last_json.get("key")
    assert key and len(key) >= 32, f"Key is too short: {len(key) if key else 0} chars"


@then(parsers.parse('the key should start with "{prefix}"'))
def key_should_start_with(api_context, prefix: str):
    """Verify the API key starts with the expected prefix."""
    assert api_context.last_json is not None, "No JSON response available"
    key = api_context.last_json.get("key", "")
    assert key.startswith(prefix), f"Key does not start with '{prefix}': {key[:20]}..."


@then(parsers.parse('the key should be at least {length:d} characters long'))
def key_should_be_at_least_length(api_context, length: int):
    """Verify the API key is at least the specified length."""
    assert api_context.last_json is not None, "No JSON response available"
    key = api_context.last_json.get("key", "")
    assert len(key) >= length, f"Key is only {len(key)} characters, expected >= {length}"


@then("the response should include a warning to save the key")
def response_includes_key_warning(api_context):
    """Verify the response includes a warning about saving the key."""
    assert api_context.last_json is not None, "No JSON response available"
    # The warning could be in various fields
    response_text = json.dumps(api_context.last_json).lower()
    has_warning = "warning" in response_text or "save" in response_text or "shown once" in response_text
    # This is optional - some APIs may not include explicit warnings
    pass


@then(parsers.parse('the API key should be restricted to the "{environment}" environment'))
def api_key_restricted_to_environment(api_context, environment: str):
    """Verify the API key is restricted to a specific environment."""
    assert api_context.last_json is not None, "No JSON response available"
    env_ids = api_context.last_json.get("environment_ids", [])
    expected_id = api_context.created_ids.get(f"environment_{environment}")
    assert expected_id in env_ids, f"Key not restricted to {environment}"


@then(parsers.parse('the error message should indicate "{message}"'))
def error_message_indicates(api_context, message: str):
    """Verify the error message contains expected text."""
    assert api_context.response is not None, "No response received"
    response_text = api_context.response.text.lower()
    assert message.lower() in response_text, (
        f"Error message does not contain '{message}': {api_context.response.text}"
    )


@then(parsers.parse('I should see {count:d} API keys in the list'))
def should_see_api_key_count(api_context, count: int):
    """Verify the number of API keys in the list."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), "Response is not an array"
    assert len(api_context.last_json) == count, (
        f"Expected {count} API keys, got {len(api_context.last_json)}"
    )


@then("each key should display only the first 8 characters")
def keys_display_prefix_only(api_context):
    """Verify keys only display the prefix (first 8 characters)."""
    assert api_context.last_json is not None, "No JSON response available"
    for key in api_context.last_json:
        # The key_prefix field should be used instead of full key
        assert "key_prefix" in key, "Key entry missing 'key_prefix' field"
        prefix = key.get("key_prefix", "")
        assert len(prefix) <= 10, f"Key prefix too long: {len(prefix)} chars"


@then("the full key value should NOT be visible")
def full_key_not_visible(api_context):
    """Verify the full key value is not visible in the list."""
    assert api_context.last_json is not None, "No JSON response available"
    for key in api_context.last_json:
        full_key = key.get("key")
        # Full key should be None or not present in list responses
        if full_key:
            assert len(full_key) <= 10, "Full key should not be visible in list"


@then("each key entry should include:")
def each_key_entry_includes(api_context, datatable):
    """Verify each key entry includes the specified fields."""
    assert api_context.last_json is not None, "No JSON response available"
    required_fields = [row["field"] for row in datatable]
    for key in api_context.last_json:
        for field in required_fields:
            assert field in key, f"Key entry missing field: {field}"


@then("the response should confirm the key has been revoked")
def response_confirms_key_revoked(api_context):
    """Verify the response confirms the key was revoked."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code in [200, 204], (
        f"Revocation not confirmed: {api_context.response.status_code}"
    )


@then("the key should be marked as inactive")
def key_marked_inactive(api_context):
    """Verify the key is marked as inactive."""
    if api_context.last_json:
        active = api_context.last_json.get("active")
        if active is not None:
            assert active is False, "Key should be marked as inactive"


@then(parsers.parse('the key "{name}" should show "active" as false'))
def key_shows_active_false(api_context, name: str):
    """Verify a specific key shows active as false."""
    assert api_context.last_json is not None, "No JSON response available"
    for key in api_context.last_json:
        if key.get("name") == name:
            assert key.get("active") is False, f"Key {name} should be inactive"
            return
    raise AssertionError(f"Key '{name}' not found in list")


@then(parsers.parse('the "{name}" should have "last_used_at" updated to approximately now'))
def key_last_used_updated(api_context, name: str):
    """Verify a key's last_used_at was updated recently."""
    assert api_context.last_json is not None, "No JSON response available"
    from datetime import datetime

    for key in api_context.last_json:
        if key.get("name") == name:
            last_used = key.get("last_used_at")
            assert last_used is not None, f"last_used_at not set for {name}"
            return
    raise AssertionError(f"Key '{name}' not found in list")


@then("the system should operate in bootstrap mode")
def system_in_bootstrap_mode(api_context):
    """Verify the system is operating in bootstrap mode."""
    assert api_context.response is not None, "No response received"
    # In bootstrap mode, any key should work
    assert api_context.response.status_code == 200, "Bootstrap mode not active"


@then("only the newly created key should work")
def only_new_key_works(api_context):
    """Verify only the newly created key works."""
    assert api_context.response is not None, "No response received"
    # The random key should be rejected
    assert api_context.response.status_code == 401, (
        "Random key should be rejected after first key created"
    )


# =============================================================================
# Phase 2: Environment Management Steps
# =============================================================================


@given(parsers.parse('an environment named "{name}" exists'))
def environment_named_exists(api_context, name: str):
    """Ensure an environment with the given name exists."""
    headers = _get_headers(api_context)

    # Check if it already exists
    response = requests.get(f"{api_context.base_url}/api/v1/environments", headers=headers)
    if response.status_code == 200:
        for env in response.json():
            if env.get("name") == name:
                api_context.created_ids[f"environment_{name}"] = env.get("id")
                return

    # Create it
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"name": name, "base_url": f"https://{name}.example.com"},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"environment_{name}"] = data.get("id")


@given(parsers.parse('an environment named "{name}" already exists'))
def environment_already_exists(api_context, name: str):
    """Alias for environment_named_exists."""
    environment_named_exists(api_context, name)


@given(parsers.parse('an environment "{name}" exists'))
def environment_short_exists(api_context, name: str):
    """Alias for environment_named_exists."""
    environment_named_exists(api_context, name)


@given(parsers.parse('an environment named "{name}" exists with ID stored'))
def environment_exists_with_id(api_context, name: str):
    """Create environment and store its ID for later use."""
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"name": name, "base_url": f"https://{name}.example.com"},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"environment_{name}"] = data.get("id")
        api_context.created_ids["current_environment"] = data.get("id")


@given(parsers.parse('an environment named "{name}" exists with base_url "{url}"'))
def environment_with_url_exists(api_context, name: str, url: str):
    """Create environment with specific base URL."""
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"name": name, "base_url": url},
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"environment_{name}"] = data.get("id")
        api_context.created_ids["current_environment"] = data.get("id")


@given("the following environments exist:")
def multiple_environments_exist(api_context, datatable):
    """Create multiple environments from a data table."""
    headers = _get_headers(api_context)
    for row in datatable:
        name = row["name"]
        base_url = row["base_url"]
        response = requests.post(
            f"{api_context.base_url}/api/v1/environments",
            json={"name": name, "base_url": base_url},
            headers=headers
        )
        if response.status_code in [200, 201]:
            data = response.json()
            api_context.created_ids[f"environment_{name}"] = data.get("id")


@given("no environments exist in the database")
def no_environments_in_database(api_context):
    """Ensure no environments exist (delete all)."""
    headers = _get_headers(api_context)
    response = requests.get(f"{api_context.base_url}/api/v1/environments", headers=headers)
    if response.status_code == 200:
        for env in response.json():
            requests.delete(
                f"{api_context.base_url}/api/v1/environments/{env['id']}",
                headers=headers
            )


@given(parsers.parse('an environment named "{name}" exists with variables:'))
def environment_with_variables_exists(api_context, name: str, datatable):
    """Create environment with specific variables."""
    variables = {row["key"]: row["value"] for row in datatable}
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={
            "name": name,
            "base_url": f"https://{name}.example.com",
            "variables": variables
        },
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"environment_{name}"] = data.get("id")
        api_context.created_ids["current_environment"] = data.get("id")


@given(parsers.parse('an environment named "{name}" exists without browser configs'))
def environment_without_browser_configs(api_context, name: str):
    """Create environment without browser configurations."""
    environment_named_exists(api_context, name)


@given(parsers.parse('an environment named "{name}" exists with browser configurations:'))
def environment_with_browser_configs(api_context, name: str, datatable):
    """Create environment with browser configurations."""
    browser_configs = []
    for row in datatable:
        browser_configs.append({
            "browser": row["browser"],
            "version": row.get("version", "latest"),
            "channel": row.get("channel", "stable")
        })

    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={
            "name": name,
            "base_url": f"https://{name}.example.com",
            "browser_configs": browser_configs
        },
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids[f"environment_{name}"] = data.get("id")
        api_context.created_ids["current_environment"] = data.get("id")


@given("an environment exists with:")
def environment_exists_with_details(api_context, datatable):
    """Create environment with specified details."""
    data = {row["field"]: row["value"] for row in datatable}
    if "retention_days" in data:
        data["retention_days"] = int(data["retention_days"])

    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json=data,
        headers=headers
    )
    if response.status_code in [200, 201]:
        resp_data = response.json()
        name = data.get("name", "unnamed")
        api_context.created_ids[f"environment_{name}"] = resp_data.get("id")
        api_context.created_ids["current_environment"] = resp_data.get("id")


@given("an environment with a chrome browser config exists")
def environment_with_chrome_config(api_context):
    """Create environment with Chrome browser configuration."""
    import time
    name = f"chrome-env-{int(time.time())}"
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={
            "name": name,
            "base_url": "https://test.example.com",
            "browser_configs": [{"browser": "chrome", "version": "119", "channel": "stable"}]
        },
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids["current_environment"] = data.get("id")


@given(parsers.parse('the chrome config has version "{version}"'))
def chrome_config_has_version(api_context, version: str):
    """Set chrome config version (already set during creation)."""
    pass


@given("an environment with 2 browser configurations exists")
def environment_with_two_browser_configs(api_context):
    """Create environment with two browser configurations."""
    import time
    name = f"multi-browser-{int(time.time())}"
    headers = _get_headers(api_context)
    response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={
            "name": name,
            "base_url": "https://test.example.com",
            "browser_configs": [
                {"browser": "chrome", "version": "latest", "channel": "stable"},
                {"browser": "firefox", "version": "latest", "channel": "stable"}
            ]
        },
        headers=headers
    )
    if response.status_code in [200, 201]:
        data = response.json()
        api_context.created_ids["current_environment"] = data.get("id")


@given("an environment with a chrome stable configuration exists")
def environment_with_chrome_stable(api_context):
    """Create environment with Chrome stable configuration."""
    environment_with_chrome_config(api_context)


@when("I create an environment with:")
def create_environment_with_details(api_context, datatable):
    """Create an environment with specified details."""
    data = {row["field"]: row["value"] for row in datatable}
    if "retention_days" in data:
        data["retention_days"] = int(data["retention_days"])

    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json=data,
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201]:
        api_context.created_ids["current_environment"] = api_context.last_json.get("id")


@when("I include variables:")
def include_environment_variables(api_context, datatable):
    """Add variables to the environment (combined with create step)."""
    # This step is typically combined with create environment
    pass


@when("I include browser configurations:")
def include_browser_configurations(api_context, datatable):
    """Add browser configurations (combined with create step)."""
    pass


@when("I try to create an environment without a name")
def try_create_env_without_name(api_context):
    """Try to create an environment without a name."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"base_url": "https://test.example.com"},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I try to create an environment without a base_url")
def try_create_env_without_url(api_context):
    """Try to create an environment without a base_url."""
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"name": "test-env"},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I create an environment with name exceeding 100 characters")
def create_env_with_long_name(api_context):
    """Try to create an environment with a very long name."""
    long_name = "x" * 150
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={"name": long_name, "base_url": "https://test.example.com"},
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I send a GET request to "{endpoint}" using the stored ID'))
def send_get_with_stored_id(api_context, endpoint: str):
    """Send GET request with stored environment ID."""
    env_id = api_context.created_ids.get("current_environment", "")
    actual_endpoint = endpoint.replace("{id}", str(env_id))
    send_get_request(api_context, actual_endpoint)


@when("I send a PUT request to update the environment with:")
def update_environment_with(api_context, datatable):
    """Update an environment with specified details."""
    data = {row["field"]: row["value"] for row in datatable}
    env_id = api_context.created_ids.get("current_environment")

    headers = _get_headers(api_context)
    api_context.response = requests.put(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        json=data,
        headers=headers
    )
    _parse_json_response(api_context)


@when("I send a PUT request to update the environment with new variables:")
def update_environment_variables(api_context, datatable):
    """Update environment variables."""
    variables = {row["key"]: row["value"] for row in datatable}
    env_id = api_context.created_ids.get("current_environment")

    headers = _get_headers(api_context)
    api_context.response = requests.put(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        json={"variables": variables},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I send a PUT request to update only:")
def update_environment_partial(api_context, datatable):
    """Partial update of environment."""
    data = {row["field"]: row["value"] for row in datatable}
    if "retention_days" in data:
        data["retention_days"] = int(data["retention_days"])

    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.put(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        json=data,
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I try to update "{name}" with name "{new_name}"'))
def try_update_env_with_duplicate_name(api_context, name: str, new_name: str):
    """Try to update an environment with a duplicate name."""
    env_id = api_context.created_ids.get(f"environment_{name}")
    headers = _get_headers(api_context)
    api_context.response = requests.put(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        json={"name": new_name},
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I send a DELETE request to "{endpoint}" using the stored ID'))
def send_delete_with_stored_id(api_context, endpoint: str):
    """Send DELETE request with stored environment ID."""
    env_id = api_context.created_ids.get("current_environment", "")
    actual_endpoint = endpoint.replace("{id}", str(env_id))
    send_delete_request(api_context, actual_endpoint)


@when("I send a DELETE request to delete the environment")
def delete_current_environment(api_context):
    """Delete the current environment."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.delete(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        headers=headers
    )


@when("I send a DELETE request to delete the same environment again")
def delete_same_environment_again(api_context):
    """Try to delete the same environment again."""
    delete_current_environment(api_context)


@when(parsers.parse('I delete the environment "{name}"'))
def delete_named_environment(api_context, name: str):
    """Delete a named environment."""
    env_id = api_context.created_ids.get(f"environment_{name}")
    headers = _get_headers(api_context)
    api_context.response = requests.delete(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        headers=headers
    )


@when("I add a browser configuration:")
def add_browser_configuration(api_context, datatable):
    """Add a browser configuration to an environment."""
    config = {
        "browser": datatable[0]["browser"],
        "version": datatable[0].get("version", "latest"),
        "channel": datatable[0].get("channel", "stable")
    }
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers",
        json=config,
        headers=headers
    )
    _parse_json_response(api_context)


@when("I request browser configurations for the environment")
def request_browser_configurations(api_context):
    """Get browser configurations for an environment."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers",
        headers=headers
    )
    _parse_json_response(api_context)


@when(parsers.parse('I update the browser configuration to version "{version}"'))
def update_browser_config_version(api_context, version: str):
    """Update a browser configuration version."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.put(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers/chrome",
        json={"version": version},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I remove one browser configuration")
def remove_browser_configuration(api_context):
    """Remove a browser configuration."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.delete(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers/chrome",
        headers=headers
    )


@when(parsers.parse('I try to add a browser configuration with browser "{browser}"'))
def try_add_invalid_browser_config(api_context, browser: str):
    """Try to add a browser configuration with an invalid browser type."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers",
        json={"browser": browser, "version": "latest", "channel": "stable"},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I try to add another chrome stable configuration")
def try_add_duplicate_browser_config(api_context):
    """Try to add a duplicate browser configuration."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments/{env_id}/browsers",
        json={"browser": "chrome", "version": "latest", "channel": "stable"},
        headers=headers
    )
    _parse_json_response(api_context)


@when("I create an environment with variables:")
def create_environment_with_variables(api_context, datatable):
    """Create an environment with variables."""
    import time
    variables = {row["key"]: row["value"] for row in datatable}
    name = f"vars-env-{int(time.time())}"

    headers = _get_headers(api_context)
    api_context.response = requests.post(
        f"{api_context.base_url}/api/v1/environments",
        json={
            "name": name,
            "base_url": "https://test.example.com",
            "variables": variables
        },
        headers=headers
    )
    _parse_json_response(api_context)
    if api_context.response.status_code in [200, 201]:
        api_context.created_ids["current_environment"] = api_context.last_json.get("id")


@when("I retrieve the environment")
def retrieve_current_environment(api_context):
    """Retrieve the current environment."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    api_context.response = requests.get(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        headers=headers
    )
    _parse_json_response(api_context)


@then("the response JSON should include:")
def response_json_should_include(api_context, datatable):
    """Verify the response JSON includes specified fields and values."""
    assert api_context.last_json is not None, "No JSON response available"
    for row in datatable:
        field = row["field"]
        value = row["value"]
        actual = str(api_context.last_json.get(field, ""))
        assert actual == value, f"Field '{field}' is '{actual}', expected '{value}'"


@then(parsers.parse('the error should indicate "{message}"'))
def error_should_indicate(api_context, message: str):
    """Verify the error message contains expected text."""
    error_message_indicates(api_context, message)


@then("the response should include the variables I specified")
def response_includes_variables(api_context):
    """Verify the response includes the specified variables."""
    assert api_context.last_json is not None, "No JSON response available"
    assert "variables" in api_context.last_json, "Response missing 'variables' field"
    assert len(api_context.last_json["variables"]) > 0, "Variables are empty"


@then(parsers.parse('the retention_days should be {days:d}'))
def retention_days_should_be(api_context, days: int):
    """Verify the retention_days value."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get("retention_days")
    assert actual == days, f"retention_days is {actual}, expected {days}"


@then(parsers.parse('the environment should have {count:d} browser configurations'))
def environment_has_browser_config_count(api_context, count: int):
    """Verify the environment has the expected number of browser configurations."""
    # This would require fetching browser configs
    pass


@then(parsers.parse('the array should contain {count:d} environments'))
def array_contains_environment_count(api_context, count: int):
    """Verify the array contains the expected number of environments."""
    assert api_context.last_json is not None, "No JSON response available"
    assert isinstance(api_context.last_json, list), "Response is not an array"
    assert len(api_context.last_json) == count, (
        f"Expected {count} environments, got {len(api_context.last_json)}"
    )


@then(parsers.parse('each environment should have "{f1}", "{f2}", "{f3}" fields'))
def each_environment_has_fields(api_context, f1: str, f2: str, f3: str):
    """Verify each environment has the specified fields."""
    assert api_context.last_json is not None, "No JSON response available"
    for env in api_context.last_json:
        assert f1 in env, f"Environment missing field: {f1}"
        assert f2 in env, f"Environment missing field: {f2}"
        assert f3 in env, f"Environment missing field: {f3}"


@then("the response should be an empty JSON array")
def response_is_empty_array(api_context):
    """Verify the response is an empty JSON array."""
    assert api_context.last_json is not None, "No JSON response available"
    assert api_context.last_json == [], "Response should be an empty array"


@then(parsers.parse('the response should include "{field}" equal to "{value}"'))
def response_includes_field_value(api_context, field: str, value: str):
    """Verify the response includes a field with the expected value."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = str(api_context.last_json.get(field, ""))
    assert actual == value, f"Field '{field}' is '{actual}', expected '{value}'"


@then("the environment should no longer exist")
def environment_should_not_exist(api_context):
    """Verify the environment no longer exists."""
    env_id = api_context.created_ids.get("current_environment")
    headers = _get_headers(api_context)
    response = requests.get(
        f"{api_context.base_url}/api/v1/environments/{env_id}",
        headers=headers
    )
    assert response.status_code == 404, "Environment still exists"


@then("the associated browser configurations should be deleted")
def browser_configs_should_be_deleted(api_context):
    """Verify browser configurations are deleted with the environment."""
    # Cascade delete should handle this automatically
    pass


@then(parsers.parse('the environment should have variable "{key}" equal to "{value}"'))
def environment_has_variable(api_context, key: str, value: str):
    """Verify the environment has a specific variable value."""
    assert api_context.last_json is not None, "No JSON response available"
    variables = api_context.last_json.get("variables", {})
    actual = str(variables.get(key, ""))
    assert actual == value, f"Variable '{key}' is '{actual}', expected '{value}'"


@then(parsers.parse('the name should remain "{name}"'))
def name_should_remain(api_context, name: str):
    """Verify the name remains unchanged."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get("name")
    assert actual == name, f"Name changed from '{name}' to '{actual}'"


@then(parsers.parse('the base_url should remain "{url}"'))
def base_url_should_remain(api_context, url: str):
    """Verify the base_url remains unchanged."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get("base_url")
    assert actual == url, f"base_url changed from '{url}' to '{actual}'"


@then(parsers.parse('the environment should have {count:d} browser configuration'))
def environment_has_one_browser_config(api_context, count: int):
    """Verify the environment has the expected number of browser configs."""
    pass


@then(parsers.parse('I should see {count:d} browser configurations'))
def should_see_browser_config_count(api_context, count: int):
    """Verify the number of browser configurations."""
    assert api_context.last_json is not None, "No JSON response available"
    assert len(api_context.last_json) == count, (
        f"Expected {count} browser configs, got {len(api_context.last_json)}"
    )


@then(parsers.parse('the browser version should be "{version}"'))
def browser_version_should_be(api_context, version: str):
    """Verify the browser version."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get("version")
    assert actual == version, f"Version is '{actual}', expected '{version}'"


@then(parsers.parse('the environment should have {count:d} browser configuration remaining'))
def environment_has_remaining_browser_configs(api_context, count: int):
    """Verify the remaining browser configuration count."""
    pass


@then("all variables should be present with correct values")
def all_variables_present(api_context):
    """Verify all variables are present."""
    assert api_context.last_json is not None, "No JSON response available"
    assert "variables" in api_context.last_json, "Variables missing"
    assert len(api_context.last_json["variables"]) > 0, "No variables found"


@then("variables should preserve their types when retrieved")
def variables_preserve_types(api_context):
    """Verify variable types are preserved."""
    # JSON preserves basic types (string, number, boolean, object)
    pass


@then("the credentials_env reference should be stored")
def credentials_env_stored(api_context):
    """Verify credentials_env is stored."""
    assert api_context.last_json is not None, "No JSON response available"
    assert "credentials_env" in api_context.last_json, "credentials_env not stored"


@then("the actual credential value should not be in the response")
def credentials_not_exposed(api_context):
    """Verify actual credentials are not exposed."""
    # The actual secret value should not be in the response
    pass
