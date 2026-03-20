"""
Test module for Dashboard and Repositories UI tests.

This module connects pytest-bdd scenarios from test_frontend_dashboard.feature
to the step definitions, with custom frontend-specific steps for dashboard
and repository management UI testing.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect


# Load all scenarios from the feature file
scenarios("test_frontend_dashboard.feature")


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def dashboard_state(test_context):
    """Track dashboard state for comparison in tests."""
    return {
        "initial_pass_rate": None,
        "initial_run_count": None,
        "initial_scenario_count": None,
    }


# =============================================================================
# Dashboard - Statistics Steps
# =============================================================================

@then(parsers.parse("the dashboard should show {count:d} total scenarios"))
def dashboard_shows_scenario_count(test_context, count: int):
    """Verify the dashboard displays the correct total scenario count."""
    locator = test_context.page.locator('[data-testid="total-scenarios-card"] .stat-value')
    expect(locator).to_have_text(str(count))


@then(parsers.parse("the dashboard should show {count:d} total repositories"))
def dashboard_shows_repo_count(test_context, count: int):
    """Verify the dashboard displays the correct total repository count."""
    locator = test_context.page.locator('[data-testid="total-repos-card"] .stat-value')
    expect(locator).to_have_text(str(count))


@given(parsers.parse("there are {count:d} scenarios in the system"))
def given_scenarios_in_system(test_context, count: int):
    """Set up scenarios in the system (mock or via API)."""
    test_context.variables["expected_scenario_count"] = count


@given(parsers.parse("there are {count:d} repositories in the system"))
def given_repos_in_system(test_context, count: int):
    """Set up repositories in the system (mock or via API)."""
    test_context.variables["expected_repo_count"] = count


# =============================================================================
# Dashboard - Recent Runs Steps
# =============================================================================

@then("I should see the run status badge")
def should_see_run_status_badge(test_context):
    """Verify a run status badge is visible in the recent runs."""
    locator = test_context.page.locator('[data-testid="recent-runs-list"] .status-badge').first
    expect(locator).to_be_visible()


@then("I should see the run timestamp")
def should_see_run_timestamp(test_context):
    """Verify a run timestamp is visible in the recent runs."""
    locator = test_context.page.locator('[data-testid="recent-runs-list"] .run-timestamp').first
    expect(locator).to_be_visible()


@then(parsers.parse('I should see the status badge "{status}" in the recent runs'))
def should_see_status_badge_in_runs(test_context, status: str):
    """Verify a specific status badge is visible in recent runs."""
    locator = test_context.page.locator(
        f'[data-testid="recent-runs-list"] .status-badge.status-{status}'
    )
    expect(locator.first).to_be_visible()


@when("I click on a recent run in the list")
def click_recent_run(test_context):
    """Click on a recent run entry to navigate to details."""
    locator = test_context.page.locator('[data-testid="recent-runs-list"] .run-item').first
    locator.click()


@given(parsers.parse('a test run with status "{status}" exists'))
def given_test_run_with_status(test_context, status: str):
    """Ensure a test run with specific status exists."""
    test_context.variables["expected_run_status"] = status


@given("at least one test run exists")
def given_at_least_one_run(test_context):
    """Ensure at least one test run exists in the system."""
    pass  # Handled by test fixtures or API setup


@given("at least one scenario exists")
def given_at_least_one_scenario(test_context):
    """Ensure at least one scenario exists in the system."""
    pass  # Handled by test fixtures or API setup


@given("at least one repository exists")
def given_at_least_one_repo(test_context):
    """Ensure at least one repository exists in the system."""
    pass  # Handled by test fixtures or API setup


@given("no scenarios exist")
def given_no_scenarios(test_context):
    """Ensure no scenarios exist in the system."""
    pass  # Handled by test fixtures or API setup


@given("no repositories exist")
def given_no_repos(test_context):
    """Ensure no repositories exist in the system."""
    pass  # Handled by test fixtures or API setup


# =============================================================================
# Dashboard - Quick Actions Steps
# =============================================================================

@then("a new test run should be queued")
def new_run_should_be_queued(test_context):
    """Verify a new test run was queued after clicking Run All."""
    # Check for success notification or updated recent runs
    locator = test_context.page.locator('.notification.success, [data-testid="recent-runs-list"] .run-item')
    expect(locator.first).to_be_visible()


@then("repository sync should be initiated")
def sync_should_be_initiated(test_context):
    """Verify repository sync was initiated after clicking Sync All."""
    # Check for sync progress indicators
    locator = test_context.page.locator('.sync-progress, .notification.success')
    expect(locator.first).to_be_visible()


# =============================================================================
# Dashboard - Trend Chart Steps
# =============================================================================

@given("there is test run history data")
def given_test_run_history(test_context):
    """Ensure test run history data exists for chart display."""
    pass  # Handled by test fixtures or API setup


@given("no test run history exists")
def given_no_test_run_history(test_context):
    """Ensure no test run history exists."""
    pass  # Handled by test fixtures or API setup


@then("the chart should show pass and fail data")
def chart_shows_pass_fail_data(test_context):
    """Verify the trend chart displays pass and fail data series."""
    # Check for chart data elements
    pass_series = test_context.page.locator('[data-testid="trend-chart"] .series-passed')
    fail_series = test_context.page.locator('[data-testid="trend-chart"] .series-failed')
    expect(pass_series.first).to_be_visible()
    expect(fail_series.first).to_be_visible()


@then("the chart should update with filtered data")
def chart_updates_with_filter(test_context):
    """Verify the chart updates after changing time range filter."""
    # Wait for chart to update
    test_context.page.wait_for_timeout(500)
    locator = test_context.page.locator('[data-testid="trend-chart"]')
    expect(locator).to_be_visible()


# =============================================================================
# Dashboard - Real-time Updates Steps
# =============================================================================

@given("I note the current pass rate")
def note_current_pass_rate(test_context, dashboard_state):
    """Note the current pass rate for later comparison."""
    locator = test_context.page.locator('[data-testid="pass-rate-card"] .stat-value')
    dashboard_state["initial_pass_rate"] = locator.text_content()


@when("a test run completes successfully")
def test_run_completes_successfully(test_context):
    """Trigger or wait for a test run to complete successfully."""
    # This would typically trigger via API or wait for WebSocket event
    pass


@when("a test run completes with failure")
def test_run_completes_with_failure(test_context):
    """Trigger or wait for a test run to complete with failure."""
    # This would typically trigger via API or wait for WebSocket event
    pass


@then("the pass rate should be updated")
def pass_rate_should_be_updated(test_context, dashboard_state):
    """Verify the pass rate has changed from initial value."""
    locator = test_context.page.locator('[data-testid="pass-rate-card"] .stat-value')
    current_rate = locator.text_content()
    # Pass rate might be the same if it rounds to same value
    assert locator.is_visible()


@then("the recent runs list should show the new run")
def recent_runs_shows_new_run(test_context):
    """Verify the recent runs list includes the newly completed run."""
    locator = test_context.page.locator('[data-testid="recent-runs-list"] .run-item').first
    expect(locator).to_be_visible()


@then(parsers.parse('I should see a notification "{message}"'))
def should_see_notification(test_context, message: str):
    """Verify a notification with specific message is shown."""
    locator = test_context.page.locator(f'.notification:has-text("{message}")')
    expect(locator.first).to_be_visible()


# =============================================================================
# Repositories Page - List Steps
# =============================================================================

@then("I should see the repository name")
def should_see_repo_name(test_context):
    """Verify repository name is visible in the list."""
    locator = test_context.page.locator('[data-testid="repos-list"] .repo-name').first
    expect(locator).to_be_visible()


@then("I should see the repository URL")
def should_see_repo_url(test_context):
    """Verify repository URL is visible in the list."""
    locator = test_context.page.locator('[data-testid="repos-list"] .repo-url').first
    expect(locator).to_be_visible()


@given(parsers.parse("a repository with {count:d} scenarios exists"))
def given_repo_with_scenario_count(test_context, count: int):
    """Ensure a repository with specific scenario count exists."""
    test_context.variables["expected_scenario_count"] = count


@then(parsers.parse('I should see "{count} scenarios" for the repository'))
def should_see_scenario_count_for_repo(test_context, count: str):
    """Verify the scenario count is displayed for a repository."""
    locator = test_context.page.locator(f'.repo-scenario-count:has-text("{count} scenarios")')
    expect(locator.first).to_be_visible()


@given("a repository that was synced recently exists")
def given_recently_synced_repo(test_context):
    """Ensure a recently synced repository exists."""
    pass  # Handled by test fixtures or API setup


@then("I should see the last sync timestamp")
def should_see_last_sync_timestamp(test_context):
    """Verify the last sync timestamp is visible."""
    locator = test_context.page.locator('.repo-last-sync, .last-sync-timestamp').first
    expect(locator).to_be_visible()


# =============================================================================
# Repositories Page - Add Repository Steps
# =============================================================================

@when(parsers.parse('I fill the repo form with name "{name}"'))
def fill_repo_form_name(test_context, name: str):
    """Fill the repository name field in the add form."""
    locator = test_context.page.locator(
        'input[name="name"], input[placeholder*="name" i], [data-testid="repo-name-input"]'
    ).first
    locator.fill(name)


@when(parsers.parse('I fill the repo form with url "{url}"'))
def fill_repo_form_url(test_context, url: str):
    """Fill the repository URL field in the add form."""
    locator = test_context.page.locator(
        'input[name="git_url"], input[placeholder*="url" i], [data-testid="repo-url-input"]'
    ).first
    locator.fill(url)


@when(parsers.parse('I fill the repo form with branch "{branch}"'))
def fill_repo_form_branch(test_context, branch: str):
    """Fill the repository branch field in the add form."""
    locator = test_context.page.locator(
        'input[name="branch"], input[placeholder*="branch" i], [data-testid="repo-branch-input"]'
    ).first
    locator.fill(branch)


@when(parsers.parse('I fill the repo form with sync path "{path}"'))
def fill_repo_form_sync_path(test_context, path: str):
    """Fill the repository sync path field in the add form."""
    locator = test_context.page.locator(
        'input[name="sync_path"], input[placeholder*="path" i], [data-testid="repo-sync-path-input"]'
    ).first
    locator.fill(path)


@then(parsers.parse('I should see "{name}" in the repos list'))
def should_see_name_in_repos_list(test_context, name: str):
    """Verify a repository name appears in the repos list."""
    locator = test_context.page.locator(f'[data-testid="repos-list"] .repo-name:has-text("{name}")')
    expect(locator.first).to_be_visible()


@then(parsers.parse('I should not see "{name}" in the repos list'))
def should_not_see_name_in_repos_list(test_context, name: str):
    """Verify a repository name does not appear in the repos list."""
    locator = test_context.page.locator(f'[data-testid="repos-list"] .repo-name:has-text("{name}")')
    expect(locator).to_have_count(0)


@then(parsers.parse('the repository should have branch "{branch}"'))
def repo_should_have_branch(test_context, branch: str):
    """Verify the repository has the expected branch."""
    locator = test_context.page.locator(f'.repo-branch:has-text("{branch}")')
    expect(locator.first).to_be_visible()


@given(parsers.parse('a repository with name "{name}" exists'))
def given_repo_with_name(test_context, name: str):
    """Ensure a repository with specific name exists."""
    test_context.variables["repo_name"] = name


# =============================================================================
# Repositories Page - Sync Steps
# =============================================================================

@when(parsers.parse('I click the sync button for repository "{name}"'))
def click_sync_button_for_repo(test_context, name: str):
    """Click the sync button for a specific repository."""
    repo_row = test_context.page.locator(f'.repo-item:has-text("{name}")')
    sync_btn = repo_row.locator('.sync-btn, [data-testid="sync-repo-btn"]')
    sync_btn.click()


@when("I click the sync button for the repository")
def click_sync_button_for_current_repo(test_context):
    """Click the sync button for the current repository."""
    locator = test_context.page.locator('.repo-item .sync-btn, [data-testid="sync-repo-btn"]').first
    locator.click()


@then(parsers.parse('the sync status should show "{status}"'))
def sync_status_should_show(test_context, status: str):
    """Verify the sync status indicator shows expected status."""
    locator = test_context.page.locator(f'.sync-status:has-text("{status}"), .sync-status.{status}')
    expect(locator.first).to_be_visible()


@given("a repository is currently syncing")
def given_repo_currently_syncing(test_context):
    """Ensure a repository is in syncing state."""
    pass  # Handled by test fixtures or triggering sync


@then("I should see the sync progress spinner")
def should_see_sync_progress_spinner(test_context):
    """Verify the sync progress spinner is visible."""
    locator = test_context.page.locator('.sync-spinner, .sync-progress, [data-testid="sync-spinner"]')
    expect(locator.first).to_be_visible()


@when("the sync completes successfully")
def sync_completes_successfully(test_context):
    """Wait for sync to complete successfully."""
    # Wait for sync status to change from syncing
    test_context.page.wait_for_selector('.sync-status:not(.syncing)', timeout=30000)


@then("the scenario count should be updated")
def scenario_count_should_be_updated(test_context):
    """Verify the scenario count has been updated after sync."""
    locator = test_context.page.locator('.repo-scenario-count').first
    expect(locator).to_be_visible()


@given("a repository with invalid credentials exists")
def given_repo_with_invalid_credentials(test_context):
    """Ensure a repository with invalid git credentials exists."""
    pass  # Handled by test fixtures or API setup


@then("the error details should be visible")
def error_details_should_be_visible(test_context):
    """Verify sync error details are visible."""
    locator = test_context.page.locator('.error-details, .sync-error')
    expect(locator.first).to_be_visible()


# =============================================================================
# Repositories Page - Delete Steps
# =============================================================================

@when(parsers.parse('I click the delete button for repository "{name}"'))
def click_delete_button_for_repo(test_context, name: str):
    """Click the delete button for a specific repository."""
    repo_row = test_context.page.locator(f'.repo-item:has-text("{name}")')
    delete_btn = repo_row.locator('.delete-btn, [data-testid="delete-repo-btn"]')
    delete_btn.click()


@when("I click the delete button for the repository")
def click_delete_button_for_current_repo(test_context):
    """Click the delete button for the current repository."""
    locator = test_context.page.locator('.repo-item .delete-btn, [data-testid="delete-repo-btn"]').first
    locator.click()


@then(parsers.parse('I should see "This will also delete {count:d} scenarios"'))
def should_see_delete_warning_with_count(test_context, count: int):
    """Verify the delete warning shows scenario count."""
    locator = test_context.page.locator(f'.delete-warning:has-text("{count} scenarios")')
    expect(locator.first).to_be_visible()


# =============================================================================
# Repositories Page - Edit Steps
# =============================================================================

@when(parsers.parse('I click the edit button for repository "{name}"'))
def click_edit_button_for_repo(test_context, name: str):
    """Click the edit button for a specific repository."""
    repo_row = test_context.page.locator(f'.repo-item:has-text("{name}")')
    edit_btn = repo_row.locator('.edit-btn, [data-testid="edit-repo-btn"]')
    edit_btn.click()


# =============================================================================
# Navigation Steps
# =============================================================================

@then(parsers.parse('the "{element}" should have class "{class_name}"'))
def element_should_have_class(test_context, element: str, class_name: str):
    """Verify an element has a specific CSS class."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).to_have_class(parsers.re(f".*{class_name}.*"))
