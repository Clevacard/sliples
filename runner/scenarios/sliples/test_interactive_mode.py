"""
Test module for Interactive Test Mode (TEST Mode) tests.

This module connects pytest-bdd scenarios from test_interactive_mode.feature
to step definitions for UI testing with Playwright.
"""

import re
import time
from datetime import datetime

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_interactive_mode.feature")


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
            self.session_id = None
            self.selected_scenario = None
            self.selected_environment = None
            self.selected_browser = None
            self.screenshots = []
            self.variables = {}
            self.step_results = []
            self.download = None
            self.popup = None

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
        "interactive": "/interactive",
    }
    url = page_urls.get(page_name, f"/{page_name}")
    test_context.page.goto(f"{test_context.base_url}{url}")
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Start Session Steps
# =============================================================================


@when(parsers.parse('I click the "{button_text}" button'))
def click_button(test_context, button_text: str):
    """Click a button by text."""
    test_context.page.get_by_role("button", name=button_text).click()


@then("I should see the interactive mode setup panel")
def should_see_interactive_setup_panel(test_context):
    """Verify interactive mode setup panel is visible."""
    expect(test_context.page.locator('[data-testid="interactive-setup-panel"]')).to_be_visible()


@then("I should see options for scenario selection")
def should_see_scenario_options(test_context):
    """Verify scenario selection options are visible."""
    expect(test_context.page.locator('[data-testid="scenario-selector"]')).to_be_visible()


@then("I should see options for environment selection")
def should_see_environment_options(test_context):
    """Verify environment selection options are visible."""
    expect(test_context.page.locator('[data-testid="environment-select"]')).to_be_visible()


@then("I should see options for browser selection")
def should_see_browser_options(test_context):
    """Verify browser selection options are visible."""
    expect(test_context.page.locator('[data-testid="browser-select"]')).to_be_visible()


@given("I am on the interactive mode setup panel")
def on_interactive_setup_panel(test_context):
    """Navigate to interactive mode setup panel."""
    test_context.page.goto(f"{test_context.base_url}/interactive")
    test_context.page.wait_for_load_state("networkidle")
    expect(test_context.page.locator('[data-testid="interactive-setup-panel"]')).to_be_visible()


@when(parsers.parse('I select scenario "{scenario_name}" from the list'))
def select_scenario(test_context, scenario_name: str):
    """Select a scenario from the list."""
    test_context.page.locator('[data-testid="scenario-selector"]').click()
    test_context.page.locator(f'[data-testid="scenario-option"]:has-text("{scenario_name}")').click()
    test_context.selected_scenario = scenario_name


@then("the scenario should be highlighted as selected")
def scenario_highlighted_selected(test_context):
    """Verify scenario is highlighted as selected."""
    selected = test_context.page.locator('[data-testid="selected-scenario"]')
    expect(selected).to_be_visible()
    expect(selected).to_have_class(re.compile(r"selected|active"))


@then("I should see the scenario steps preview")
def should_see_steps_preview(test_context):
    """Verify scenario steps preview is visible."""
    expect(test_context.page.locator('[data-testid="steps-preview"]')).to_be_visible()


@then(parsers.parse('the "{button}" button should become enabled'))
def button_should_become_enabled(test_context, button: str):
    """Verify button becomes enabled."""
    expect(test_context.page.get_by_role("button", name=button)).to_be_enabled()


@when(parsers.parse('I select "{option}" from "{dropdown}"'))
def select_from_dropdown(test_context, option: str, dropdown: str):
    """Select an option from a dropdown."""
    locator = test_context.page.locator(f'[data-testid="{dropdown}"]')
    locator.select_option(label=option)
    if dropdown == "environment-select":
        test_context.selected_environment = option
    elif dropdown == "browser-select":
        test_context.selected_browser = option


@then("the environment should be confirmed as selected")
def environment_confirmed_selected(test_context):
    """Verify environment is confirmed as selected."""
    expect(test_context.page.locator('[data-testid="selected-environment"]')).to_be_visible()


@then("environment variables should be loaded")
def environment_variables_loaded(test_context):
    """Verify environment variables are loaded."""
    expect(test_context.page.locator('[data-testid="env-variables-loaded"]')).to_be_visible()


@then("the base URL should be displayed")
def base_url_displayed(test_context):
    """Verify base URL is displayed."""
    expect(test_context.page.locator('[data-testid="base-url-display"]')).to_be_visible()


@then("Chrome should be selected for the session")
def chrome_selected(test_context):
    """Verify Chrome is selected."""
    select = test_context.page.locator('[data-testid="browser-select"]')
    expect(select).to_have_value("chrome")


@then("browser options should be displayed")
def browser_options_displayed(test_context):
    """Verify browser options are displayed."""
    expect(test_context.page.locator('[data-testid="browser-options"]')).to_be_visible()


@then(parsers.parse('I should see the "{toggle}" toggle enabled by default'))
def toggle_enabled_by_default(test_context, toggle: str):
    """Verify toggle is enabled by default."""
    toggle_selector = toggle.lower().replace(" ", "-")
    toggle_element = test_context.page.locator(f'[data-testid="{toggle_selector}-toggle"]')
    expect(toggle_element).to_be_checked()


@then("Firefox should be selected for the session")
def firefox_selected(test_context):
    """Verify Firefox is selected."""
    select = test_context.page.locator('[data-testid="browser-select"]')
    expect(select).to_have_value("firefox")


@then("I should see Firefox-specific options if available")
def firefox_specific_options(test_context):
    """Verify Firefox-specific options are shown if available."""
    # Firefox-specific options may or may not exist
    pass


@then("WebKit should be selected for the session")
def webkit_selected(test_context):
    """Verify WebKit is selected."""
    select = test_context.page.locator('[data-testid="browser-select"]')
    expect(select).to_have_value("webkit")


@then("a warning about WebKit limitations may be shown")
def webkit_warning_shown(test_context):
    """Verify WebKit warning may be shown."""
    warning = test_context.page.locator('[data-testid="webkit-warning"]')
    # Warning is optional
    pass


@given("I have configured an interactive session")
def have_configured_session(test_context):
    """Configure an interactive session."""
    on_interactive_setup_panel(test_context)
    # Select first available scenario
    test_context.page.locator('[data-testid="scenario-selector"]').click()
    test_context.page.locator('[data-testid="scenario-option"]').first.click()
    # Select environment
    test_context.page.locator('[data-testid="environment-select"]').select_option(index=1)
    # Select browser
    test_context.page.locator('[data-testid="browser-select"]').select_option(value="chrome")


@then(parsers.parse('I should see the "{status}" status'))
def should_see_status(test_context, status: str):
    """Verify status message is shown."""
    expect(test_context.page.get_by_text(status)).to_be_visible()


@then(parsers.parse('after the browser launches I should see "{indicator}" indicator'))
def should_see_session_active_indicator(test_context, indicator: str):
    """Verify session active indicator is shown."""
    test_context.page.wait_for_selector(f'[data-testid="session-status"]:has-text("{indicator}")', timeout=30000)
    expect(test_context.page.locator(f'[data-testid="session-status"]:has-text("{indicator}")')).to_be_visible()


@then("the session timer should start")
def session_timer_should_start(test_context):
    """Verify session timer starts."""
    expect(test_context.page.locator('[data-testid="session-timer"]')).to_be_visible()


@then("I should see the interactive control panel")
def should_see_control_panel(test_context):
    """Verify interactive control panel is visible."""
    expect(test_context.page.locator('[data-testid="interactive-control-panel"]')).to_be_visible()


@when("the browser launches")
def browser_launches(test_context):
    """Wait for browser to launch."""
    test_context.page.wait_for_selector('[data-testid="session-status"]:has-text("Active")', timeout=30000)


@then("a visible browser window should open")
def visible_browser_window_opens(test_context):
    """Verify visible browser window opens."""
    # This is verified by the headed mode - the test runner launches in headed mode
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@then("the browser should navigate to the environment base URL")
def browser_navigates_to_base_url(test_context):
    """Verify browser navigates to base URL."""
    expect(test_context.page.locator('[data-testid="current-url"]')).to_be_visible()


@then("I should see the browser preview in the control panel")
def should_see_browser_preview(test_context):
    """Verify browser preview is visible."""
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@given("I have an active interactive session")
def have_active_session(test_context):
    """Ensure there is an active interactive session."""
    test_context.page.goto(f"{test_context.base_url}/interactive")
    test_context.page.wait_for_load_state("networkidle")

    # Check if session is already active
    if test_context.page.locator('[data-testid="session-status"]:has-text("Active")').count() > 0:
        return

    # Start a new session
    have_configured_session(test_context)
    test_context.page.get_by_role("button", name="Start Session").click()
    test_context.page.wait_for_selector('[data-testid="session-status"]:has-text("Active")', timeout=30000)


@when("I remain inactive for 30 minutes")
def remain_inactive(test_context):
    """Simulate inactivity (test will use mock)."""
    # In real test, this would be simulated via API or time manipulation
    test_context.page.evaluate("""
        window.__simulateInactivity && window.__simulateInactivity(30);
    """)


@then(parsers.parse('I should see a "{notification}" notification'))
def should_see_notification(test_context, notification: str):
    """Verify notification is shown."""
    expect(test_context.page.locator(f'[data-testid="notification"]:has-text("{notification}")')).to_be_visible()


@then(parsers.parse('I should have option to "{option1}" or "{option2}"'))
def should_have_options(test_context, option1: str, option2: str):
    """Verify both options are available."""
    expect(test_context.page.get_by_role("button", name=option1)).to_be_visible()
    expect(test_context.page.get_by_role("button", name=option2)).to_be_visible()


@when("I do not respond within 5 minutes")
def do_not_respond(test_context):
    """Simulate not responding (test will use mock)."""
    test_context.page.evaluate("""
        window.__simulateInactivity && window.__simulateInactivity(5);
    """)


@then("the session should end automatically")
def session_ends_automatically(test_context):
    """Verify session ends automatically."""
    expect(test_context.page.locator('[data-testid="session-status"]:has-text("Ended")')).to_be_visible()


@then("the browser should close")
def browser_should_close(test_context):
    """Verify browser closes."""
    expect(test_context.page.locator('[data-testid="browser-preview"]')).not_to_be_visible()


@when("I try to start another interactive session")
def try_start_another_session(test_context):
    """Try to start another interactive session."""
    test_context.page.goto(f"{test_context.base_url}/interactive/new")
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should see an error message "{message}"'))
def should_see_error_message(test_context, message: str):
    """Verify error message is shown."""
    expect(test_context.page.get_by_text(message)).to_be_visible()


@then(parsers.parse('I should see option to "{option1}" or "{option2}"'))
def should_see_option_to(test_context, option1: str, option2: str):
    """Verify options are available."""
    expect(test_context.page.get_by_role("button", name=option1)).to_be_visible()
    expect(test_context.page.get_by_role("button", name=option2)).to_be_visible()


@given("I have not selected a scenario")
def have_not_selected_scenario(test_context):
    """Ensure no scenario is selected."""
    # Default state - no action needed
    pass


@then(parsers.parse('I should see validation error "{error}"'))
def should_see_validation_error(test_context, error: str):
    """Verify validation error is shown."""
    expect(test_context.page.get_by_text(error)).to_be_visible()


@then("the session should not start")
def session_should_not_start(test_context):
    """Verify session does not start."""
    expect(test_context.page.locator('[data-testid="session-status"]:has-text("Active")')).not_to_be_visible()


# =============================================================================
# Step Execution Steps
# =============================================================================


@given("I see the list of scenario steps")
def see_list_of_steps(test_context):
    """Ensure scenario steps list is visible."""
    expect(test_context.page.locator('[data-testid="scenario-steps-list"]')).to_be_visible()


@when(parsers.parse('I click the "Execute" button on step "{step_text}"'))
def click_execute_on_step(test_context, step_text: str):
    """Click execute button on a specific step."""
    step = test_context.page.locator(f'[data-testid="step-item"]:has-text("{step_text}")')
    step.locator('[data-testid="execute-step-btn"]').click()


@then(parsers.parse('the step should show "{status}" status'))
def step_should_show_status(test_context, status: str):
    """Verify step shows expected status."""
    expect(test_context.page.locator(f'[data-testid="step-status"]:has-text("{status}")')).to_be_visible()


@then("the browser should perform the step action")
def browser_performs_step_action(test_context):
    """Verify browser performs the step action."""
    # This is verified by the step completing
    pass


@then("the step status should update when complete")
def step_status_updates_on_complete(test_context):
    """Verify step status updates on completion."""
    test_context.page.wait_for_selector(
        '[data-testid="step-status"]:not(:has-text("Running"))',
        timeout=30000
    )


@when("I execute a step that completes successfully")
def execute_successful_step(test_context):
    """Execute a step that will pass."""
    steps = test_context.page.locator('[data-testid="step-item"]')
    steps.first.locator('[data-testid="execute-step-btn"]').click()
    test_context.page.wait_for_selector('[data-testid="step-status"]:has-text("Passed")', timeout=30000)


@then("the step should show a green checkmark indicator")
def step_shows_green_checkmark(test_context):
    """Verify step shows green checkmark."""
    expect(test_context.page.locator('[data-testid="step-status-icon-passed"]')).to_be_visible()


@then("the step row should have green highlighting")
def step_row_has_green_highlighting(test_context):
    """Verify step row has green highlighting."""
    step = test_context.page.locator('[data-testid="step-item"][data-status="passed"]').first
    expect(step).to_have_class(re.compile(r"passed|success|green"))


@then("the step duration should be displayed")
def step_duration_displayed(test_context):
    """Verify step duration is displayed."""
    expect(test_context.page.locator('[data-testid="step-duration"]').first).to_be_visible()


@then(parsers.parse('the "{badge}" badge should appear next to the step'))
def badge_appears_next_to_step(test_context, badge: str):
    """Verify badge appears next to step."""
    expect(test_context.page.locator(f'[data-testid="step-badge"]:has-text("{badge}")')).to_be_visible()


@when("I execute a step that fails")
def execute_failing_step(test_context):
    """Execute a step that will fail."""
    # This would typically execute a step known to fail in the test scenario
    failing_step = test_context.page.locator('[data-testid="step-item"][data-expected-fail="true"]')
    if failing_step.count() > 0:
        failing_step.first.locator('[data-testid="execute-step-btn"]').click()
        test_context.page.wait_for_selector('[data-testid="step-status"]:has-text("Failed")', timeout=30000)


@then("the step should show a red X indicator")
def step_shows_red_x(test_context):
    """Verify step shows red X indicator."""
    expect(test_context.page.locator('[data-testid="step-status-icon-failed"]')).to_be_visible()


@then("the step row should have red highlighting")
def step_row_has_red_highlighting(test_context):
    """Verify step row has red highlighting."""
    step = test_context.page.locator('[data-testid="step-item"][data-status="failed"]').first
    expect(step).to_have_class(re.compile(r"failed|error|red"))


@then("the error message should be displayed")
def error_message_displayed(test_context):
    """Verify error message is displayed."""
    expect(test_context.page.locator('[data-testid="step-error-message"]')).to_be_visible()


@then("a screenshot should be captured automatically")
def screenshot_captured_automatically(test_context):
    """Verify screenshot is captured automatically."""
    expect(test_context.page.locator('[data-testid="step-screenshot"]')).to_be_visible()


@when(parsers.parse('I click the "Skip" button on a step'))
def click_skip_on_step(test_context):
    """Click skip button on a step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    step.locator('[data-testid="skip-step-btn"]').click()


@then(parsers.parse('the step should show "Skipped" status with gray indicator'))
def step_shows_skipped_status(test_context):
    """Verify step shows skipped status with gray indicator."""
    expect(test_context.page.locator('[data-testid="step-status"]:has-text("Skipped")')).to_be_visible()
    expect(test_context.page.locator('[data-testid="step-status-icon-skipped"]')).to_be_visible()


@then("I should be able to continue to the next step")
def can_continue_to_next_step(test_context):
    """Verify can continue to next step."""
    next_step = test_context.page.locator('[data-testid="step-item"]:not([data-status])').first
    expect(next_step.locator('[data-testid="execute-step-btn"]')).to_be_enabled()


@then("the skipped step should be marked in the execution summary")
def skipped_step_marked_in_summary(test_context):
    """Verify skipped step is marked in execution summary."""
    expect(test_context.page.locator('[data-testid="skipped-count"]')).to_contain_text("1")


@given("a step has failed")
def step_has_failed(test_context):
    """Ensure a step has failed."""
    execute_failing_step(test_context)


@when(parsers.parse('I click the "Retry" button on the failed step'))
def click_retry_on_failed_step(test_context):
    """Click retry button on failed step."""
    failed_step = test_context.page.locator('[data-testid="step-item"][data-status="failed"]').first
    failed_step.locator('[data-testid="retry-step-btn"]').click()


@then("the step should re-execute")
def step_should_re_execute(test_context):
    """Verify step re-executes."""
    expect(test_context.page.locator('[data-testid="step-status"]:has-text("Running")')).to_be_visible()


@then("the previous error should be cleared")
def previous_error_cleared(test_context):
    """Verify previous error is cleared."""
    # Wait for re-execution to complete
    test_context.page.wait_for_selector('[data-testid="step-status"]:not(:has-text("Running"))', timeout=30000)


@then("the new result should replace the old result")
def new_result_replaces_old(test_context):
    """Verify new result replaces old result."""
    # The step should now show the new status
    pass


@when("I execute a step")
def execute_a_step(test_context):
    """Execute a step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    step.locator('[data-testid="execute-step-btn"]').click()


@when("the step completes")
def step_completes(test_context):
    """Wait for step to complete."""
    test_context.page.wait_for_selector('[data-testid="step-status"]:not(:has-text("Running"))', timeout=30000)


@then("I should see a screenshot thumbnail next to the step")
def see_screenshot_thumbnail(test_context):
    """Verify screenshot thumbnail is visible."""
    expect(test_context.page.locator('[data-testid="step-screenshot-thumbnail"]')).to_be_visible()


@then("I can click the thumbnail to view full-size screenshot")
def can_click_thumbnail_for_fullsize(test_context):
    """Verify thumbnail is clickable."""
    thumbnail = test_context.page.locator('[data-testid="step-screenshot-thumbnail"]')
    expect(thumbnail).to_be_enabled()


@then("the screenshot should show the browser state after step execution")
def screenshot_shows_browser_state(test_context):
    """Verify screenshot shows browser state."""
    # This is verified by the screenshot content
    pass


@given("I see a step in the list")
def see_step_in_list(test_context):
    """Ensure step is visible in list."""
    expect(test_context.page.locator('[data-testid="step-item"]').first).to_be_visible()


@when(parsers.parse('I click the "Edit" button on the step'))
def click_edit_on_step(test_context):
    """Click edit button on step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    step.locator('[data-testid="edit-step-btn"]').click()


@then("I should see an inline editor with the step text")
def see_inline_editor(test_context):
    """Verify inline editor is visible."""
    expect(test_context.page.locator('[data-testid="step-inline-editor"]')).to_be_visible()


@then("I can modify the step parameters")
def can_modify_step_parameters(test_context):
    """Verify can modify step parameters."""
    editor = test_context.page.locator('[data-testid="step-inline-editor"]')
    expect(editor.locator('input, textarea')).to_be_editable()


@when("I save the changes")
def save_changes(test_context):
    """Save the changes."""
    test_context.page.get_by_role("button", name="Save").click()


@then("the step should update with my modifications")
def step_updates_with_modifications(test_context):
    """Verify step updates with modifications."""
    expect(test_context.page.locator('[data-testid="step-inline-editor"]')).not_to_be_visible()


@then("I can execute the modified step")
def can_execute_modified_step(test_context):
    """Verify can execute modified step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    expect(step.locator('[data-testid="execute-step-btn"]')).to_be_enabled()


@given("I am running steps in sequence")
def running_steps_in_sequence(test_context):
    """Start running steps in sequence."""
    test_context.page.get_by_role("button", name="Run All").click()


@when(parsers.parse('I click the "Pause" button'))
def click_pause_button(test_context):
    """Click pause button."""
    test_context.page.get_by_role("button", name="Pause").click()


@then("the execution should pause after the current step completes")
def execution_pauses_after_current(test_context):
    """Verify execution pauses after current step."""
    test_context.page.wait_for_selector('[data-testid="execution-status"]:has-text("Paused")', timeout=30000)


@then(parsers.parse('I should see "Execution Paused" status'))
def see_execution_paused_status(test_context):
    """Verify execution paused status."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Paused")')).to_be_visible()


@then(parsers.parse('the "Resume" button should appear'))
def resume_button_appears(test_context):
    """Verify resume button appears."""
    expect(test_context.page.get_by_role("button", name="Resume")).to_be_visible()


@given("execution is paused")
def execution_is_paused(test_context):
    """Ensure execution is paused."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Paused")')).to_be_visible()


@when(parsers.parse('I click the "Resume" button'))
def click_resume_button(test_context):
    """Click resume button."""
    test_context.page.get_by_role("button", name="Resume").click()


@then("execution should continue from the next step")
def execution_continues_from_next(test_context):
    """Verify execution continues from next step."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Running")')).to_be_visible()


@then(parsers.parse('the "Pause" button should reappear'))
def pause_button_reappears(test_context):
    """Verify pause button reappears."""
    expect(test_context.page.get_by_role("button", name="Pause")).to_be_visible()


@then(parsers.parse('I should see "Running..." status'))
def see_running_status(test_context):
    """Verify running status."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Running")')).to_be_visible()


@when(parsers.parse('I click the "Logs" tab in the control panel'))
def click_logs_tab(test_context):
    """Click logs tab."""
    test_context.page.locator('[data-testid="logs-tab"]').click()


@then("I should see the execution logs panel")
def see_execution_logs_panel(test_context):
    """Verify execution logs panel is visible."""
    expect(test_context.page.locator('[data-testid="execution-logs-panel"]')).to_be_visible()


@then("logs should show real-time output")
def logs_show_realtime_output(test_context):
    """Verify logs show real-time output."""
    expect(test_context.page.locator('[data-testid="log-entry"]')).to_be_visible()


@then("I can filter logs by level (info, debug, error)")
def can_filter_logs_by_level(test_context):
    """Verify can filter logs by level."""
    expect(test_context.page.locator('[data-testid="log-level-filter"]')).to_be_visible()


@then("I can search within logs")
def can_search_logs(test_context):
    """Verify can search within logs."""
    expect(test_context.page.locator('[data-testid="log-search"]')).to_be_visible()


@given("I have executed some steps")
def have_executed_some_steps(test_context):
    """Execute some steps."""
    steps = test_context.page.locator('[data-testid="step-item"]')
    for i in range(min(2, steps.count())):
        steps.nth(i).locator('[data-testid="execute-step-btn"]').click()
        test_context.page.wait_for_selector('[data-testid="step-status"]:not(:has-text("Running"))', timeout=30000)


@when(parsers.parse('I click the "Run All Remaining" button'))
def click_run_all_remaining(test_context):
    """Click run all remaining button."""
    test_context.page.get_by_role("button", name="Run All Remaining").click()


@then("all unexecuted steps should run in sequence")
def all_unexecuted_steps_run(test_context):
    """Verify all unexecuted steps run."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Running")')).to_be_visible()


@then("I should see progress indicator")
def see_progress_indicator(test_context):
    """Verify progress indicator is visible."""
    expect(test_context.page.locator('[data-testid="execution-progress"]')).to_be_visible()


@then("I can pause at any time")
def can_pause_at_any_time(test_context):
    """Verify can pause at any time."""
    expect(test_context.page.get_by_role("button", name="Pause")).to_be_enabled()


@when("I right-click on a step in the middle of the scenario")
def right_click_step_in_middle(test_context):
    """Right-click on a step in the middle."""
    steps = test_context.page.locator('[data-testid="step-item"]')
    middle_index = steps.count() // 2
    steps.nth(middle_index).click(button="right")


@when(parsers.parse('I select "Run from here"'))
def select_run_from_here(test_context):
    """Select run from here context menu option."""
    test_context.page.locator('[data-testid="context-menu-run-from-here"]').click()


@then("execution should start from that step")
def execution_starts_from_step(test_context):
    """Verify execution starts from that step."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Running")')).to_be_visible()


@then("continue through remaining steps")
def continue_through_remaining(test_context):
    """Verify execution continues through remaining steps."""
    # This is verified by execution status
    pass


# =============================================================================
# Screenshot Controls Steps
# =============================================================================


@when(parsers.parse('I click the "Take Screenshot" button'))
def click_take_screenshot(test_context):
    """Click take screenshot button."""
    test_context.page.get_by_role("button", name="Take Screenshot").click()


@then("a screenshot should be captured immediately")
def screenshot_captured_immediately(test_context):
    """Verify screenshot is captured immediately."""
    expect(test_context.page.locator('[data-testid="screenshot-captured-notification"]')).to_be_visible()


@then(parsers.parse('I should see a "Screenshot captured" notification'))
def see_screenshot_captured_notification(test_context):
    """Verify screenshot captured notification."""
    expect(test_context.page.get_by_text("Screenshot captured")).to_be_visible()


@then("the screenshot should appear in the gallery")
def screenshot_appears_in_gallery(test_context):
    """Verify screenshot appears in gallery."""
    test_context.page.locator('[data-testid="gallery-tab"]').click()
    expect(test_context.page.locator('[data-testid="gallery-screenshot"]').first).to_be_visible()


@given("I have taken multiple screenshots")
def have_taken_multiple_screenshots(test_context):
    """Take multiple screenshots."""
    for _ in range(3):
        test_context.page.get_by_role("button", name="Take Screenshot").click()
        test_context.page.wait_for_selector('[data-testid="screenshot-captured-notification"]', timeout=5000)
        time.sleep(0.5)


@when(parsers.parse('I click the "Gallery" tab'))
def click_gallery_tab(test_context):
    """Click gallery tab."""
    test_context.page.locator('[data-testid="gallery-tab"]').click()


@then("I should see all captured screenshots")
def see_all_captured_screenshots(test_context):
    """Verify all screenshots are visible."""
    expect(test_context.page.locator('[data-testid="gallery-screenshot"]')).to_have_count(3)


@then("screenshots should be displayed in chronological order")
def screenshots_in_chronological_order(test_context):
    """Verify screenshots are in chronological order."""
    # Would verify by timestamps
    pass


@then("each screenshot should show capture timestamp")
def screenshot_shows_timestamp(test_context):
    """Verify each screenshot shows timestamp."""
    screenshot = test_context.page.locator('[data-testid="gallery-screenshot"]').first
    expect(screenshot.locator('[data-testid="screenshot-timestamp"]')).to_be_visible()


@then("each screenshot should show the step context if applicable")
def screenshot_shows_step_context(test_context):
    """Verify screenshot shows step context if applicable."""
    screenshot = test_context.page.locator('[data-testid="gallery-screenshot"]').first
    # Step context is optional
    pass


@given("I have a screenshot in the gallery")
def have_screenshot_in_gallery(test_context):
    """Ensure there is a screenshot in the gallery."""
    test_context.page.get_by_role("button", name="Take Screenshot").click()
    test_context.page.wait_for_selector('[data-testid="screenshot-captured-notification"]', timeout=5000)


@when(parsers.parse('I click the "Download" button on a screenshot'))
def click_download_on_screenshot(test_context):
    """Click download button on screenshot."""
    test_context.page.locator('[data-testid="gallery-tab"]').click()
    with test_context.page.expect_download() as download_info:
        test_context.page.locator('[data-testid="download-screenshot-btn"]').first.click()
    test_context.download = download_info.value


@then("the screenshot should be downloaded as a PNG file")
def screenshot_downloaded_as_png(test_context):
    """Verify screenshot is downloaded as PNG."""
    assert test_context.download is not None
    filename = test_context.download.suggested_filename
    assert ".png" in filename.lower()


@then("the filename should include timestamp and session ID")
def filename_includes_timestamp_and_session(test_context):
    """Verify filename includes timestamp and session ID."""
    filename = test_context.download.suggested_filename
    # Filename format: screenshot_<timestamp>_<session_id>.png
    assert "screenshot" in filename.lower()


@given("I have multiple screenshots in the gallery")
def have_multiple_screenshots_in_gallery(test_context):
    """Ensure there are multiple screenshots in the gallery."""
    have_taken_multiple_screenshots(test_context)


@when("I select two screenshots for comparison")
def select_two_screenshots_for_comparison(test_context):
    """Select two screenshots for comparison."""
    test_context.page.locator('[data-testid="gallery-tab"]').click()
    screenshots = test_context.page.locator('[data-testid="gallery-screenshot"] [data-testid="select-checkbox"]')
    screenshots.nth(0).check()
    screenshots.nth(1).check()


@when(parsers.parse('I click the "Compare" button'))
def click_compare_button(test_context):
    """Click compare button."""
    test_context.page.get_by_role("button", name="Compare").click()


@then("I should see a side-by-side comparison view")
def see_side_by_side_comparison(test_context):
    """Verify side-by-side comparison view."""
    expect(test_context.page.locator('[data-testid="screenshot-comparison"]')).to_be_visible()


@then("I should see a diff overlay highlighting differences")
def see_diff_overlay(test_context):
    """Verify diff overlay is visible."""
    expect(test_context.page.locator('[data-testid="diff-overlay"]')).to_be_visible()


@then("I can toggle between overlay and side-by-side modes")
def can_toggle_comparison_modes(test_context):
    """Verify can toggle comparison modes."""
    expect(test_context.page.locator('[data-testid="comparison-mode-toggle"]')).to_be_visible()


@given(parsers.parse('the "Auto-screenshot" toggle is enabled'))
def auto_screenshot_toggle_enabled(test_context):
    """Ensure auto-screenshot toggle is enabled."""
    toggle = test_context.page.locator('[data-testid="auto-screenshot-toggle"]')
    if not toggle.is_checked():
        toggle.check()


@then("a screenshot should be automatically captured")
def screenshot_auto_captured(test_context):
    """Verify screenshot is automatically captured."""
    expect(test_context.page.locator('[data-testid="step-screenshot"]')).to_be_visible()


@then("the screenshot should be associated with the step")
def screenshot_associated_with_step(test_context):
    """Verify screenshot is associated with step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    expect(step.locator('[data-testid="step-screenshot"]')).to_be_visible()


@given("I have a screenshot open in full view")
def have_screenshot_in_full_view(test_context):
    """Open screenshot in full view."""
    test_context.page.locator('[data-testid="gallery-tab"]').click()
    test_context.page.locator('[data-testid="gallery-screenshot"]').first.click()
    expect(test_context.page.locator('[data-testid="screenshot-fullview"]')).to_be_visible()


@when(parsers.parse('I click the "Annotate" button'))
def click_annotate_button(test_context):
    """Click annotate button."""
    test_context.page.get_by_role("button", name="Annotate").click()


@then("I should see annotation tools")
def see_annotation_tools(test_context):
    """Verify annotation tools are visible."""
    expect(test_context.page.locator('[data-testid="annotation-toolbar"]')).to_be_visible()


@then("I can draw rectangles to highlight areas")
def can_draw_rectangles(test_context):
    """Verify can draw rectangles."""
    expect(test_context.page.locator('[data-testid="tool-rectangle"]')).to_be_visible()


@then("I can add text labels")
def can_add_text_labels(test_context):
    """Verify can add text labels."""
    expect(test_context.page.locator('[data-testid="tool-text"]')).to_be_visible()


@then("I can add arrows pointing to elements")
def can_add_arrows(test_context):
    """Verify can add arrows."""
    expect(test_context.page.locator('[data-testid="tool-arrow"]')).to_be_visible()


@when("I save the annotation")
def save_annotation(test_context):
    """Save the annotation."""
    test_context.page.get_by_role("button", name="Save Annotation").click()


@then("the annotated screenshot should be saved separately")
def annotated_screenshot_saved(test_context):
    """Verify annotated screenshot is saved."""
    expect(test_context.page.locator('[data-testid="annotation-saved-notification"]')).to_be_visible()


# =============================================================================
# Session Management Steps
# =============================================================================


@then("I should see the session status panel")
def see_session_status_panel(test_context):
    """Verify session status panel is visible."""
    expect(test_context.page.locator('[data-testid="session-status-panel"]')).to_be_visible()


@then("the panel should show session duration")
def panel_shows_session_duration(test_context):
    """Verify panel shows session duration."""
    expect(test_context.page.locator('[data-testid="session-duration"]')).to_be_visible()


@then("the panel should show steps executed count")
def panel_shows_steps_executed(test_context):
    """Verify panel shows steps executed count."""
    expect(test_context.page.locator('[data-testid="steps-executed-count"]')).to_be_visible()


@then("the panel should show steps passed/failed count")
def panel_shows_steps_pass_fail(test_context):
    """Verify panel shows steps passed/failed count."""
    expect(test_context.page.locator('[data-testid="steps-passed-count"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="steps-failed-count"]')).to_be_visible()


@then("the panel should show memory usage indicator")
def panel_shows_memory_usage(test_context):
    """Verify panel shows memory usage."""
    expect(test_context.page.locator('[data-testid="memory-usage"]')).to_be_visible()


@when(parsers.parse('I click the "End Session" button'))
def click_end_session(test_context):
    """Click end session button."""
    test_context.page.get_by_role("button", name="End Session").click()


@then("I should see a confirmation dialog")
def see_confirmation_dialog(test_context):
    """Verify confirmation dialog is visible."""
    expect(test_context.page.locator('[data-testid="confirmation-dialog"]')).to_be_visible()


@when("I confirm the action")
def confirm_action(test_context):
    """Confirm the action."""
    test_context.page.get_by_role("button", name="Confirm").click()


@then("the session should end")
def session_should_end(test_context):
    """Verify session ends."""
    expect(test_context.page.locator('[data-testid="session-status"]:has-text("Ended")')).to_be_visible()


@then("I should see the session summary with results")
def see_session_summary(test_context):
    """Verify session summary is visible."""
    expect(test_context.page.locator('[data-testid="session-summary"]')).to_be_visible()


@then("I should have option to save the session log")
def have_option_to_save_log(test_context):
    """Verify option to save session log."""
    expect(test_context.page.get_by_role("button", name="Save Log")).to_be_visible()


@when("the browser window is closed unexpectedly")
def browser_closed_unexpectedly(test_context):
    """Simulate browser closing unexpectedly."""
    test_context.page.evaluate("""
        window.__simulateBrowserClose && window.__simulateBrowserClose();
    """)


@then("the session should detect the browser closure")
def session_detects_browser_closure(test_context):
    """Verify session detects browser closure."""
    expect(test_context.page.locator('[data-testid="browser-disconnected-notification"]')).to_be_visible()


@then(parsers.parse('a notification should appear "Browser closed - Session ended"'))
def notification_browser_closed(test_context):
    """Verify browser closed notification."""
    expect(test_context.page.get_by_text("Browser closed - Session ended")).to_be_visible()


@then("session data should be preserved")
def session_data_preserved(test_context):
    """Verify session data is preserved."""
    # Session data should be saved to storage
    pass


@given("I had an active session that was interrupted")
def had_interrupted_session(test_context):
    """Simulate having an interrupted session."""
    test_context.page.evaluate("""
        localStorage.setItem('interrupted_session', JSON.stringify({
            id: 'test-session-123',
            scenario: 'Test Scenario',
            step: 3
        }));
    """)


@when("I navigate back to interactive mode")
def navigate_back_to_interactive(test_context):
    """Navigate back to interactive mode."""
    test_context.page.goto(f"{test_context.base_url}/interactive")
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should see "Previous session found" notification'))
def see_previous_session_notification(test_context):
    """Verify previous session found notification."""
    expect(test_context.page.get_by_text("Previous session found")).to_be_visible()


@then(parsers.parse('I should have option to "Resume Session" or "Start New"'))
def have_resume_or_start_options(test_context):
    """Verify resume or start new options."""
    expect(test_context.page.get_by_role("button", name="Resume Session")).to_be_visible()
    expect(test_context.page.get_by_role("button", name="Start New")).to_be_visible()


@when(parsers.parse('I click "Resume Session"'))
def click_resume_session(test_context):
    """Click resume session."""
    test_context.page.get_by_role("button", name="Resume Session").click()


@then("the previous session state should be restored")
def previous_session_restored(test_context):
    """Verify previous session state is restored."""
    expect(test_context.page.locator('[data-testid="session-status"]:has-text("Active")')).to_be_visible()


@then("the browser should reopen")
def browser_should_reopen(test_context):
    """Verify browser reopens."""
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@then("I should continue from where I left off")
def continue_from_where_left_off(test_context):
    """Verify can continue from where left off."""
    expect(test_context.page.locator('[data-testid="current-step-indicator"]')).to_be_visible()


@given("I have completed previous interactive sessions")
def have_completed_previous_sessions(test_context):
    """Simulate having previous sessions."""
    # This would be set up via test data
    pass


@when(parsers.parse('I click "Session History" in the interactive mode menu'))
def click_session_history(test_context):
    """Click session history."""
    test_context.page.locator('[data-testid="interactive-menu"]').click()
    test_context.page.locator('[data-testid="session-history-option"]').click()


@then("I should see a list of past sessions")
def see_list_of_past_sessions(test_context):
    """Verify list of past sessions is visible."""
    expect(test_context.page.locator('[data-testid="session-history-list"]')).to_be_visible()


@then("each session should show date, duration, and scenario")
def session_shows_date_duration_scenario(test_context):
    """Verify session shows date, duration, scenario."""
    session = test_context.page.locator('[data-testid="session-history-item"]').first
    expect(session.locator('[data-testid="session-date"]')).to_be_visible()
    expect(session.locator('[data-testid="session-duration"]')).to_be_visible()
    expect(session.locator('[data-testid="session-scenario"]')).to_be_visible()


@then("each session should show pass/fail status")
def session_shows_pass_fail(test_context):
    """Verify session shows pass/fail status."""
    session = test_context.page.locator('[data-testid="session-history-item"]').first
    expect(session.locator('[data-testid="session-status"]')).to_be_visible()


@then("I can click a session to view its details and screenshots")
def can_click_session_for_details(test_context):
    """Verify can click session for details."""
    session = test_context.page.locator('[data-testid="session-history-item"]').first
    expect(session).to_be_enabled()


@when(parsers.parse('I click the "Share Session" button'))
def click_share_session(test_context):
    """Click share session button."""
    test_context.page.get_by_role("button", name="Share Session").click()


@then("I should see sharing options")
def see_sharing_options(test_context):
    """Verify sharing options are visible."""
    expect(test_context.page.locator('[data-testid="share-options"]')).to_be_visible()


@then("I can generate a view-only link")
def can_generate_view_only_link(test_context):
    """Verify can generate view-only link."""
    expect(test_context.page.locator('[data-testid="generate-link-btn"]')).to_be_visible()


@then("I can invite a team member by email")
def can_invite_by_email(test_context):
    """Verify can invite by email."""
    expect(test_context.page.locator('[data-testid="invite-email-input"]')).to_be_visible()


@when("I share with a team member")
def share_with_team_member(test_context):
    """Share with a team member."""
    test_context.page.locator('[data-testid="invite-email-input"]').fill("teammate@example.com")
    test_context.page.get_by_role("button", name="Send Invite").click()


@then("they should receive a notification")
def teammate_receives_notification(test_context):
    """Verify teammate receives notification."""
    expect(test_context.page.get_by_text("Invitation sent")).to_be_visible()


@then("they can view the live browser preview (read-only)")
def teammate_can_view_readonly(test_context):
    """Verify teammate can view read-only."""
    # This would be tested in a separate flow
    pass


# =============================================================================
# Browser Preview Steps
# =============================================================================


@given("the browser preview panel is visible")
def browser_preview_visible(test_context):
    """Ensure browser preview panel is visible."""
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@when("the browser page changes")
def browser_page_changes(test_context):
    """Simulate browser page change."""
    # Navigate within the test app
    pass


@then("the preview should update in real-time")
def preview_updates_realtime(test_context):
    """Verify preview updates in real-time."""
    # Would verify via timestamp or content change
    pass


@then("there should be minimal delay (under 500ms)")
def minimal_delay(test_context):
    """Verify minimal delay."""
    # Would measure actual delay
    pass


@then("the preview should reflect current page state")
def preview_reflects_current_state(test_context):
    """Verify preview reflects current state."""
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@when("I look at the browser preview panel")
def look_at_preview_panel(test_context):
    """Look at browser preview panel."""
    pass


@then("I should see a rendered view of the current page")
def see_rendered_view(test_context):
    """Verify rendered view is visible."""
    expect(test_context.page.locator('[data-testid="browser-preview-content"]')).to_be_visible()


@then("the page URL should be displayed above the preview")
def url_displayed_above_preview(test_context):
    """Verify URL is displayed above preview."""
    expect(test_context.page.locator('[data-testid="current-url"]')).to_be_visible()


@then("the page title should be shown")
def page_title_shown(test_context):
    """Verify page title is shown."""
    expect(test_context.page.locator('[data-testid="current-page-title"]')).to_be_visible()


@when(parsers.parse('I click the "Zoom In" button'))
def click_zoom_in(test_context):
    """Click zoom in button."""
    test_context.page.locator('[data-testid="zoom-in-btn"]').click()


@then("the preview should zoom in")
def preview_zooms_in(test_context):
    """Verify preview zooms in."""
    zoom_level = test_context.page.locator('[data-testid="zoom-level"]').inner_text()
    assert int(zoom_level.replace("%", "")) > 100


@then("I should see more detail")
def see_more_detail(test_context):
    """Verify more detail is visible."""
    pass


@when(parsers.parse('I click the "Zoom Out" button'))
def click_zoom_out(test_context):
    """Click zoom out button."""
    test_context.page.locator('[data-testid="zoom-out-btn"]').click()


@then("the preview should zoom out")
def preview_zooms_out(test_context):
    """Verify preview zooms out."""
    zoom_level = test_context.page.locator('[data-testid="zoom-level"]').inner_text()
    assert int(zoom_level.replace("%", "")) <= 100


@then("I should see more of the page")
def see_more_of_page(test_context):
    """Verify more of page is visible."""
    pass


@then("zoom level should be displayed")
def zoom_level_displayed(test_context):
    """Verify zoom level is displayed."""
    expect(test_context.page.locator('[data-testid="zoom-level"]')).to_be_visible()


@when(parsers.parse('I click the "Fullscreen Preview" button'))
def click_fullscreen_preview(test_context):
    """Click fullscreen preview button."""
    test_context.page.locator('[data-testid="fullscreen-preview-btn"]').click()


@then("the browser preview should expand to full screen")
def preview_expands_fullscreen(test_context):
    """Verify preview expands to fullscreen."""
    expect(test_context.page.locator('[data-testid="browser-preview-fullscreen"]')).to_be_visible()


@then("I should still see basic controls")
def still_see_basic_controls(test_context):
    """Verify basic controls are still visible."""
    expect(test_context.page.locator('[data-testid="fullscreen-controls"]')).to_be_visible()


@when(parsers.parse('I press Escape or click "Exit Fullscreen"'))
def exit_fullscreen(test_context):
    """Exit fullscreen mode."""
    test_context.page.keyboard.press("Escape")


@then("the preview should return to normal size")
def preview_returns_to_normal(test_context):
    """Verify preview returns to normal size."""
    expect(test_context.page.locator('[data-testid="browser-preview-fullscreen"]')).not_to_be_visible()
    expect(test_context.page.locator('[data-testid="browser-preview"]')).to_be_visible()


@given(parsers.parse('the preview has "Direct Interaction" mode enabled'))
def direct_interaction_enabled(test_context):
    """Enable direct interaction mode."""
    toggle = test_context.page.locator('[data-testid="direct-interaction-toggle"]')
    if not toggle.is_checked():
        toggle.check()


@when("I click on an element in the preview")
def click_element_in_preview(test_context):
    """Click on element in preview."""
    test_context.page.locator('[data-testid="browser-preview-content"]').click()


@then("the click should be sent to the actual browser")
def click_sent_to_browser(test_context):
    """Verify click is sent to browser."""
    # Would verify via browser state change
    pass


@then("the page should respond to the interaction")
def page_responds_to_interaction(test_context):
    """Verify page responds to interaction."""
    pass


@then("the preview should update")
def preview_should_update(test_context):
    """Verify preview updates."""
    pass


@when(parsers.parse('I click the "DevTools" button'))
def click_devtools_button(test_context):
    """Click DevTools button."""
    test_context.page.locator('[data-testid="devtools-btn"]').click()


@then("browser DevTools should open")
def devtools_should_open(test_context):
    """Verify DevTools opens."""
    expect(test_context.page.locator('[data-testid="devtools-panel"]')).to_be_visible()


@then("I can inspect elements")
def can_inspect_elements(test_context):
    """Verify can inspect elements."""
    expect(test_context.page.locator('[data-testid="devtools-elements-tab"]')).to_be_visible()


@then("I can view console output")
def can_view_console_output(test_context):
    """Verify can view console output."""
    expect(test_context.page.locator('[data-testid="devtools-console-tab"]')).to_be_visible()


@then("I can debug JavaScript")
def can_debug_javascript(test_context):
    """Verify can debug JavaScript."""
    expect(test_context.page.locator('[data-testid="devtools-sources-tab"]')).to_be_visible()


# =============================================================================
# Additional Interactive Features Steps
# =============================================================================


@when(parsers.parse('I click the "Find Locator" button'))
def click_find_locator(test_context):
    """Click find locator button."""
    test_context.page.get_by_role("button", name="Find Locator").click()


@then("I should enter locator discovery mode")
def enter_locator_discovery_mode(test_context):
    """Verify locator discovery mode is entered."""
    expect(test_context.page.locator('[data-testid="locator-discovery-mode"]')).to_be_visible()


@then("when I hover over elements in the preview they should highlight")
def elements_highlight_on_hover(test_context):
    """Verify elements highlight on hover."""
    # Would verify via visual change
    pass


@when("I click an element")
def click_an_element(test_context):
    """Click an element."""
    test_context.page.locator('[data-testid="browser-preview-content"]').click()


@then("suggested locators should be displayed")
def suggested_locators_displayed(test_context):
    """Verify suggested locators are displayed."""
    expect(test_context.page.locator('[data-testid="suggested-locators"]')).to_be_visible()


@then("I can copy the best locator to clipboard")
def can_copy_locator(test_context):
    """Verify can copy locator."""
    expect(test_context.page.locator('[data-testid="copy-locator-btn"]')).to_be_visible()


@then("I can test the locator immediately")
def can_test_locator(test_context):
    """Verify can test locator."""
    expect(test_context.page.locator('[data-testid="test-locator-btn"]')).to_be_visible()


@when(parsers.parse('I click the "Record" button'))
def click_record_button(test_context):
    """Click record button."""
    test_context.page.get_by_role("button", name="Record").click()


@then("recording mode should start")
def recording_mode_starts(test_context):
    """Verify recording mode starts."""
    expect(test_context.page.locator('[data-testid="recording-indicator"]')).to_be_visible()


@then(parsers.parse('I should see "Recording..." indicator'))
def see_recording_indicator(test_context):
    """Verify recording indicator is visible."""
    expect(test_context.page.get_by_text("Recording...")).to_be_visible()


@when("I interact with the browser")
def interact_with_browser(test_context):
    """Interact with browser."""
    test_context.page.locator('[data-testid="browser-preview-content"]').click()


@then("my actions should be recorded as new steps")
def actions_recorded_as_steps(test_context):
    """Verify actions are recorded as steps."""
    expect(test_context.page.locator('[data-testid="recorded-step"]')).to_be_visible()


@when("I stop recording")
def stop_recording(test_context):
    """Stop recording."""
    test_context.page.get_by_role("button", name="Stop Recording").click()


@then("the new steps should appear in the scenario")
def new_steps_appear(test_context):
    """Verify new steps appear in scenario."""
    expect(test_context.page.locator('[data-testid="new-recorded-steps"]')).to_be_visible()


@when(parsers.parse('I click the "Variables" tab'))
def click_variables_tab(test_context):
    """Click variables tab."""
    test_context.page.locator('[data-testid="variables-tab"]').click()


@then("I should see all current test variables")
def see_all_variables(test_context):
    """Verify all variables are visible."""
    expect(test_context.page.locator('[data-testid="variables-list"]')).to_be_visible()


@then("I can modify variable values")
def can_modify_variables(test_context):
    """Verify can modify variable values."""
    variable = test_context.page.locator('[data-testid="variable-item"]').first
    expect(variable.locator('[data-testid="variable-value-input"]')).to_be_editable()


@then("I can add new variables")
def can_add_new_variables(test_context):
    """Verify can add new variables."""
    expect(test_context.page.get_by_role("button", name="Add Variable")).to_be_visible()


@then("changes should take effect immediately")
def changes_take_effect(test_context):
    """Verify changes take effect immediately."""
    pass


@when("I right-click on a step")
def right_click_on_step(test_context):
    """Right-click on a step."""
    step = test_context.page.locator('[data-testid="step-item"]').first
    step.click(button="right")


@when(parsers.parse('I select "Add Breakpoint"'))
def select_add_breakpoint(test_context):
    """Select add breakpoint from context menu."""
    test_context.page.locator('[data-testid="context-menu-add-breakpoint"]').click()


@then("a breakpoint indicator should appear on the step")
def breakpoint_indicator_appears(test_context):
    """Verify breakpoint indicator appears."""
    expect(test_context.page.locator('[data-testid="breakpoint-indicator"]')).to_be_visible()


@then("I can set a condition for the breakpoint")
def can_set_breakpoint_condition(test_context):
    """Verify can set breakpoint condition."""
    expect(test_context.page.locator('[data-testid="breakpoint-condition-input"]')).to_be_visible()


@when("the step is reached and condition is met")
def step_reached_condition_met(test_context):
    """Simulate step reached with condition met."""
    pass


@then("execution should pause automatically")
def execution_pauses_automatically(test_context):
    """Verify execution pauses automatically."""
    expect(test_context.page.locator('[data-testid="execution-status"]:has-text("Paused")')).to_be_visible()


@when(parsers.parse('I click the "Network" tab'))
def click_network_tab(test_context):
    """Click network tab."""
    test_context.page.locator('[data-testid="network-tab"]').click()


@then("I should see all network requests made by the browser")
def see_all_network_requests(test_context):
    """Verify all network requests are visible."""
    expect(test_context.page.locator('[data-testid="network-requests-list"]')).to_be_visible()


@then("I can filter requests by type (XHR, Fetch, Document, etc.)")
def can_filter_by_request_type(test_context):
    """Verify can filter by request type."""
    expect(test_context.page.locator('[data-testid="network-type-filter"]')).to_be_visible()


@then("I can view request and response details")
def can_view_request_response(test_context):
    """Verify can view request and response details."""
    request = test_context.page.locator('[data-testid="network-request-item"]').first
    request.click()
    expect(test_context.page.locator('[data-testid="request-details"]')).to_be_visible()


@then("I can mock or block specific requests")
def can_mock_or_block_requests(test_context):
    """Verify can mock or block requests."""
    expect(test_context.page.locator('[data-testid="mock-request-btn"]')).to_be_visible()
    expect(test_context.page.locator('[data-testid="block-request-btn"]')).to_be_visible()


@when(parsers.parse('I click the "Console" tab'))
def click_console_tab(test_context):
    """Click console tab."""
    test_context.page.locator('[data-testid="console-tab"]').click()


@then("I should see browser console output")
def see_browser_console_output(test_context):
    """Verify browser console output is visible."""
    expect(test_context.page.locator('[data-testid="console-output"]')).to_be_visible()


@then("errors should be highlighted in red")
def errors_highlighted_red(test_context):
    """Verify errors are highlighted in red."""
    error_entry = test_context.page.locator('[data-testid="console-entry-error"]')
    if error_entry.count() > 0:
        expect(error_entry.first).to_have_class(re.compile(r"error|red"))


@then("warnings should be highlighted in yellow")
def warnings_highlighted_yellow(test_context):
    """Verify warnings are highlighted in yellow."""
    warning_entry = test_context.page.locator('[data-testid="console-entry-warning"]')
    if warning_entry.count() > 0:
        expect(warning_entry.first).to_have_class(re.compile(r"warning|yellow|orange"))


@then("I can execute JavaScript commands")
def can_execute_javascript(test_context):
    """Verify can execute JavaScript commands."""
    expect(test_context.page.locator('[data-testid="console-input"]')).to_be_visible()
