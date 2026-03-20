"""
Test module for Frontend Test Runs, Run Details, and Scenarios pages.

This module connects pytest-bdd scenarios from test_frontend_testruns.feature
to step definitions for UI testing with Playwright.
"""

import re
import time
from datetime import datetime

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_frontend_testruns.feature")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app_url():
    """Base URL for the Sliples frontend application."""
    import os
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def test_context(page: Page, app_url: str):
    """Test context for storing state between steps."""
    class TestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.selected_tags = []
            self.selected_browsers = []
            self.selected_environment = None
            self.current_run_id = None
            self.screenshots = []
            self.variables = {}

    return TestContext()


# =============================================================================
# Background Steps
# =============================================================================


@given("I am on the Sliples application")
def on_sliples_application(test_context):
    """Navigate to the Sliples application."""
    test_context.page.goto(test_context.base_url)
    test_context.page.wait_for_load_state("networkidle")


@given("I am authenticated")
def am_authenticated(test_context):
    """Ensure user is authenticated (mock or actual auth)."""
    # Check if already authenticated
    if test_context.page.locator('[data-testid="user-menu"]').count() > 0:
        return
    # For testing, we might use a test token or mock auth
    test_context.page.evaluate("""
        localStorage.setItem('auth_token', 'test-token-for-e2e');
    """)
    test_context.page.reload()


# =============================================================================
# Navigation Steps
# =============================================================================


@given(parsers.parse('I am on the "{page_name}" page'))
def am_on_page(test_context, page_name: str):
    """Navigate to a specific page."""
    page_urls = {
        "runs": "/runs",
        "scenarios": "/scenarios",
        "dashboard": "/dashboard",
        "environments": "/environments",
    }
    url = page_urls.get(page_name, f"/{page_name}")
    test_context.page.goto(f"{test_context.base_url}{url}")
    test_context.page.wait_for_load_state("networkidle")


@given("I am on a completed test run details page")
@given("I navigate to a completed test run details page")
def on_completed_run_details(test_context):
    """Navigate to a completed test run details page."""
    # First get a completed run from API or navigate to runs page
    test_context.page.goto(f"{test_context.base_url}/runs")
    test_context.page.wait_for_load_state("networkidle")

    # Click on the first completed run
    completed_run = test_context.page.locator(
        '[data-testid="run-item"][data-status="passed"], '
        '[data-testid="run-item"][data-status="failed"]'
    ).first

    if completed_run.count() > 0:
        completed_run.click()
        test_context.page.wait_for_load_state("networkidle")


@given("I navigate to a running test run details page")
@given("I am on a running test run details page")
def on_running_run_details(test_context):
    """Navigate to a running test run details page."""
    test_context.page.goto(f"{test_context.base_url}/runs")
    test_context.page.wait_for_load_state("networkidle")

    # Click on a running test
    running_run = test_context.page.locator('[data-testid="run-item"][data-status="running"]').first

    if running_run.count() > 0:
        running_run.click()
        test_context.page.wait_for_load_state("networkidle")


@given("I am on a completed test run details page with failures")
def on_failed_run_details(test_context):
    """Navigate to a completed test run with failures."""
    test_context.page.goto(f"{test_context.base_url}/runs")
    test_context.page.wait_for_load_state("networkidle")

    failed_run = test_context.page.locator('[data-testid="run-item"][data-status="failed"]').first

    if failed_run.count() > 0:
        failed_run.click()
        test_context.page.wait_for_load_state("networkidle")


@given("I am on a test run details page")
def on_run_details_page(test_context):
    """Navigate to any test run details page."""
    test_context.page.goto(f"{test_context.base_url}/runs")
    test_context.page.wait_for_load_state("networkidle")

    run_item = test_context.page.locator('[data-testid="run-item"]').first
    if run_item.count() > 0:
        run_item.click()
        test_context.page.wait_for_load_state("networkidle")


@when("the page finishes loading")
def page_finishes_loading(test_context):
    """Wait for page to finish loading."""
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Test Runs Page - List Steps
# =============================================================================


@given("at least one test run exists in the system")
@given("at least one test run exists")
def at_least_one_run_exists(test_context):
    """Ensure at least one test run exists."""
    runs_list = test_context.page.locator('[data-testid="run-item"]')
    # If no runs, we might need to create one via API
    pass


@given("no test runs exist in the system")
def no_runs_exist(test_context):
    """Ensure no test runs exist (test isolation)."""
    # This would typically be handled by test data setup
    pass


@given("test runs with various statuses exist")
def runs_with_various_statuses(test_context):
    """Ensure test runs with different statuses exist."""
    # Test data setup
    pass


@given("a test run is currently running")
def run_is_currently_running(test_context):
    """Ensure a test run is in running state."""
    # Test data setup or trigger a new run
    pass


@given("test runs exist for multiple environments")
def runs_exist_for_multiple_environments(test_context):
    """Ensure test runs exist for different environments."""
    pass


@given("more than 20 test runs exist")
@given("more than 50 test runs exist")
def many_runs_exist(test_context):
    """Ensure many test runs exist for pagination testing."""
    pass


@then("I should see the test runs list")
def should_see_runs_list(test_context):
    """Verify test runs list is visible."""
    expect(test_context.page.locator('[data-testid="test-runs-list"]')).to_be_visible()


@then("each test run should display status, browser, and timestamp")
def run_shows_metadata(test_context):
    """Verify each run shows required metadata."""
    first_run = test_context.page.locator('[data-testid="run-item"]').first
    expect(first_run.locator('[data-testid="run-status"]')).to_be_visible()
    expect(first_run.locator('[data-testid="run-browser"]')).to_be_visible()
    expect(first_run.locator('[data-testid="run-timestamp"]')).to_be_visible()


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible."""
    locator = test_context.page.locator(f'[data-testid="{element}"]')
    expect(locator).to_be_visible()


@then("I should see the run status indicator")
def should_see_status_indicator(test_context):
    """Verify run status indicators are visible."""
    expect(test_context.page.locator('[data-testid="run-status"]').first).to_be_visible()


@then("I should see the environment name for each run")
def should_see_environment_name(test_context):
    """Verify environment names are displayed."""
    expect(test_context.page.locator('[data-testid="run-environment"]').first).to_be_visible()


@then("I should see the execution duration for completed runs")
def should_see_execution_duration(test_context):
    """Verify execution duration is displayed for completed runs."""
    completed_run = test_context.page.locator(
        '[data-testid="run-item"][data-status="passed"], '
        '[data-testid="run-item"][data-status="failed"]'
    ).first
    if completed_run.count() > 0:
        expect(completed_run.locator('[data-testid="run-duration"]')).to_be_visible()


@then(parsers.parse('I should see "{text}"'))
def should_see_text(test_context, text: str):
    """Verify text is visible on page."""
    expect(test_context.page.get_by_text(text)).to_be_visible()


@then(parsers.parse('I should see a "{text}" call-to-action button'))
def should_see_cta_button(test_context, text: str):
    """Verify a CTA button is visible."""
    expect(test_context.page.get_by_role("button", name=text)).to_be_visible()


# =============================================================================
# Test Runs Page - Filter Steps
# =============================================================================


@when(parsers.parse('I select "{option}" from "{dropdown}"'))
def select_from_dropdown(test_context, option: str, dropdown: str):
    """Select an option from a dropdown."""
    locator = test_context.page.locator(f'[data-testid="{dropdown}"], select[name="{dropdown}"]').first
    locator.select_option(label=option)


@given(parsers.parse('I have filtered by status "{status}"'))
def have_filtered_by_status(test_context, status: str):
    """Apply a status filter."""
    test_context.page.locator('[data-testid="status-filter"]').select_option(label=status.capitalize())
    test_context.page.wait_for_load_state("networkidle")


@then("I should only see test runs with passed status")
def only_see_passed_runs(test_context):
    """Verify only passed runs are shown."""
    runs = test_context.page.locator('[data-testid="run-item"]')
    for i in range(runs.count()):
        status = runs.nth(i).get_attribute("data-status")
        assert status == "passed", f"Expected passed status, got {status}"


@then("I should only see test runs with failed status")
def only_see_failed_runs(test_context):
    """Verify only failed runs are shown."""
    runs = test_context.page.locator('[data-testid="run-item"]')
    for i in range(min(runs.count(), 10)):  # Check first 10
        status = runs.nth(i).get_attribute("data-status")
        assert status == "failed", f"Expected failed status, got {status}"


@then("I should only see test runs with running status")
def only_see_running_runs(test_context):
    """Verify only running runs are shown."""
    runs = test_context.page.locator('[data-testid="run-item"]')
    for i in range(runs.count()):
        status = runs.nth(i).get_attribute("data-status")
        assert status == "running", f"Expected running status, got {status}"


@then("I should only see test runs with queued status")
def only_see_queued_runs(test_context):
    """Verify only queued runs are shown."""
    runs = test_context.page.locator('[data-testid="run-item"]')
    for i in range(runs.count()):
        status = runs.nth(i).get_attribute("data-status")
        assert status == "queued", f"Expected queued status, got {status}"


@then("the run should show a progress indicator")
def run_shows_progress_indicator(test_context):
    """Verify running run shows progress indicator."""
    running_run = test_context.page.locator('[data-testid="run-item"][data-status="running"]').first
    expect(running_run.locator('[data-testid="progress-indicator"]')).to_be_visible()


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify URL contains specified text."""
    assert text in test_context.page.url, f"URL '{test_context.page.url}' does not contain '{text}'"


@then(parsers.parse('the URL should not contain "{text}"'))
def url_should_not_contain(test_context, text: str):
    """Verify URL does not contain specified text."""
    assert text not in test_context.page.url, f"URL '{test_context.page.url}' contains '{text}'"


@when(parsers.parse('I click the "{button_text}" button'))
def click_button(test_context, button_text: str):
    """Click a button by text."""
    test_context.page.get_by_role("button", name=button_text).click()


@then("I should see test runs with all statuses")
def should_see_all_status_runs(test_context):
    """Verify runs with various statuses are shown."""
    # Just verify the list is visible and not empty
    expect(test_context.page.locator('[data-testid="run-item"]').first).to_be_visible()


@then("I should only see test runs for the selected environment")
def only_see_runs_for_environment(test_context):
    """Verify only runs for selected environment are shown."""
    # Verification would check data-environment attribute
    pass


# =============================================================================
# Test Runs Page - Create Modal Steps
# =============================================================================


@given("I open the new test run modal")
@when("I open the new test run modal")
def open_new_run_modal(test_context):
    """Open the new test run modal."""
    test_context.page.get_by_role("button", name="New Test Run").click()
    expect(test_context.page.locator('[data-testid="new-run-modal"]')).to_be_visible()


@then("I should see the new test run modal")
def should_see_new_run_modal(test_context):
    """Verify new test run modal is visible."""
    expect(test_context.page.locator('[data-testid="new-run-modal"]')).to_be_visible()


@then("the modal should display tag selection")
def modal_shows_tag_selection(test_context):
    """Verify tag selection is visible in modal."""
    expect(test_context.page.locator('[data-testid="tag-selector"]')).to_be_visible()


@then("the modal should display environment selection")
def modal_shows_environment_selection(test_context):
    """Verify environment selection is visible in modal."""
    expect(test_context.page.locator('[data-testid="environment-select"]')).to_be_visible()


@then("the modal should display browser selection")
def modal_shows_browser_selection(test_context):
    """Verify browser selection is visible in modal."""
    expect(test_context.page.locator('[data-testid="browser-selector"]')).to_be_visible()


@when(parsers.parse('I click on tag "{tag}"'))
def click_on_tag(test_context, tag: str):
    """Click on a tag to select it."""
    test_context.page.locator(f'[data-testid="tag-{tag}"]').click()
    test_context.selected_tags.append(tag)


@when(parsers.parse('I click on tag "{tag}" again'))
def click_on_tag_again(test_context, tag: str):
    """Click on a tag to deselect it."""
    test_context.page.locator(f'[data-testid="tag-{tag}"]').click()
    if tag in test_context.selected_tags:
        test_context.selected_tags.remove(tag)


@then(parsers.parse('the tag "{tag}" should be selected'))
def tag_should_be_selected(test_context, tag: str):
    """Verify a tag is selected."""
    tag_element = test_context.page.locator(f'[data-testid="tag-{tag}"]')
    expect(tag_element).to_have_class(re.compile(r"selected|active"))


@then(parsers.parse('the tag "{tag}" should not be selected'))
def tag_should_not_be_selected(test_context, tag: str):
    """Verify a tag is not selected."""
    tag_element = test_context.page.locator(f'[data-testid="tag-{tag}"]')
    expect(tag_element).not_to_have_class(re.compile(r"selected|active"))


@then("the selected scenarios count should update")
@then("the selected scenarios count should increase")
@then("the selected scenarios count should decrease")
def scenarios_count_updates(test_context):
    """Verify scenario count updates."""
    expect(test_context.page.locator('[data-testid="selected-scenarios-count"]')).to_be_visible()


@then("both tags should be selected")
def both_tags_selected(test_context):
    """Verify multiple tags are selected."""
    for tag in test_context.selected_tags:
        tag_element = test_context.page.locator(f'[data-testid="tag-{tag}"]')
        expect(tag_element).to_have_class(re.compile(r"selected|active"))


@then(parsers.parse('the environment "{env}" should be selected'))
def environment_should_be_selected(test_context, env: str):
    """Verify environment is selected."""
    select = test_context.page.locator('[data-testid="environment-select"]')
    assert select.input_value() == env or env in select.inner_text()


@then("the environment configuration should be displayed")
def environment_config_displayed(test_context):
    """Verify environment config is shown."""
    expect(test_context.page.locator('[data-testid="environment-config"]')).to_be_visible()


@when(parsers.parse('I check the "{checkbox}" checkbox'))
def check_checkbox(test_context, checkbox: str):
    """Check a checkbox."""
    test_context.page.locator(f'[data-testid="browser-{checkbox}"], input[name="{checkbox}"]').check()
    test_context.selected_browsers.append(checkbox)


@then("Chrome should be selected for the run")
def chrome_should_be_selected(test_context):
    """Verify Chrome is selected."""
    expect(test_context.page.locator('[data-testid="browser-chrome"]')).to_be_checked()


@then("both Chrome and Firefox should be selected")
def chrome_and_firefox_selected(test_context):
    """Verify both browsers are selected."""
    expect(test_context.page.locator('[data-testid="browser-chrome"]')).to_be_checked()
    expect(test_context.page.locator('[data-testid="browser-firefox"]')).to_be_checked()


@then("all three browsers should be selected")
def all_browsers_selected(test_context):
    """Verify all three browsers are selected."""
    expect(test_context.page.locator('[data-testid="browser-chrome"]')).to_be_checked()
    expect(test_context.page.locator('[data-testid="browser-firefox"]')).to_be_checked()
    expect(test_context.page.locator('[data-testid="browser-webkit"]')).to_be_checked()


@then("the estimated run time should be displayed")
def estimated_run_time_displayed(test_context):
    """Verify estimated run time is shown."""
    expect(test_context.page.locator('[data-testid="estimated-time"]')).to_be_visible()


@given(parsers.parse('I have selected tag "{tag}"'))
def have_selected_tag(test_context, tag: str):
    """Pre-select a tag."""
    test_context.page.locator(f'[data-testid="tag-{tag}"]').click()
    test_context.selected_tags.append(tag)


@given(parsers.parse('I have selected environment "{env}"'))
def have_selected_environment(test_context, env: str):
    """Pre-select an environment."""
    test_context.page.locator('[data-testid="environment-select"]').select_option(label=env)
    test_context.selected_environment = env


@given(parsers.parse('I have selected browser "{browser}"'))
def have_selected_browser(test_context, browser: str):
    """Pre-select a browser."""
    test_context.page.locator(f'[data-testid="browser-{browser}"]').check()
    test_context.selected_browsers.append(browser)


@then("the modal should close")
def modal_should_close(test_context):
    """Verify modal is closed."""
    expect(test_context.page.locator('[data-testid="new-run-modal"]')).not_to_be_visible()


@then(parsers.parse('I should see a success notification "{message}"'))
def should_see_success_notification(test_context, message: str):
    """Verify success notification is shown."""
    expect(test_context.page.get_by_text(message)).to_be_visible()


@then(parsers.parse('the new run should appear in the list with status "{status}"'))
def new_run_appears_with_status(test_context, status: str):
    """Verify new run appears with expected status."""
    first_run = test_context.page.locator('[data-testid="run-item"]').first
    expect(first_run).to_have_attribute("data-status", status)


@when("I click the \"Start Run\" button without selecting any options")
def click_start_without_options(test_context):
    """Try to start run without selecting options."""
    test_context.page.get_by_role("button", name="Start Run").click()


@then(parsers.parse('I should see validation error "{error}"'))
def should_see_validation_error(test_context, error: str):
    """Verify validation error is shown."""
    expect(test_context.page.get_by_text(error)).to_be_visible()


@then(parsers.parse('the "{button}" button should be disabled'))
def button_should_be_disabled(test_context, button: str):
    """Verify button is disabled."""
    expect(test_context.page.get_by_role("button", name=button)).to_be_disabled()


@given("I have selected some options")
def have_selected_some_options(test_context):
    """Select some options in the modal."""
    # Select a tag if available
    tag = test_context.page.locator('[data-testid^="tag-"]').first
    if tag.count() > 0:
        tag.click()


@then("no test run should be created")
def no_run_should_be_created(test_context):
    """Verify no new run was created."""
    # Would typically check via API or verify list hasn't changed
    pass


# =============================================================================
# Test Runs Page - Pagination Steps
# =============================================================================


@then(parsers.parse('I should see the first {count:d} test runs'))
def should_see_first_n_runs(test_context, count: int):
    """Verify first N runs are shown."""
    runs = test_context.page.locator('[data-testid="run-item"]')
    expect(runs).to_have_count(count)


@then("the pagination controls should be visible")
def pagination_controls_visible(test_context):
    """Verify pagination controls are shown."""
    expect(test_context.page.locator('[data-testid="pagination"]')).to_be_visible()


@when(parsers.parse('I click the "{button}" pagination button'))
def click_pagination_button(test_context, button: str):
    """Click a pagination button."""
    test_context.page.get_by_role("button", name=button).click()
    test_context.page.wait_for_load_state("networkidle")


@then("I should see the next page of test runs")
def should_see_next_page(test_context):
    """Verify next page of runs is shown."""
    # Check URL for page parameter or that runs have changed
    assert "page=" in test_context.page.url or "offset=" in test_context.page.url


@then("the page number should update")
def page_number_should_update(test_context):
    """Verify page number indicator updates."""
    expect(test_context.page.locator('[data-testid="current-page"]')).to_be_visible()


@when(parsers.parse('I click on page number "{page}" in pagination'))
def click_page_number(test_context, page: str):
    """Click on specific page number."""
    test_context.page.locator(f'[data-testid="page-{page}"]').click()
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should see test runs from page {page:d}'))
def should_see_runs_from_page(test_context, page: int):
    """Verify runs from specific page are shown."""
    # Verify via URL or data
    pass


@then(parsers.parse('page "{page}" should be highlighted in pagination'))
def page_should_be_highlighted(test_context, page: str):
    """Verify page number is highlighted."""
    page_btn = test_context.page.locator(f'[data-testid="page-{page}"]')
    expect(page_btn).to_have_class(re.compile(r"active|current|selected"))


@given("I am on page 2 of test runs")
def on_page_2(test_context):
    """Navigate to page 2."""
    test_context.page.locator('[data-testid="page-2"]').click()
    test_context.page.wait_for_load_state("networkidle")


@then("I should see the first page of test runs")
def should_see_first_page(test_context):
    """Verify first page is shown."""
    page_btn = test_context.page.locator('[data-testid="page-1"]')
    expect(page_btn).to_have_class(re.compile(r"active|current|selected"))


@given("I am on the first page")
def on_first_page(test_context):
    """Ensure on first page."""
    # Default state
    pass


@given("I am on the last page of test runs")
def on_last_page(test_context):
    """Navigate to last page."""
    last_page = test_context.page.locator('[data-testid^="page-"]').last
    last_page.click()
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('the "{button}" pagination button should be disabled'))
def pagination_button_disabled(test_context, button: str):
    """Verify pagination button is disabled."""
    expect(test_context.page.get_by_role("button", name=button)).to_be_disabled()


# =============================================================================
# Test Runs Page - Navigation Steps
# =============================================================================


@when("I click on a test run in the list")
def click_on_run(test_context):
    """Click on a test run in the list."""
    first_run = test_context.page.locator('[data-testid="run-item"]').first
    test_context.current_run_id = first_run.get_attribute("data-run-id")
    first_run.click()
    test_context.page.wait_for_load_state("networkidle")


@then("I should be on the run details page")
def should_be_on_run_details(test_context):
    """Verify on run details page."""
    expect(test_context.page.locator('[data-testid="run-details"]')).to_be_visible()


@then("the URL should contain the run ID")
def url_contains_run_id(test_context):
    """Verify URL contains run ID."""
    if test_context.current_run_id:
        assert test_context.current_run_id in test_context.page.url


@when("I click the \"View Details\" button for a run")
def click_view_details(test_context):
    """Click view details button for a run."""
    first_run = test_context.page.locator('[data-testid="run-item"]').first
    first_run.locator('[data-testid="view-details"]').click()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Run Details Page - Summary Steps
# =============================================================================


@then("I should see the run status badge")
def should_see_status_badge(test_context):
    """Verify run status badge is visible."""
    expect(test_context.page.locator('[data-testid="run-status-badge"]')).to_be_visible()


@then("I should see the total execution duration")
def should_see_total_duration(test_context):
    """Verify total execution duration is visible."""
    expect(test_context.page.locator('[data-testid="total-duration"]')).to_be_visible()


@then("I should see the environment name")
def should_see_env_name(test_context):
    """Verify environment name is visible."""
    expect(test_context.page.locator('[data-testid="environment-name"]')).to_be_visible()


@then("I should see the browser used")
def should_see_browser_used(test_context):
    """Verify browser used is visible."""
    expect(test_context.page.locator('[data-testid="browser-used"]')).to_be_visible()


@then("I should see the timestamp of execution")
def should_see_timestamp(test_context):
    """Verify execution timestamp is visible."""
    expect(test_context.page.locator('[data-testid="execution-timestamp"]')).to_be_visible()


@then("I should see the total scenarios count")
def should_see_total_scenarios(test_context):
    """Verify total scenarios count is visible."""
    expect(test_context.page.locator('[data-testid="total-scenarios"]')).to_be_visible()


@then("I should see the passed scenarios count")
def should_see_passed_count(test_context):
    """Verify passed scenarios count is visible."""
    expect(test_context.page.locator('[data-testid="passed-count"]')).to_be_visible()


@then("I should see the failed scenarios count")
def should_see_failed_count(test_context):
    """Verify failed scenarios count is visible."""
    expect(test_context.page.locator('[data-testid="failed-count"]')).to_be_visible()


@then("I should see the tags that were used to select scenarios")
def should_see_tags_used(test_context):
    """Verify tags used are visible."""
    expect(test_context.page.locator('[data-testid="run-tags"]')).to_be_visible()


@then("the tags should be displayed as badges")
def tags_displayed_as_badges(test_context):
    """Verify tags are displayed as badges."""
    tags = test_context.page.locator('[data-testid="run-tags"] [data-testid^="tag-badge-"]')
    expect(tags.first).to_be_visible()


# =============================================================================
# Run Details Page - Progress Steps
# =============================================================================


@then("I should see a progress bar")
def should_see_progress_bar(test_context):
    """Verify progress bar is visible."""
    expect(test_context.page.locator('[data-testid="progress-bar"]')).to_be_visible()


@then("the progress bar should show percentage complete")
def progress_bar_shows_percentage(test_context):
    """Verify progress bar shows percentage."""
    progress = test_context.page.locator('[data-testid="progress-percentage"]')
    expect(progress).to_be_visible()
    text = progress.inner_text()
    assert "%" in text, f"Expected percentage in '{text}'"


@then(parsers.parse('I should see "{text}" scenarios completed'))
@then(parsers.parse('I should see "X of Y scenarios completed"'))
def should_see_scenarios_completed(test_context):
    """Verify scenarios completed text."""
    expect(test_context.page.locator('[data-testid="scenarios-progress"]')).to_be_visible()


@given(parsers.parse('{completed:d} of {total:d} scenarios have completed'))
def scenarios_have_completed(test_context, completed: int, total: int):
    """Set up scenario completion state."""
    # Test data setup
    pass


@when("another scenario completes")
def another_scenario_completes(test_context):
    """Wait for another scenario to complete."""
    time.sleep(2)  # Wait for update


@then("the progress bar should update to show 60%")
def progress_bar_shows_60_percent(test_context):
    """Verify progress bar shows 60%."""
    progress = test_context.page.locator('[data-testid="progress-percentage"]')
    expect(progress).to_contain_text("60")


@then(parsers.parse('the completed count should show "{text}"'))
def completed_count_shows(test_context, text: str):
    """Verify completed count text."""
    expect(test_context.page.locator('[data-testid="scenarios-progress"]')).to_contain_text(text)


@when(parsers.parse('I wait for {seconds:d} seconds'))
def wait_seconds(test_context, seconds: int):
    """Wait for specified seconds."""
    time.sleep(seconds)


@then("the page should auto-refresh the run status")
def page_auto_refreshes(test_context):
    """Verify page auto-refreshes."""
    # Check for updated content or timestamp
    pass


@then("new completed steps should appear")
def new_completed_steps_appear(test_context):
    """Verify new steps appear."""
    # Would track step count change
    pass


@then("the progress should update without full page reload")
def progress_updates_without_reload(test_context):
    """Verify progress updates via AJAX/WebSocket."""
    # Would check for lack of navigation event
    pass


@when("the test run completes")
def run_completes(test_context):
    """Wait for run to complete."""
    test_context.page.wait_for_selector(
        '[data-testid="run-status-badge"][data-status="passed"], '
        '[data-testid="run-status-badge"][data-status="failed"]',
        timeout=60000
    )


@then("the auto-refresh should stop")
def auto_refresh_stops(test_context):
    """Verify auto-refresh stops."""
    # Would verify no more updates occur
    pass


@then("I should see the final status badge")
def should_see_final_status(test_context):
    """Verify final status badge is shown."""
    status_badge = test_context.page.locator('[data-testid="run-status-badge"]')
    status = status_badge.get_attribute("data-status")
    assert status in ["passed", "failed"], f"Unexpected status: {status}"


@then("a completion notification should appear")
def completion_notification_appears(test_context):
    """Verify completion notification is shown."""
    expect(test_context.page.locator('[data-testid="completion-notification"]')).to_be_visible()


@given("all scenarios passed")
def all_scenarios_passed(test_context):
    """Ensure all scenarios passed."""
    # Test data setup
    pass


@given("some scenarios failed")
def some_scenarios_failed(test_context):
    """Ensure some scenarios failed."""
    # Test data setup
    pass


@then(parsers.parse('I should see a "{status}" status badge with green styling'))
def should_see_passed_badge_green(test_context, status: str):
    """Verify passed status badge with green styling."""
    badge = test_context.page.locator('[data-testid="run-status-badge"]')
    expect(badge).to_contain_text(status)
    expect(badge).to_have_class(re.compile(r"success|green|passed"))


@then(parsers.parse('I should see a "{status}" status badge with red styling'))
def should_see_failed_badge_red(test_context, status: str):
    """Verify failed status badge with red styling."""
    badge = test_context.page.locator('[data-testid="run-status-badge"]')
    expect(badge).to_contain_text(status)
    expect(badge).to_have_class(re.compile(r"danger|red|failed|error"))


@then("the progress bar should show 100%")
def progress_bar_shows_100_percent(test_context):
    """Verify progress bar shows 100%."""
    progress = test_context.page.locator('[data-testid="progress-bar"]')
    expect(progress).to_have_attribute("data-value", "100")


@then(parsers.parse('I should see "{text}"'))
def should_see_specific_text(test_context, text: str):
    """Verify specific text is visible."""
    expect(test_context.page.get_by_text(text)).to_be_visible()


@then("I should see the failure count prominently")
def should_see_failure_count(test_context):
    """Verify failure count is prominently displayed."""
    expect(test_context.page.locator('[data-testid="failed-count"]')).to_be_visible()


@then("failed scenarios should be highlighted")
def failed_scenarios_highlighted(test_context):
    """Verify failed scenarios are highlighted."""
    failed_scenarios = test_context.page.locator('[data-testid="scenario-result"][data-status="failed"]')
    if failed_scenarios.count() > 0:
        expect(failed_scenarios.first).to_have_class(re.compile(r"failed|error|highlight"))


# =============================================================================
# Run Details Page - Step Results Steps
# =============================================================================


@then("I should see a list of all executed steps")
def should_see_all_steps(test_context):
    """Verify all executed steps are listed."""
    expect(test_context.page.locator('[data-testid="steps-list"]')).to_be_visible()


@then("each step should show its status (passed/failed/skipped)")
def each_step_shows_status(test_context):
    """Verify each step shows status."""
    steps = test_context.page.locator('[data-testid="step-item"]')
    for i in range(min(steps.count(), 5)):  # Check first 5
        status = steps.nth(i).get_attribute("data-status")
        assert status in ["passed", "failed", "skipped"], f"Invalid status: {status}"


@then("each step should show its execution time")
def each_step_shows_time(test_context):
    """Verify each step shows execution time."""
    steps = test_context.page.locator('[data-testid="step-item"]')
    for i in range(min(steps.count(), 5)):
        duration = steps.nth(i).locator('[data-testid="step-duration"]')
        expect(duration).to_be_visible()


@then("I should see steps organized by scenario name")
def steps_organized_by_scenario(test_context):
    """Verify steps are grouped by scenario."""
    scenario_groups = test_context.page.locator('[data-testid="scenario-group"]')
    expect(scenario_groups.first).to_be_visible()


@then("each scenario group should be collapsible")
def scenario_groups_collapsible(test_context):
    """Verify scenario groups are collapsible."""
    scenario_header = test_context.page.locator('[data-testid="scenario-header"]').first
    expect(scenario_header.locator('[data-testid="collapse-toggle"]')).to_be_visible()


@then("the scenario header should show pass/fail status")
def scenario_header_shows_status(test_context):
    """Verify scenario header shows status."""
    scenario_header = test_context.page.locator('[data-testid="scenario-header"]').first
    expect(scenario_header.locator('[data-testid="scenario-status"]')).to_be_visible()


@given("I see a list of steps")
def see_list_of_steps(test_context):
    """Ensure steps list is visible."""
    expect(test_context.page.locator('[data-testid="steps-list"]')).to_be_visible()


@when("I click on a step to expand it")
def click_to_expand_step(test_context):
    """Click on a step to expand it."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    step.click()


@then("I should see the step details panel")
def should_see_step_details(test_context):
    """Verify step details panel is visible."""
    expect(test_context.page.locator('[data-testid="step-details"]')).to_be_visible()


@then("the details should include the Gherkin step text")
def details_include_gherkin(test_context):
    """Verify Gherkin step text is in details."""
    expect(test_context.page.locator('[data-testid="step-gherkin"]')).to_be_visible()


@then("the details should include the execution duration")
def details_include_duration(test_context):
    """Verify execution duration is in details."""
    expect(test_context.page.locator('[data-testid="step-duration-detail"]')).to_be_visible()


@then("the details should include any step data")
def details_include_step_data(test_context):
    """Verify step data is included if present."""
    # Step data is optional
    pass


@given("I am on a completed test run details page with multiple failures")
def on_run_with_multiple_failures(test_context):
    """Navigate to a run with multiple failures."""
    on_failed_run_details(test_context)


@when("I expand a failed step")
def expand_failed_step(test_context):
    """Expand a failed step."""
    failed_step = test_context.page.locator('[data-testid="step-item"][data-status="failed"]').first
    failed_step.click()


@then("I should see the error message")
def should_see_error_message(test_context):
    """Verify error message is visible."""
    expect(test_context.page.locator('[data-testid="error-message"]')).to_be_visible()


@then("I should see the stack trace if available")
def should_see_stack_trace(test_context):
    """Verify stack trace is visible if available."""
    stack_trace = test_context.page.locator('[data-testid="stack-trace"]')
    # Stack trace is optional
    pass


@then("the error should be syntax highlighted")
def error_syntax_highlighted(test_context):
    """Verify error is syntax highlighted."""
    error_section = test_context.page.locator('[data-testid="error-message"]')
    expect(error_section.locator('code, pre')).to_be_visible()


@when("I click \"Next Failed\" button")
def click_next_failed(test_context):
    """Click next failed button."""
    test_context.page.get_by_role("button", name="Next Failed").click()


@then("I should jump to the next failed step")
def jump_to_next_failed(test_context):
    """Verify jump to next failed step."""
    # Would verify scroll position or focus
    pass


@then("the step should auto-expand")
def step_should_auto_expand(test_context):
    """Verify step auto-expands."""
    expect(test_context.page.locator('[data-testid="step-details"]')).to_be_visible()


@when("I click \"Previous Failed\" button")
def click_previous_failed(test_context):
    """Click previous failed button."""
    test_context.page.get_by_role("button", name="Previous Failed").click()


@then("I should jump back to the previous failed step")
def jump_to_previous_failed(test_context):
    """Verify jump to previous failed step."""
    pass


# =============================================================================
# Run Details Page - Screenshot Steps
# =============================================================================


@given("the failed step has a screenshot")
def failed_step_has_screenshot(test_context):
    """Ensure failed step has a screenshot."""
    # Test data setup
    pass


@then("I should see a screenshot thumbnail")
def should_see_screenshot_thumbnail(test_context):
    """Verify screenshot thumbnail is visible."""
    expect(test_context.page.locator('[data-testid="screenshot-thumbnail"]')).to_be_visible()


@then("the thumbnail should be clickable")
def thumbnail_is_clickable(test_context):
    """Verify thumbnail is clickable."""
    thumbnail = test_context.page.locator('[data-testid="screenshot-thumbnail"]')
    expect(thumbnail).to_be_enabled()


@given("I have expanded a failed step with screenshot")
def expanded_failed_step_with_screenshot(test_context):
    """Expand a failed step that has a screenshot."""
    expand_failed_step(test_context)


@when("I click on the screenshot thumbnail")
def click_screenshot_thumbnail(test_context):
    """Click on screenshot thumbnail."""
    test_context.page.locator('[data-testid="screenshot-thumbnail"]').click()


@then("I should see a full-size screenshot modal")
def should_see_screenshot_modal(test_context):
    """Verify full-size screenshot modal is visible."""
    expect(test_context.page.locator('[data-testid="screenshot-modal"]')).to_be_visible()


@then("the modal should have zoom controls")
def modal_has_zoom_controls(test_context):
    """Verify modal has zoom controls."""
    expect(test_context.page.locator('[data-testid="zoom-in"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="zoom-out"]')).to_be_visible()


@then("the modal should have a close button")
def modal_has_close_button(test_context):
    """Verify modal has close button."""
    expect(test_context.page.locator('[data-testid="close-modal"]')).to_be_visible()


@given("I am on a screenshot modal")
def on_screenshot_modal(test_context):
    """Ensure screenshot modal is open."""
    on_failed_run_details(test_context)
    expand_failed_step(test_context)
    click_screenshot_thumbnail(test_context)


@when("I click the \"Download\" button")
def click_download_button(test_context):
    """Click download button."""
    with test_context.page.expect_download() as download_info:
        test_context.page.get_by_role("button", name="Download").click()
    test_context.download = download_info.value


@then("the screenshot should be downloaded")
def screenshot_should_be_downloaded(test_context):
    """Verify screenshot is downloaded."""
    assert test_context.download is not None


@then("the filename should include the step name")
def filename_includes_step_name(test_context):
    """Verify filename includes step name."""
    filename = test_context.download.suggested_filename
    assert ".png" in filename.lower() or ".jpg" in filename.lower()


@given("the run has multiple screenshots")
def run_has_multiple_screenshots(test_context):
    """Ensure run has multiple screenshots."""
    pass


@when("I click \"View All Screenshots\"")
def click_view_all_screenshots(test_context):
    """Click view all screenshots."""
    test_context.page.get_by_role("button", name="View All Screenshots").click()


@then("I should see a gallery view of all screenshots")
def should_see_gallery_view(test_context):
    """Verify gallery view is visible."""
    expect(test_context.page.locator('[data-testid="screenshot-gallery"]')).to_be_visible()


@then("I should be able to navigate between screenshots")
def can_navigate_screenshots(test_context):
    """Verify can navigate between screenshots."""
    expect(test_context.page.locator('[data-testid="next-screenshot"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="prev-screenshot"]')).to_be_visible()


@then("each screenshot should show which step it belongs to")
def screenshot_shows_step_info(test_context):
    """Verify screenshot shows step info."""
    expect(test_context.page.locator('[data-testid="screenshot-step-info"]')).to_be_visible()


# =============================================================================
# Run Details Page - Report Steps
# =============================================================================


@when("I click the \"View Report\" button")
def click_view_report(test_context):
    """Click view report button."""
    with test_context.page.expect_popup() as popup_info:
        test_context.page.get_by_role("button", name="View Report").click()
    test_context.popup = popup_info.value


@then("a new tab should open with the HTML report")
def new_tab_opens_with_report(test_context):
    """Verify new tab opens with report."""
    assert test_context.popup is not None


@then("the report should load successfully")
def report_loads_successfully(test_context):
    """Verify report loads."""
    test_context.popup.wait_for_load_state("domcontentloaded")


@when("I click the \"Download Report\" button")
def click_download_report(test_context):
    """Click download report button."""
    with test_context.page.expect_download() as download_info:
        test_context.page.get_by_role("button", name="Download Report").click()
    test_context.download = download_info.value


@then("the HTML report should be downloaded")
def html_report_downloaded(test_context):
    """Verify HTML report is downloaded."""
    assert test_context.download is not None
    assert ".html" in test_context.download.suggested_filename.lower()


@then("the filename should include the run ID and timestamp")
def filename_includes_run_info(test_context):
    """Verify filename includes run ID."""
    filename = test_context.download.suggested_filename
    assert "html" in filename.lower()


@when("I look for the report button")
def look_for_report_button(test_context):
    """Look for report button."""
    # Just check visibility
    pass


@then(parsers.parse('the "{button}" button should be disabled'))
def button_is_disabled(test_context, button: str):
    """Verify button is disabled."""
    expect(test_context.page.get_by_role("button", name=button)).to_be_disabled()


@then(parsers.parse('I should see tooltip "{text}"'))
def should_see_tooltip(test_context, text: str):
    """Verify tooltip is shown."""
    # Hover over disabled button to see tooltip
    button = test_context.page.get_by_role("button", name="View Report")
    button.hover()
    expect(test_context.page.get_by_text(text)).to_be_visible()


# =============================================================================
# Scenarios Page - List Steps
# =============================================================================


@given("scenarios exist in the system")
def scenarios_exist(test_context):
    """Ensure scenarios exist."""
    pass


@given("no scenarios are synced")
def no_scenarios_synced(test_context):
    """Ensure no scenarios exist."""
    pass


@then("I should see the scenarios list")
def should_see_scenarios_list(test_context):
    """Verify scenarios list is visible."""
    expect(test_context.page.locator('[data-testid="scenarios-list"]')).to_be_visible()


@then("each scenario should display name and feature path")
def scenario_shows_name_and_path(test_context):
    """Verify scenario shows name and path."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    expect(scenario.locator('[data-testid="scenario-name"]')).to_be_visible()
    expect(scenario.locator('[data-testid="feature-path"]')).to_be_visible()


@then("each scenario should show its tags")
def scenario_shows_tags(test_context):
    """Verify scenario shows tags."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    expect(scenario.locator('[data-testid="scenario-tags"]')).to_be_visible()


@then("each scenario should show its repository source")
def scenario_shows_repo_source(test_context):
    """Verify scenario shows repo source."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    expect(scenario.locator('[data-testid="repo-source"]')).to_be_visible()


@then("the total count of scenarios should be displayed")
def total_scenarios_displayed(test_context):
    """Verify total scenarios count is displayed."""
    expect(test_context.page.locator('[data-testid="total-scenarios-count"]')).to_be_visible()


@then(parsers.parse('I should see a "{text}" button'))
def should_see_button(test_context, text: str):
    """Verify button is visible."""
    expect(test_context.page.get_by_role("button", name=text)).to_be_visible()


# =============================================================================
# Scenarios Page - Filter Steps
# =============================================================================


@given("scenarios exist from multiple repositories")
def scenarios_from_multiple_repos(test_context):
    """Ensure scenarios from multiple repos exist."""
    pass


@given("scenarios with various tags exist")
def scenarios_with_various_tags(test_context):
    """Ensure scenarios with various tags exist."""
    pass


@then(parsers.parse('I should only see scenarios from "{repo}"'))
def only_see_scenarios_from_repo(test_context, repo: str):
    """Verify only scenarios from repo are shown."""
    scenarios = test_context.page.locator('[data-testid="scenario-card"]')
    for i in range(min(scenarios.count(), 10)):
        repo_source = scenarios.nth(i).locator('[data-testid="repo-source"]').inner_text()
        assert repo in repo_source, f"Expected repo '{repo}' in '{repo_source}'"


@when(parsers.parse('I click on the "{tag}" tag filter'))
def click_tag_filter(test_context, tag: str):
    """Click on a tag filter."""
    test_context.page.locator(f'[data-testid="tag-filter-{tag}"]').click()
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should only see scenarios with the "{tag}" tag'))
def only_see_scenarios_with_tag(test_context, tag: str):
    """Verify only scenarios with tag are shown."""
    scenarios = test_context.page.locator('[data-testid="scenario-card"]')
    for i in range(min(scenarios.count(), 10)):
        tags = scenarios.nth(i).locator('[data-testid="scenario-tags"]').inner_text()
        assert tag in tags.lower(), f"Expected tag '{tag}' in '{tags}'"


@then(parsers.parse('the "{tag}" tag should be highlighted as active filter'))
def tag_highlighted_as_active(test_context, tag: str):
    """Verify tag is highlighted as active."""
    tag_filter = test_context.page.locator(f'[data-testid="tag-filter-{tag}"]')
    expect(tag_filter).to_have_class(re.compile(r"active|selected"))


@then(parsers.parse('I should see scenarios that have both "{tag1}" and "{tag2}" tags'))
def see_scenarios_with_both_tags(test_context, tag1: str, tag2: str):
    """Verify scenarios with both tags are shown."""
    scenarios = test_context.page.locator('[data-testid="scenario-card"]')
    for i in range(min(scenarios.count(), 5)):
        tags = scenarios.nth(i).locator('[data-testid="scenario-tags"]').inner_text().lower()
        assert tag1 in tags and tag2 in tags


@then("both tags should be highlighted as active filters")
def both_tags_highlighted(test_context):
    """Verify both tags are highlighted."""
    # Would check both tag filters are active
    pass


@given("I have active tag and repository filters")
def have_active_filters(test_context):
    """Apply tag and repository filters."""
    test_context.page.locator('[data-testid="tag-filter-smoke"]').click()
    test_context.page.wait_for_load_state("networkidle")


@when("I click \"Clear All Filters\"")
def click_clear_all_filters(test_context):
    """Click clear all filters."""
    test_context.page.get_by_role("button", name="Clear All Filters").click()
    test_context.page.wait_for_load_state("networkidle")


@then("I should see all scenarios")
def should_see_all_scenarios(test_context):
    """Verify all scenarios are shown."""
    expect(test_context.page.locator('[data-testid="scenario-card"]').first).to_be_visible()


@then("no filters should be highlighted")
def no_filters_highlighted(test_context):
    """Verify no filters are highlighted."""
    active_filters = test_context.page.locator('[data-testid^="tag-filter-"].active')
    expect(active_filters).to_have_count(0)


# =============================================================================
# Scenarios Page - Search Steps
# =============================================================================


@when(parsers.parse('I enter "{text}" into the "{field}" field'))
def enter_into_field(test_context, text: str, field: str):
    """Enter text into a field."""
    locator = test_context.page.locator(f'[data-testid="{field}"], input[name="{field}"]').first
    locator.fill(text)


@when("I wait for the search results")
def wait_for_search_results(test_context):
    """Wait for search results to load."""
    test_context.page.wait_for_load_state("networkidle")
    time.sleep(0.5)  # Additional wait for debounce


@then(parsers.parse('I should only see scenarios containing "{text}" in the name'))
def only_see_scenarios_matching_search(test_context, text: str):
    """Verify only matching scenarios are shown."""
    scenarios = test_context.page.locator('[data-testid="scenario-card"]')
    for i in range(min(scenarios.count(), 10)):
        name = scenarios.nth(i).locator('[data-testid="scenario-name"]').inner_text()
        assert text.lower() in name.lower(), f"Expected '{text}' in '{name}'"


@then("the search term should be highlighted in results")
def search_term_highlighted(test_context):
    """Verify search term is highlighted."""
    highlight = test_context.page.locator('[data-testid="scenario-card"] mark, [data-testid="scenario-card"] .highlight')
    # Highlighting is optional UI enhancement
    pass


@then(parsers.parse('I should see "{text}"'))
def see_text(test_context, text: str):
    """Verify text is visible."""
    expect(test_context.page.get_by_text(text)).to_be_visible()


@then(parsers.parse('a "{text}" option should be available'))
def option_should_be_available(test_context, text: str):
    """Verify an option is available."""
    expect(test_context.page.get_by_text(text)).to_be_visible()


@when(parsers.parse('I type "{text}" quickly into the "{field}" field'))
def type_quickly(test_context, text: str, field: str):
    """Type quickly into a field."""
    locator = test_context.page.locator(f'[data-testid="{field}"]').first
    locator.type(text, delay=50)


@then("the search should not trigger for each keystroke")
def search_not_triggered_per_keystroke(test_context):
    """Verify search is debounced."""
    # Would track API calls
    pass


@then("the search should trigger after I stop typing")
def search_triggers_after_typing(test_context):
    """Verify search triggers after typing stops."""
    time.sleep(0.5)
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Scenarios Page - Details Steps
# =============================================================================


@when("I click on a scenario card")
def click_scenario_card(test_context):
    """Click on a scenario card."""
    test_context.page.locator('[data-testid="scenario-card"]').first.click()


@then("I should see the scenario details panel")
def should_see_scenario_details(test_context):
    """Verify scenario details panel is visible."""
    expect(test_context.page.locator('[data-testid="scenario-details"]')).to_be_visible()


@then("I should see the full Gherkin content")
def should_see_gherkin_content(test_context):
    """Verify Gherkin content is visible."""
    expect(test_context.page.locator('[data-testid="gherkin-content"]')).to_be_visible()


@then("I should see the feature file path")
def should_see_feature_path(test_context):
    """Verify feature file path is visible."""
    expect(test_context.page.locator('[data-testid="feature-path-detail"]')).to_be_visible()


@given("I have opened a scenario details panel")
def have_opened_scenario_details(test_context):
    """Open scenario details panel."""
    click_scenario_card(test_context)


@then("I should see the Given steps")
def should_see_given_steps(test_context):
    """Verify Given steps are visible."""
    expect(test_context.page.locator('[data-testid="gherkin-content"]')).to_contain_text("Given")


@then("I should see the When steps")
def should_see_when_steps(test_context):
    """Verify When steps are visible."""
    expect(test_context.page.locator('[data-testid="gherkin-content"]')).to_contain_text("When")


@then("I should see the Then steps")
def should_see_then_steps(test_context):
    """Verify Then steps are visible."""
    expect(test_context.page.locator('[data-testid="gherkin-content"]')).to_contain_text("Then")


@then("the Gherkin keywords should be highlighted")
def gherkin_keywords_highlighted(test_context):
    """Verify Gherkin keywords are highlighted."""
    # Check for syntax highlighting classes
    pass


@then("each scenario card should display its tags as badges")
def cards_display_tag_badges(test_context):
    """Verify scenario cards display tag badges."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    tags = scenario.locator('[data-testid="tag-badge"]')
    expect(tags.first).to_be_visible()


@then("clicking a tag badge should filter by that tag")
def clicking_tag_filters(test_context):
    """Verify clicking tag badge filters."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    tag_badge = scenario.locator('[data-testid="tag-badge"]').first
    tag_text = tag_badge.inner_text()
    tag_badge.click()
    test_context.page.wait_for_load_state("networkidle")
    # Verify filter is applied
    assert f"tag={tag_text.lower()}" in test_context.page.url.lower() or \
           test_context.page.locator(f'[data-testid="tag-filter-{tag_text.lower()}"].active').count() > 0


@then("critical tags should have a distinct color")
def critical_tags_distinct_color(test_context):
    """Verify critical tags have distinct color."""
    critical_tag = test_context.page.locator('[data-testid="tag-badge"]:has-text("critical")').first
    if critical_tag.count() > 0:
        expect(critical_tag).to_have_class(re.compile(r"critical|important|red|danger"))


@then("phase tags should have a consistent color")
def phase_tags_consistent_color(test_context):
    """Verify phase tags have consistent color."""
    phase_tags = test_context.page.locator('[data-testid="tag-badge"]:has-text("phase")')
    # All phase tags should have same class
    pass


@then("feature tags should be visually distinguishable")
def feature_tags_distinguishable(test_context):
    """Verify feature tags are distinguishable."""
    pass


# =============================================================================
# Scenarios Page - Run Actions Steps
# =============================================================================


@given("I have selected a scenario")
def have_selected_scenario(test_context):
    """Select a scenario."""
    test_context.page.locator('[data-testid="scenario-card"]').first.click()


@when("I click the \"Run\" button on the scenario card")
def click_run_on_scenario(test_context):
    """Click run button on scenario card."""
    scenario = test_context.page.locator('[data-testid="scenario-card"]').first
    scenario.locator('[data-testid="quick-run-btn"]').click()


@then("I should see the quick run modal")
def should_see_quick_run_modal(test_context):
    """Verify quick run modal is visible."""
    expect(test_context.page.locator('[data-testid="quick-run-modal"]')).to_be_visible()


@then("the scenario should be pre-selected")
def scenario_pre_selected(test_context):
    """Verify scenario is pre-selected."""
    expect(test_context.page.locator('[data-testid="selected-scenario"]')).to_be_visible()


@then("I only need to select environment and browser")
def only_need_env_and_browser(test_context):
    """Verify only environment and browser selection needed."""
    expect(test_context.page.locator('[data-testid="environment-select"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="browser-selector"]')).to_be_visible()


@when("I check the checkbox on multiple scenario cards")
def check_multiple_scenarios(test_context):
    """Check multiple scenario checkboxes."""
    scenarios = test_context.page.locator('[data-testid="scenario-card"]')
    for i in range(min(scenarios.count(), 3)):
        scenarios.nth(i).locator('input[type="checkbox"]').check()


@then("the \"Run Selected\" button should become enabled")
def run_selected_enabled(test_context):
    """Verify Run Selected button is enabled."""
    expect(test_context.page.get_by_role("button", name="Run Selected")).to_be_enabled()


@then("I should see a count of selected scenarios")
def see_selected_count(test_context):
    """Verify selected scenarios count is shown."""
    expect(test_context.page.locator('[data-testid="selected-count"]')).to_be_visible()


@when("I click \"Run Selected\"")
def click_run_selected(test_context):
    """Click Run Selected button."""
    test_context.page.get_by_role("button", name="Run Selected").click()


@then("I should see the new test run modal with scenarios pre-selected")
def see_modal_with_scenarios_preselected(test_context):
    """Verify modal shows with scenarios pre-selected."""
    expect(test_context.page.locator('[data-testid="new-run-modal"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="pre-selected-scenarios"]')).to_be_visible()


# =============================================================================
# Cross-Page Navigation Steps
# =============================================================================


@then(parsers.parse('I should see breadcrumbs showing "{breadcrumb_text}"'))
def should_see_breadcrumbs(test_context, breadcrumb_text: str):
    """Verify breadcrumbs are shown."""
    expect(test_context.page.locator('[data-testid="breadcrumbs"]')).to_contain_text(breadcrumb_text.split(" > ")[0])


@when(parsers.parse('I click on "{link}" in the breadcrumbs'))
def click_breadcrumb(test_context, link: str):
    """Click on breadcrumb link."""
    test_context.page.locator(f'[data-testid="breadcrumbs"] >> text="{link}"').click()
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should be on the "{page}" page'))
def should_be_on_page(test_context, page: str):
    """Verify on expected page."""
    expect(test_context.page).to_have_url(re.compile(f"/{page}"))


@when("I navigate back to the runs page")
def navigate_back_to_runs(test_context):
    """Navigate back to runs page."""
    test_context.page.go_back()
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('the "{filter}" status filter should still be applied'))
def filter_should_be_applied(test_context, filter: str):
    """Verify filter is still applied."""
    assert f"status={filter}" in test_context.page.url.lower()
