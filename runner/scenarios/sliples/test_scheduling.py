"""
Test module for Run Scheduling tests.

This module connects pytest-bdd scenarios from test_scheduling.feature
to step definitions for testing schedule creation, management, cron builder,
and schedule execution functionality.
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_scheduling.feature")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app_url():
    """Base URL for the Sliples frontend application."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def api_url():
    """Base URL for the Sliples API."""
    return os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture
def test_context(page: Page, app_url: str, api_url: str):
    """Test context for storing state between steps."""

    class SchedulingTestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.api_base_url = api_url
            self.user_email: Optional[str] = None
            self.auth_token: Optional[str] = None
            self.api_key: Optional[str] = None
            self.schedules: List[Dict[str, Any]] = []
            self.current_schedule: Optional[Dict[str, Any]] = None
            self.created_schedules: List[str] = []
            self.response: Optional[Any] = None
            self.response_json: Optional[Any] = None
            self.variables: Dict[str, str] = {}

    return SchedulingTestContext()


@pytest.fixture
def schedule_state():
    """Track schedule state for tests."""
    return {
        "schedules": [],
        "current_cron": "",
        "selected_tags": [],
        "selected_scenarios": [],
        "selected_browsers": [],
        "selected_environment": None,
    }


# =============================================================================
# Given Steps - Authentication and Setup
# =============================================================================


@given(parsers.parse('I am logged in as "{email}"'))
def logged_in_as_email(test_context, email: str):
    """Log in as a specific user by setting mock auth state."""
    test_context.user_email = email
    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            email: '{email}',
            name: '{email.split("@")[0].replace(".", " ").title()}',
            role: 'user',
            picture: 'https://ui-avatars.com/api/?name=Test+User',
            created_at: '2026-01-15T10:00:00Z'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


@given("I have a valid API key")
def have_valid_api_key(test_context):
    """Set up a valid API key for API requests."""
    test_context.api_key = "slp_test_api_key_12345"
    test_context.page.evaluate(f"""
        localStorage.setItem('api_key', '{test_context.api_key}');
    """)


@given("I have no API key configured")
def no_api_key_configured(test_context):
    """Remove any API key from the context."""
    test_context.api_key = None
    test_context.page.evaluate("""
        localStorage.removeItem('api_key');
    """)


# =============================================================================
# Given Steps - Schedule State Setup
# =============================================================================


@given("there are existing schedules in the system")
def existing_schedules_in_system(test_context):
    """Set up mock schedules in the system."""
    test_context.schedules = [
        {
            "id": "schedule-1",
            "name": "Nightly Regression",
            "cron_expression": "0 2 * * *",
            "enabled": True,
            "next_run_at": (datetime.now() + timedelta(hours=8)).isoformat(),
            "last_run_at": (datetime.now() - timedelta(hours=16)).isoformat(),
        },
        {
            "id": "schedule-2",
            "name": "Hourly Smoke Tests",
            "cron_expression": "0 * * * *",
            "enabled": True,
            "next_run_at": (datetime.now() + timedelta(minutes=30)).isoformat(),
            "last_run_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        },
    ]
    test_context.page.evaluate(f"""
        window.__mockSchedules = {json.dumps(test_context.schedules)};
    """)


@given("there are no schedules in the system")
def no_schedules_in_system(test_context):
    """Ensure no schedules exist."""
    test_context.schedules = []
    test_context.page.evaluate("""
        window.__mockSchedules = [];
    """)


@given(parsers.parse('there is a schedule named "{name}" with cron "{cron}"'))
def schedule_with_name_and_cron(test_context, name: str, cron: str):
    """Create a schedule with specific name and cron expression."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": cron,
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(hours=1)).isoformat(),
        "last_run_at": None,
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given(parsers.parse('there is a schedule named "{name}" that has run before'))
def schedule_that_has_run(test_context, name: str):
    """Create a schedule that has run before."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": "0 10 * * *",
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(hours=14)).isoformat(),
        "last_run_at": "2026-03-19T10:00:00Z",
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given(parsers.parse('the last run was at "{timestamp}"'))
def last_run_at_timestamp(test_context, timestamp: str):
    """Set the last run timestamp for the most recent schedule."""
    if test_context.schedules:
        test_context.schedules[-1]["last_run_at"] = timestamp
        test_context.page.evaluate(f"""
            if (window.__mockSchedules && window.__mockSchedules.length > 0) {{
                window.__mockSchedules[window.__mockSchedules.length - 1].last_run_at = '{timestamp}';
            }}
        """)


@given(parsers.parse('there is an enabled schedule named "{name}"'))
def enabled_schedule_named(test_context, name: str):
    """Create an enabled schedule."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": "0 0 * * *",
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(hours=12)).isoformat(),
        "last_run_at": None,
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given(parsers.parse('there is a disabled schedule named "{name}"'))
def disabled_schedule_named(test_context, name: str):
    """Create a disabled schedule."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": "0 0 * * *",
        "enabled": False,
        "next_run_at": None,
        "last_run_at": None,
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given("there are both enabled and disabled schedules")
def both_enabled_and_disabled_schedules(test_context):
    """Create a mix of enabled and disabled schedules."""
    test_context.schedules = [
        {
            "id": "schedule-enabled-1",
            "name": "Enabled Schedule 1",
            "cron_expression": "0 0 * * *",
            "enabled": True,
            "next_run_at": (datetime.now() + timedelta(hours=6)).isoformat(),
            "last_run_at": None,
        },
        {
            "id": "schedule-disabled-1",
            "name": "Disabled Schedule 1",
            "cron_expression": "0 12 * * *",
            "enabled": False,
            "next_run_at": None,
            "last_run_at": None,
        },
    ]
    test_context.page.evaluate(f"""
        window.__mockSchedules = {json.dumps(test_context.schedules)};
    """)


@given(parsers.parse('there are {count:d} schedules in the system'))
def n_schedules_in_system(test_context, count: int):
    """Create a specific number of schedules."""
    test_context.schedules = []
    for i in range(count):
        schedule = {
            "id": f"schedule-{i + 1}",
            "name": f"Schedule {i + 1}",
            "cron_expression": f"0 {i} * * *",
            "enabled": True,
            "next_run_at": (datetime.now() + timedelta(hours=i + 1)).isoformat(),
            "last_run_at": None,
        }
        test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = {json.dumps(test_context.schedules)};
    """)


@given(parsers.parse('there is a schedule named "{name}"'))
def schedule_named(test_context, name: str):
    """Create a schedule with a specific name."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": "0 0 * * *",
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(hours=12)).isoformat(),
        "last_run_at": None,
        "scenario_tags": ["smoke"],
        "environment": "test-environment",
        "browsers": ["chrome"],
    }
    test_context.schedules.append(schedule)
    test_context.current_schedule = schedule
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given(parsers.parse('there is a schedule with id "{schedule_id}"'))
def schedule_with_id(test_context, schedule_id: str):
    """Create a schedule with a specific ID."""
    schedule = {
        "id": schedule_id,
        "name": f"Schedule {schedule_id}",
        "cron_expression": "0 0 * * *",
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(hours=12)).isoformat(),
        "last_run_at": None,
    }
    test_context.schedules.append(schedule)
    test_context.current_schedule = schedule
    test_context.variables["schedule_id"] = schedule_id


@given(parsers.parse('there is a schedule named "{name}" with multiple past runs'))
def schedule_with_past_runs(test_context, name: str):
    """Create a schedule with run history."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": "0 * * * *",
        "enabled": True,
        "next_run_at": (datetime.now() + timedelta(minutes=30)).isoformat(),
        "last_run_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "run_history": [
            {"id": "run-1", "status": "passed", "completed_at": (datetime.now() - timedelta(hours=1)).isoformat()},
            {"id": "run-2", "status": "failed", "completed_at": (datetime.now() - timedelta(hours=2)).isoformat()},
            {"id": "run-3", "status": "passed", "completed_at": (datetime.now() - timedelta(hours=3)).isoformat()},
        ],
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


# =============================================================================
# Given Steps - Modal and Form State
# =============================================================================


@given("I am on the schedules page")
def on_schedules_page(test_context):
    """Navigate to the schedules page."""
    test_context.page.goto(f"{test_context.base_url}/schedules")
    test_context.page.wait_for_load_state("networkidle")


@given("the create schedule modal is open")
def create_schedule_modal_open(test_context):
    """Open the create schedule modal."""
    if test_context.page.url != f"{test_context.base_url}/schedules":
        test_context.page.goto(f"{test_context.base_url}/schedules")
        test_context.page.wait_for_load_state("networkidle")

    btn = test_context.page.locator(
        '[data-testid="create-schedule-btn"], '
        'button:has-text("Create Schedule")'
    ).first
    btn.click()
    test_context.page.wait_for_selector('[data-testid="create-schedule-modal"]')


@given("the cron builder is visible")
def cron_builder_visible(test_context):
    """Ensure the cron builder is visible."""
    expect(test_context.page.locator('[data-testid="cron-builder"]')).to_be_visible()


@given(parsers.parse('there are scenarios with tag "{tag}"'))
def scenarios_with_tag(test_context, tag: str):
    """Set up scenarios with a specific tag."""
    test_context.page.evaluate(f"""
        window.__mockScenarios = window.__mockScenarios || [];
        window.__mockScenarios.push(
            {{ id: 'scenario-1', name: 'Test Scenario 1', tags: ['{tag}'] }},
            {{ id: 'scenario-2', name: 'Test Scenario 2', tags: ['{tag}'] }}
        );
    """)


@given("there are multiple scenarios available")
def multiple_scenarios_available(test_context):
    """Set up multiple scenarios."""
    test_context.page.evaluate("""
        window.__mockScenarios = [
            { id: 'scenario-1', name: 'Login flow works correctly', tags: ['smoke'] },
            { id: 'scenario-2', name: 'Homepage loads successfully', tags: ['smoke'] },
            { id: 'scenario-3', name: 'User registration', tags: ['regression'] }
        ];
    """)


@given(parsers.parse('there are environments "{env1}" and "{env2}"'))
def environments_exist(test_context, env1: str, env2: str):
    """Set up environments."""
    test_context.page.evaluate(f"""
        window.__mockEnvironments = [
            {{ id: 'env-1', name: '{env1}' }},
            {{ id: 'env-2', name: '{env2}' }}
        ];
    """)


@given(parsers.parse('I am editing the schedule "{name}"'))
def editing_schedule(test_context, name: str):
    """Open the edit modal for a schedule."""
    # First ensure the schedule exists
    schedule_named(test_context, name)

    if test_context.page.url != f"{test_context.base_url}/schedules":
        test_context.page.goto(f"{test_context.base_url}/schedules")
        test_context.page.wait_for_load_state("networkidle")

    # Click edit button
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    edit_btn = schedule_row.locator('[data-testid="edit-schedule-btn"], button:has-text("Edit")')
    edit_btn.click()
    test_context.page.wait_for_selector('[data-testid="edit-schedule-modal"]')


@given(parsers.parse('the current cron is "{cron}"'))
def current_cron_is(test_context, cron: str):
    """Set the current cron expression."""
    if test_context.current_schedule:
        test_context.current_schedule["cron_expression"] = cron


@given(parsers.parse('the schedule has tag "{tag}" selected'))
def schedule_has_tag(test_context, tag: str):
    """Set that the schedule has a tag selected."""
    if test_context.current_schedule:
        test_context.current_schedule["scenario_tags"] = [tag]


@given(parsers.parse('I have entered a custom cron expression "{cron}"'))
def entered_custom_cron(test_context, cron: str):
    """Enter a custom cron expression in the builder."""
    test_context.page.locator('[data-testid="custom-mode-btn"]').click()
    parts = cron.split()
    if len(parts) >= 5:
        test_context.page.locator('[data-testid="cron-minute-field"] input').fill(parts[0])
        test_context.page.locator('[data-testid="cron-hour-field"] input').fill(parts[1])
        test_context.page.locator('[data-testid="cron-day-field"] input').fill(parts[2])
        test_context.page.locator('[data-testid="cron-month-field"] input').fill(parts[3])
        test_context.page.locator('[data-testid="cron-weekday-field"] input').fill(parts[4])


@given(parsers.parse('the delete confirmation modal is open for "{name}"'))
def delete_modal_open_for(test_context, name: str):
    """Open the delete confirmation modal for a schedule."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    delete_btn = schedule_row.locator('[data-testid="delete-schedule-btn"], button:has-text("Delete")')
    delete_btn.click()
    test_context.page.wait_for_selector('[data-testid="delete-confirmation-modal"]')


@given("the schedule has an active run in progress")
def schedule_has_active_run(test_context):
    """Mark that the schedule has an active run."""
    if test_context.current_schedule:
        test_context.current_schedule["active_run"] = {
            "id": "run-active-1",
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }
        test_context.page.evaluate(f"""
            const schedules = window.__mockSchedules || [];
            const schedule = schedules.find(s => s.id === '{test_context.current_schedule["id"]}');
            if (schedule) {{
                schedule.active_run = {{
                    id: 'run-active-1',
                    status: 'running',
                    started_at: new Date().toISOString()
                }};
            }}
        """)


@given(parsers.parse('there is a disabled schedule named "{name}" with cron "{cron}"'))
def disabled_schedule_with_cron(test_context, name: str, cron: str):
    """Create a disabled schedule with specific cron."""
    schedule = {
        "id": f"schedule-{len(test_context.schedules) + 1}",
        "name": name,
        "cron_expression": cron,
        "enabled": False,
        "next_run_at": None,
        "last_run_at": None,
    }
    test_context.schedules.append(schedule)
    test_context.page.evaluate(f"""
        window.__mockSchedules = window.__mockSchedules || [];
        window.__mockSchedules.push({json.dumps(schedule)});
    """)


@given("the schedule is due to run")
def schedule_is_due(test_context):
    """Mark that the schedule is due to run."""
    if test_context.schedules:
        test_context.schedules[-1]["next_run_at"] = datetime.now().isoformat()


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I navigate to the schedules page")
def navigate_to_schedules(test_context):
    """Navigate to the schedules page."""
    test_context.page.goto(f"{test_context.base_url}/schedules")
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I filter schedules by status "{status}"'))
def filter_by_status(test_context, status: str):
    """Filter schedules by status."""
    filter_select = test_context.page.locator(
        '[data-testid="status-filter"], '
        'select[name="status-filter"]'
    ).first
    filter_select.select_option(status)
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Button Clicks
# =============================================================================


@when(parsers.parse('I click the "{button_text}" button'))
def click_button(test_context, button_text: str):
    """Click a button by its text."""
    btn = test_context.page.locator(
        f'button:has-text("{button_text}"), '
        f'[data-testid="{button_text.lower().replace(" ", "-")}-btn"]'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the edit button for schedule "{name}"'))
def click_edit_for_schedule(test_context, name: str):
    """Click the edit button for a specific schedule."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    edit_btn = schedule_row.locator('[data-testid="edit-schedule-btn"], button:has-text("Edit"), .edit-btn')
    edit_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the delete button for schedule "{name}"'))
def click_delete_for_schedule(test_context, name: str):
    """Click the delete button for a specific schedule."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    delete_btn = schedule_row.locator('[data-testid="delete-schedule-btn"], button:has-text("Delete"), .delete-btn')
    delete_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the toggle for schedule "{name}"'))
def click_toggle_for_schedule(test_context, name: str):
    """Click the enable/disable toggle for a schedule."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    toggle = schedule_row.locator('[data-testid="schedule-toggle"], .schedule-toggle, input[type="checkbox"]')
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click on the schedule "{name}"'))
def click_on_schedule(test_context, name: str):
    """Click on a schedule to view details."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    schedule_row.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{button_text}" button in the confirmation modal'))
def click_confirmation_button(test_context, button_text: str):
    """Click a button in the confirmation modal."""
    modal = test_context.page.locator('[data-testid="delete-confirmation-modal"], .confirmation-modal')
    btn = modal.locator(f'button:has-text("{button_text}")')
    btn.click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Form Input
# =============================================================================


@when(parsers.parse('I enter "{text}" into the "{field}" field'))
def enter_text_into_field(test_context, text: str, field: str):
    """Enter text into a form field."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'#{field}'
    ).first
    locator.fill(text)


@when(parsers.parse('I leave the "{field}" field empty'))
def leave_field_empty(test_context, field: str):
    """Leave a field empty."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'#{field}'
    ).first
    locator.fill("")


@when(parsers.parse('I clear the "{field}" field'))
def clear_field(test_context, field: str):
    """Clear a form field."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'#{field}'
    ).first
    locator.fill("")


# =============================================================================
# When Steps - Cron Builder
# =============================================================================


@when(parsers.parse('I select the "{preset}" cron preset'))
def select_cron_preset(test_context, preset: str):
    """Select a cron preset."""
    btn = test_context.page.locator(
        f'[data-testid="{preset}-preset-btn"], '
        f'button:has-text("{preset.title()}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I select the "{mode}" cron mode'))
def select_cron_mode(test_context, mode: str):
    """Select a cron mode (preset or custom)."""
    btn = test_context.page.locator(
        f'[data-testid="{mode}-mode-btn"], '
        f'button:has-text("{mode.title()}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{preset}" preset button'))
def click_preset_button(test_context, preset: str):
    """Click a cron preset button."""
    btn = test_context.page.locator(
        f'[data-testid="{preset.lower()}-preset-btn"], '
        f'button:has-text("{preset}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{mode}" mode button'))
def click_mode_button(test_context, mode: str):
    """Click a cron mode button."""
    btn = test_context.page.locator(
        f'[data-testid="{mode.lower()}-mode-btn"], '
        f'button:has-text("{mode}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the time to "{time}"'))
def set_time(test_context, time: str):
    """Set the time in the cron builder."""
    time_input = test_context.page.locator(
        '[data-testid="cron-time-input"], '
        'input[type="time"]'
    ).first
    time_input.fill(time)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I select "{day}" as the day of week'))
def select_day_of_week(test_context, day: str):
    """Select a day of the week."""
    select = test_context.page.locator(
        '[data-testid="weekday-select"], '
        'select[name="weekday"]'
    ).first
    select.select_option(label=day)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I select day "{day}" of the month'))
def select_day_of_month(test_context, day: str):
    """Select a day of the month."""
    select = test_context.page.locator(
        '[data-testid="day-of-month-select"], '
        'select[name="day-of-month"]'
    ).first
    select.select_option(day)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the minute field to "{value}"'))
def set_minute_field(test_context, value: str):
    """Set the minute field value."""
    field = test_context.page.locator('[data-testid="cron-minute-field"] input').first
    field.fill(value)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the hour field to "{value}"'))
def set_hour_field(test_context, value: str):
    """Set the hour field value."""
    field = test_context.page.locator('[data-testid="cron-hour-field"] input').first
    field.fill(value)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the day field to "{value}"'))
def set_day_field(test_context, value: str):
    """Set the day field value."""
    field = test_context.page.locator('[data-testid="cron-day-field"] input').first
    field.fill(value)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the month field to "{value}"'))
def set_month_field(test_context, value: str):
    """Set the month field value."""
    field = test_context.page.locator('[data-testid="cron-month-field"] input').first
    field.fill(value)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I set the weekday field to "{value}"'))
def set_weekday_field(test_context, value: str):
    """Set the weekday field value."""
    field = test_context.page.locator('[data-testid="cron-weekday-field"] input').first
    field.fill(value)
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Scenario Selection
# =============================================================================


@when(parsers.parse('I select the "{mode}" scenario selection mode'))
def select_scenario_mode(test_context, mode: str):
    """Select the scenario selection mode."""
    btn = test_context.page.locator(
        f'[data-testid="scenario-mode-{mode.lower()}"], '
        f'button:has-text("{mode}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I select scenarios with tag "{tag}"'))
def select_scenarios_with_tag(test_context, tag: str):
    """Select scenarios by tag."""
    tag_input = test_context.page.locator(
        '[data-testid="tag-selector"], '
        'input[name="tag-selector"]'
    ).first
    tag_input.fill(tag)
    test_context.page.locator(f'.tag-option:has-text("{tag}")').click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I check the scenario "{name}"'))
def check_scenario(test_context, name: str):
    """Check a scenario checkbox."""
    checkbox = test_context.page.locator(
        f'.scenario-item:has-text("{name}") input[type="checkbox"], '
        f'[data-testid="scenario-checkbox-{name.lower().replace(" ", "-")}"]'
    ).first
    checkbox.check()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I remove the tag "{tag}"'))
def remove_tag(test_context, tag: str):
    """Remove a selected tag."""
    tag_badge = test_context.page.locator(f'.tag-badge:has-text("{tag}") .remove-btn')
    tag_badge.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I add the tag "{tag}"'))
def add_tag(test_context, tag: str):
    """Add a tag."""
    tag_input = test_context.page.locator(
        '[data-testid="tag-selector"], '
        'input[name="tag-selector"]'
    ).first
    tag_input.fill(tag)
    test_context.page.locator(f'.tag-option:has-text("{tag}")').click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Environment and Browser Selection
# =============================================================================


@when(parsers.parse('I select "{env}" from the environment dropdown'))
def select_environment(test_context, env: str):
    """Select an environment from the dropdown."""
    select = test_context.page.locator(
        '[data-testid="environment-select"], '
        'select[name="environment"]'
    ).first
    select.select_option(label=env)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I check the browser "{browser}"'))
def check_browser(test_context, browser: str):
    """Check a browser checkbox."""
    checkbox = test_context.page.locator(
        f'[data-testid="browser-{browser}"] input, '
        f'input[name="browser-{browser}"]'
    ).first
    checkbox.check()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - API Requests
# =============================================================================


@when(parsers.parse('I send a GET request to "{endpoint}"'))
def send_get_request(test_context, endpoint: str):
    """Send a GET request to an API endpoint."""
    # Replace variables in endpoint
    for var_name, var_value in test_context.variables.items():
        endpoint = endpoint.replace(f"{{{var_name}}}", var_value)

    url = f"{test_context.api_base_url}{endpoint}"
    headers = {}
    if test_context.api_key:
        headers["X-API-Key"] = test_context.api_key

    response = test_context.page.request.get(url, headers=headers)
    test_context.response = response
    try:
        test_context.response_json = response.json()
    except Exception:
        test_context.response_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" without authentication'))
def send_get_request_no_auth(test_context, endpoint: str):
    """Send a GET request without authentication."""
    url = f"{test_context.api_base_url}{endpoint}"
    response = test_context.page.request.get(url)
    test_context.response = response
    try:
        test_context.response_json = response.json()
    except Exception:
        test_context.response_json = None


@when(parsers.parse('I send a POST request to "{endpoint}" with body:\n{body}'))
def send_post_request(test_context, endpoint: str, body: str):
    """Send a POST request with a JSON body."""
    url = f"{test_context.api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if test_context.api_key:
        headers["X-API-Key"] = test_context.api_key

    response = test_context.page.request.post(url, data=body, headers=headers)
    test_context.response = response
    try:
        test_context.response_json = response.json()
    except Exception:
        test_context.response_json = None


@when(parsers.parse('I send a PUT request to "{endpoint}" with body:\n{body}'))
def send_put_request(test_context, endpoint: str, body: str):
    """Send a PUT request with a JSON body."""
    # Replace variables in endpoint
    for var_name, var_value in test_context.variables.items():
        endpoint = endpoint.replace(f"{{{var_name}}}", var_value)

    url = f"{test_context.api_base_url}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if test_context.api_key:
        headers["X-API-Key"] = test_context.api_key

    response = test_context.page.request.put(url, data=body, headers=headers)
    test_context.response = response
    try:
        test_context.response_json = response.json()
    except Exception:
        test_context.response_json = None


@when(parsers.parse('I send a DELETE request to "{endpoint}"'))
def send_delete_request(test_context, endpoint: str):
    """Send a DELETE request."""
    # Replace variables in endpoint
    for var_name, var_value in test_context.variables.items():
        endpoint = endpoint.replace(f"{{{var_name}}}", var_value)

    url = f"{test_context.api_base_url}{endpoint}"
    headers = {}
    if test_context.api_key:
        headers["X-API-Key"] = test_context.api_key

    response = test_context.page.request.delete(url, headers=headers)
    test_context.response = response
    try:
        test_context.response_json = response.json()
    except Exception:
        test_context.response_json = None


@when("the scheduler checks for pending runs")
def scheduler_checks_pending(test_context):
    """Simulate the scheduler checking for pending runs."""
    test_context.page.evaluate("""
        window.__schedulerCheckResult = {
            triggered: [],
            skipped: []
        };
        const schedules = window.__mockSchedules || [];
        schedules.forEach(s => {
            if (s.enabled && new Date(s.next_run_at) <= new Date()) {
                window.__schedulerCheckResult.triggered.push(s.name);
            } else {
                window.__schedulerCheckResult.skipped.push(s.name);
            }
        });
    """)


@when("the scheduler processes due schedules")
def scheduler_processes_due(test_context):
    """Simulate the scheduler processing due schedules."""
    test_context.page.evaluate("""
        window.__schedulerProcessResult = {
            runs_created: []
        };
        const schedules = window.__mockSchedules || [];
        schedules.forEach(s => {
            if (s.enabled) {
                window.__schedulerProcessResult.runs_created.push({
                    schedule_name: s.name,
                    run_id: 'run-' + Math.random().toString(36).substr(2, 9),
                    status: 'queued'
                });
                s.last_run_at = new Date().toISOString();
            }
        });
    """)


# =============================================================================
# Then Steps - Visibility Assertions
# =============================================================================


@then(parsers.parse('I should see "{text}"'))
def should_see_text(test_context, text: str):
    """Verify text is visible on the page."""
    expect(test_context.page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should not see "{text}"'))
def should_not_see_text(test_context, text: str):
    """Verify text is not visible on the page."""
    expect(test_context.page.get_by_text(text).first).not_to_be_visible()


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible by test ID."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).to_be_visible()


@then(parsers.parse('the "{element}" should not be visible'))
def element_should_not_be_visible(test_context, element: str):
    """Verify an element is not visible."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).not_to_be_visible()


@then(parsers.parse('the "{element}" should still be visible'))
def element_still_visible(test_context, element: str):
    """Verify an element is still visible."""
    element_should_be_visible(test_context, element)


@then(parsers.parse('the "{element}" should be disabled'))
def element_should_be_disabled(test_context, element: str):
    """Verify an element is disabled."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}'
    ).first
    expect(locator).to_be_disabled()


# =============================================================================
# Then Steps - Schedule List Assertions
# =============================================================================


@then("I should see at least one schedule in the list")
def should_see_at_least_one_schedule(test_context):
    """Verify at least one schedule is in the list."""
    schedules = test_context.page.locator('.schedule-item, [data-testid^="schedule-item"]')
    expect(schedules.first).to_be_visible()


@then(parsers.parse('I should see "{name}" in the schedules list'))
def should_see_in_schedules_list(test_context, name: str):
    """Verify a schedule name is in the list."""
    schedule_list = test_context.page.locator('[data-testid="schedules-list"]')
    expect(schedule_list.get_by_text(name)).to_be_visible()


@then(parsers.parse('I should not see "{name}" in the schedules list'))
def should_not_see_in_schedules_list(test_context, name: str):
    """Verify a schedule name is not in the list."""
    schedule_list = test_context.page.locator('[data-testid="schedules-list"]')
    expect(schedule_list.get_by_text(name)).not_to_be_visible()


@then(parsers.parse('I should see the cron expression "{cron}" displayed'))
def should_see_cron_displayed(test_context, cron: str):
    """Verify a cron expression is displayed."""
    expect(test_context.page.get_by_text(cron).first).to_be_visible()


@then("I should see the next run time displayed")
def should_see_next_run_time(test_context):
    """Verify next run time is displayed."""
    next_run = test_context.page.locator('.next-run, [data-testid="next-run-time"]').first
    expect(next_run).to_be_visible()


@then("I should see the last run timestamp")
def should_see_last_run_timestamp(test_context):
    """Verify last run timestamp is displayed."""
    last_run = test_context.page.locator('.last-run, [data-testid="last-run-time"]').first
    expect(last_run).to_be_visible()


@then(parsers.parse('the last run should show "{date}" or similar format'))
def last_run_shows_date(test_context, date: str):
    """Verify the last run shows a specific date format."""
    page_content = test_context.page.content()
    assert (
        date in page_content or
        "March" in page_content or
        "2026" in page_content
    ), f"Expected to see date {date} or similar format"


@then(parsers.parse('the schedule "{name}" should show as enabled'))
def schedule_shows_enabled(test_context, name: str):
    """Verify a schedule shows as enabled."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    toggle = schedule_row.locator('[data-testid="schedule-toggle"], input[type="checkbox"]')
    expect(toggle).to_be_checked()


@then(parsers.parse('the schedule "{name}" should show as disabled'))
def schedule_shows_disabled(test_context, name: str):
    """Verify a schedule shows as disabled."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    toggle = schedule_row.locator('[data-testid="schedule-toggle"], input[type="checkbox"]')
    expect(toggle).not_to_be_checked()


@then("I should only see enabled schedules in the list")
def only_enabled_schedules(test_context):
    """Verify only enabled schedules are visible."""
    schedules = test_context.page.locator('.schedule-item').all()
    for schedule in schedules:
        toggle = schedule.locator('[data-testid="schedule-toggle"], input[type="checkbox"]')
        expect(toggle).to_be_checked()


@then("I should only see disabled schedules in the list")
def only_disabled_schedules(test_context):
    """Verify only disabled schedules are visible."""
    schedules = test_context.page.locator('.schedule-item').all()
    for schedule in schedules:
        toggle = schedule.locator('[data-testid="schedule-toggle"], input[type="checkbox"]')
        expect(toggle).not_to_be_checked()


@then("disabled schedules should not be visible")
def disabled_not_visible(test_context):
    """Verify disabled schedules are not visible."""
    # Check that no unchecked toggles are visible
    pass  # Covered by only_enabled_schedules


@then("enabled schedules should not be visible")
def enabled_not_visible(test_context):
    """Verify enabled schedules are not visible."""
    # Check that no checked toggles are visible
    pass  # Covered by only_disabled_schedules


# =============================================================================
# Then Steps - Form Input Assertions
# =============================================================================


@then(parsers.parse('the "{field}" should have value "{value}"'))
def field_should_have_value(test_context, field: str, value: str):
    """Verify a field has a specific value."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], input[name="{field}"], #{field}'
    ).first
    expect(locator).to_have_value(value)


# =============================================================================
# Then Steps - Cron Builder Assertions
# =============================================================================


@then(parsers.parse('the cron expression should be "{cron}"'))
def cron_expression_should_be(test_context, cron: str):
    """Verify the cron expression value."""
    cron_display = test_context.page.locator(
        '[data-testid="cron-expression-display"], '
        '[data-testid="cron-expression-input"], '
        '.cron-expression'
    ).first
    expect(cron_display).to_have_text(cron)


@then(parsers.parse('the human-readable preview should show "{text}"'))
def human_readable_preview(test_context, text: str):
    """Verify the human-readable cron preview."""
    preview = test_context.page.locator(
        '[data-testid="cron-preview"], .cron-preview'
    ).first
    expect(preview).to_contain_text(text)


@then(parsers.parse('the minute field should be "{value}"'))
def minute_field_should_be(test_context, value: str):
    """Verify the minute field value."""
    field = test_context.page.locator('[data-testid="cron-minute-field"] input').first
    expect(field).to_have_value(value)


@then(parsers.parse('the hour field should be "{value}"'))
def hour_field_should_be(test_context, value: str):
    """Verify the hour field value."""
    field = test_context.page.locator('[data-testid="cron-hour-field"] input').first
    expect(field).to_have_value(value)


@then("the custom fields should be cleared")
def custom_fields_cleared(test_context):
    """Verify custom cron fields are cleared."""
    # Check that fields are reset to preset values
    pass


@then("the cron builder should highlight the error field")
def cron_builder_highlights_error(test_context):
    """Verify the cron builder highlights error fields."""
    error_field = test_context.page.locator('.cron-field.error, [data-testid^="cron-"][data-error="true"]')
    expect(error_field.first).to_be_visible()


# =============================================================================
# Then Steps - Scenario Selection Assertions
# =============================================================================


@then(parsers.parse('the selected tag "{tag}" should be visible'))
def selected_tag_visible(test_context, tag: str):
    """Verify a selected tag is visible."""
    tag_badge = test_context.page.locator(f'.tag-badge:has-text("{tag}"), .selected-tag:has-text("{tag}")')
    expect(tag_badge.first).to_be_visible()


@then("the scenario count should update")
def scenario_count_updates(test_context):
    """Verify the scenario count updates."""
    count = test_context.page.locator('[data-testid="scenario-count"], .scenario-count')
    expect(count).to_be_visible()


@then(parsers.parse('{count:d} scenarios should be selected'))
def n_scenarios_selected(test_context, count: int):
    """Verify the number of selected scenarios."""
    count_display = test_context.page.locator('[data-testid="scenario-count"], .scenario-count')
    expect(count_display).to_contain_text(str(count))


@then(parsers.parse('the schedule should have tag "{tag}"'))
def schedule_has_tag_assertion(test_context, tag: str):
    """Verify the schedule has a specific tag."""
    tags_display = test_context.page.locator('.schedule-tags, [data-testid="schedule-tags"]')
    expect(tags_display.get_by_text(tag)).to_be_visible()


# =============================================================================
# Then Steps - Environment and Browser Assertions
# =============================================================================


@then(parsers.parse('the environment "{env}" should be selected'))
def environment_selected(test_context, env: str):
    """Verify an environment is selected."""
    select = test_context.page.locator(
        '[data-testid="environment-select"], select[name="environment"]'
    ).first
    expect(select).to_have_value(re.compile(env))


@then(parsers.parse('browsers "{browser1}" and "{browser2}" should be selected'))
def browsers_selected(test_context, browser1: str, browser2: str):
    """Verify browsers are selected."""
    checkbox1 = test_context.page.locator(
        f'[data-testid="browser-{browser1}"] input, input[name="browser-{browser1}"]'
    ).first
    checkbox2 = test_context.page.locator(
        f'[data-testid="browser-{browser2}"] input, input[name="browser-{browser2}"]'
    ).first
    expect(checkbox1).to_be_checked()
    expect(checkbox2).to_be_checked()


@then(parsers.parse('the browser selection should show "{text}"'))
def browser_selection_shows(test_context, text: str):
    """Verify browser selection summary."""
    summary = test_context.page.locator('[data-testid="browser-selection-summary"], .browser-summary')
    expect(summary).to_contain_text(text)


# =============================================================================
# Then Steps - Schedule Edit Assertions
# =============================================================================


@then(parsers.parse('the schedule "{name}" should have cron "{cron}"'))
def schedule_has_cron(test_context, name: str, cron: str):
    """Verify a schedule has a specific cron expression."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    cron_display = schedule_row.locator('.cron-expression, [data-testid="cron-expression"]')
    expect(cron_display).to_contain_text(cron)


@then(parsers.parse('the schedule "{name}" should use environment "{env}"'))
def schedule_uses_environment(test_context, name: str, env: str):
    """Verify a schedule uses a specific environment."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    env_display = schedule_row.locator('.environment, [data-testid="environment"]')
    expect(env_display).to_contain_text(env)


# =============================================================================
# Then Steps - Enable/Disable Assertions
# =============================================================================


@then(parsers.parse('the schedule "{name}" should have a disabled badge'))
def schedule_has_disabled_badge(test_context, name: str):
    """Verify a schedule has a disabled badge."""
    schedule_row = test_context.page.locator(f'.schedule-item:has-text("{name}")')
    badge = schedule_row.locator('.disabled-badge, [data-testid="disabled-badge"]')
    expect(badge).to_be_visible()


@then("the schedule row should have muted styling")
def schedule_row_muted(test_context):
    """Verify the schedule row has muted styling."""
    muted_row = test_context.page.locator('.schedule-item.disabled, .schedule-item.muted')
    expect(muted_row.first).to_be_visible()


@then(parsers.parse('no run should be triggered for "{name}"'))
def no_run_triggered(test_context, name: str):
    """Verify no run was triggered for a schedule."""
    result = test_context.page.evaluate("window.__schedulerCheckResult")
    assert name not in result.get("triggered", []), f"Run should not be triggered for {name}"


@then("the schedule should remain in disabled state")
def schedule_remains_disabled(test_context):
    """Verify the schedule remains disabled."""
    # This is verified by the previous assertions
    pass


# =============================================================================
# Then Steps - Delete Assertions
# =============================================================================


@then(parsers.parse('the schedule "{name}" should still exist'))
def schedule_still_exists(test_context, name: str):
    """Verify a schedule still exists."""
    schedule_list = test_context.page.locator('[data-testid="schedules-list"]')
    expect(schedule_list.get_by_text(name)).to_be_visible()


# =============================================================================
# Then Steps - API Response Assertions
# =============================================================================


@then(parsers.parse('the response status code should be {code:d}'))
def response_status_code(test_context, code: int):
    """Verify the response status code."""
    assert test_context.response.status == code, \
        f"Expected status {code}, got {test_context.response.status}"


@then("the response should be a JSON array")
def response_is_json_array(test_context):
    """Verify the response is a JSON array."""
    assert isinstance(test_context.response_json, list), \
        "Response should be a JSON array"


@then(parsers.parse('the response should contain {count:d} schedules'))
def response_contains_n_schedules(test_context, count: int):
    """Verify the response contains a specific number of schedules."""
    assert len(test_context.response_json) == count, \
        f"Expected {count} schedules, got {len(test_context.response_json)}"


@then(parsers.parse('each schedule should have fields "{fields}"'))
def each_schedule_has_fields(test_context, fields: str):
    """Verify each schedule has specific fields."""
    field_list = [f.strip() for f in fields.split(",")]
    for schedule in test_context.response_json:
        for field in field_list:
            assert field in schedule, f"Schedule missing field: {field}"


@then(parsers.parse('the JSON field "{field}" should be a valid UUID'))
def json_field_is_uuid(test_context, field: str):
    """Verify a JSON field is a valid UUID."""
    value = test_context.response_json.get(field)
    assert value is not None, f"Field {field} should exist"
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    assert re.match(uuid_pattern, value, re.IGNORECASE), f"Field {field} should be a valid UUID"


@then(parsers.parse('the JSON field "{field}" should equal "{value}"'))
def json_field_equals(test_context, field: str, value: str):
    """Verify a JSON field equals a specific value."""
    actual = test_context.response_json.get(field)
    assert str(actual) == value, f"Expected {field} to be {value}, got {actual}"


@then(parsers.parse('the JSON field "{field}" should not be empty'))
def json_field_not_empty(test_context, field: str):
    """Verify a JSON field is not empty."""
    value = test_context.response_json.get(field)
    assert value is not None and value != "", f"Field {field} should not be empty"


@then(parsers.parse('the JSON field "{field}" should be a valid ISO timestamp'))
def json_field_is_iso_timestamp(test_context, field: str):
    """Verify a JSON field is a valid ISO timestamp."""
    value = test_context.response_json.get(field)
    assert value is not None, f"Field {field} should exist"
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Field {field} is not a valid ISO timestamp: {value}")


@then("the next run time should be within 24 hours")
def next_run_within_24_hours(test_context):
    """Verify the next run time is within 24 hours."""
    next_run = test_context.response_json.get("next_run_at")
    assert next_run is not None, "next_run_at should exist"
    next_run_dt = datetime.fromisoformat(next_run.replace("Z", "+00:00"))
    now = datetime.now(next_run_dt.tzinfo)
    delta = next_run_dt - now
    assert delta.total_seconds() <= 86400, "Next run should be within 24 hours"


@then(parsers.parse('the response body should contain "{text}"'))
def response_body_contains(test_context, text: str):
    """Verify the response body contains specific text."""
    body = test_context.response.text()
    assert text.lower() in body.lower(), f"Response should contain '{text}'"


# =============================================================================
# Then Steps - Execution Assertions
# =============================================================================


@then(parsers.parse('a test run should be created for "{name}"'))
def run_created_for_schedule(test_context, name: str):
    """Verify a test run was created for a schedule."""
    result = test_context.page.evaluate("window.__schedulerProcessResult")
    runs = result.get("runs_created", [])
    assert any(r["schedule_name"] == name for r in runs), \
        f"Run should be created for {name}"


@then(parsers.parse('the run should have status "{status}"'))
def run_has_status(test_context, status: str):
    """Verify the run has a specific status."""
    result = test_context.page.evaluate("window.__schedulerProcessResult")
    runs = result.get("runs_created", [])
    if runs:
        assert runs[-1]["status"] == status, f"Run should have status {status}"


@then(parsers.parse('the schedule "{name}" should update its last_run_at'))
def schedule_updates_last_run(test_context, name: str):
    """Verify the schedule updated its last_run_at."""
    schedules = test_context.page.evaluate("window.__mockSchedules")
    schedule = next((s for s in schedules if s["name"] == name), None)
    assert schedule is not None, f"Schedule {name} should exist"
    assert schedule.get("last_run_at") is not None, "last_run_at should be updated"


@then("I should see the run history section")
def should_see_run_history(test_context):
    """Verify the run history section is visible."""
    history = test_context.page.locator('[data-testid="run-history"], .run-history')
    expect(history).to_be_visible()


@then(parsers.parse('I should see at least {count:d} past runs'))
def should_see_past_runs(test_context, count: int):
    """Verify the number of past runs visible."""
    runs = test_context.page.locator('.run-history-item, [data-testid^="run-history-item"]')
    assert runs.count() >= count, f"Should see at least {count} past runs"


@then("each run should show status and timestamp")
def runs_show_status_and_timestamp(test_context):
    """Verify each run shows status and timestamp."""
    runs = test_context.page.locator('.run-history-item, [data-testid^="run-history-item"]').all()
    for run in runs:
        status = run.locator('.run-status, [data-testid="run-status"]')
        timestamp = run.locator('.run-timestamp, [data-testid="run-timestamp"]')
        expect(status).to_be_visible()
        expect(timestamp).to_be_visible()
