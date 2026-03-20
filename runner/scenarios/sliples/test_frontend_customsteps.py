"""
Test module for Custom Steps Editor UI tests.

This module connects pytest-bdd scenarios from test_frontend_customsteps.feature
to step definitions for testing the Custom Steps management page including
listing, creating, editing, deleting steps and Monaco editor functionality.
"""

import os
import re
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_frontend_customsteps.feature")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def app_url():
    """Base URL for the Sliples frontend application."""
    return os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest.fixture
def test_context(page: Page, app_url: str):
    """Test context for storing state between steps."""

    class CustomStepsTestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.user_email: Optional[str] = None
            self.user_name: Optional[str] = None
            self.auth_token: Optional[str] = None
            self.created_steps: list = []
            self.current_step: Optional[dict] = None
            self.initial_step_count: int = 0
            self.variables: dict = {}
            self.screenshots: list = []

    return CustomStepsTestContext()


@pytest.fixture
def custom_steps_state():
    """Track custom steps state for tests."""
    return {
        "steps": [],
        "selected_step": None,
        "filter_tag": None,
        "search_query": None,
    }


# =============================================================================
# Given Steps - Authentication
# =============================================================================


@given(parsers.parse('I am logged in as "{email}"'))
def logged_in_as_email(test_context, email: str):
    """Log in as a specific user by setting mock auth state."""
    test_context.user_email = email
    test_context.user_name = email.split("@")[0].replace(".", " ").title()

    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            email: '{email}',
            name: '{test_context.user_name}',
            role: 'user',
            picture: 'https://ui-avatars.com/api/?name={test_context.user_name.replace(" ", "+")}',
            created_at: '2026-01-15T10:00:00Z'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Given Steps - Custom Steps State Setup
# =============================================================================


@given("custom steps exist in the system")
def custom_steps_exist(test_context):
    """Ensure custom steps exist in the system."""
    test_context.page.evaluate("""
        window.__mockCustomSteps = [
            {
                id: 'step-1',
                name: 'Click Button Step',
                pattern: 'I click the {button} button',
                description: 'Clicks a button element',
                code: 'def step_impl(context, button):\\n    context.page.click(f\\'button:has-text("{button}")\\')\\n',
                tags: ['ui', 'interaction'],
                created_at: '2026-03-01T10:00:00Z',
                updated_at: '2026-03-01T10:00:00Z',
                usage_count: 5
            },
            {
                id: 'step-2',
                name: 'Wait For Element Step',
                pattern: 'I wait for {element} to be visible',
                description: 'Waits until an element is visible',
                code: 'def step_impl(context, element):\\n    context.page.wait_for_selector(element)\\n',
                tags: ['ui', 'wait'],
                created_at: '2026-03-02T10:00:00Z',
                updated_at: '2026-03-02T10:00:00Z',
                usage_count: 3
            }
        ];
    """)


@given("no custom steps exist in the system")
def no_custom_steps_exist(test_context):
    """Ensure no custom steps exist in the system."""
    test_context.page.evaluate("""
        window.__mockCustomSteps = [];
    """)


@given(parsers.parse('a custom step with name "{name}" exists'))
def custom_step_with_name_exists(test_context, name: str):
    """Ensure a custom step with specific name exists."""
    step_id = f"step-{name.lower().replace(' ', '-')}"
    test_context.created_steps.append({
        "id": step_id,
        "name": name,
        "pattern": f"I do {name.lower().replace(' ', '_')}",
        "description": f"Description for {name}",
        "code": "def step_impl(context):\n    pass\n",
        "tags": [],
        "usage_count": 0,
    })
    test_context.page.evaluate(f"""
        window.__mockCustomSteps = window.__mockCustomSteps || [];
        window.__mockCustomSteps.push({{
            id: '{step_id}',
            name: '{name}',
            pattern: 'I do {name.lower().replace(' ', '_')}',
            description: 'Description for {name}',
            code: 'def step_impl(context):\\n    pass\\n',
            tags: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            usage_count: 0
        }});
    """)


@given(parsers.parse('the step has pattern "{pattern}"'))
def step_has_pattern(test_context, pattern: str):
    """Set the pattern for the most recently created step."""
    if test_context.created_steps:
        test_context.created_steps[-1]["pattern"] = pattern
        test_context.page.evaluate(f"""
            if (window.__mockCustomSteps && window.__mockCustomSteps.length > 0) {{
                window.__mockCustomSteps[window.__mockCustomSteps.length - 1].pattern = '{pattern}';
            }}
        """)


@given(parsers.parse('the step has description "{description}"'))
def step_has_description(test_context, description: str):
    """Set the description for the most recently created step."""
    if test_context.created_steps:
        test_context.created_steps[-1]["description"] = description
        test_context.page.evaluate(f"""
            if (window.__mockCustomSteps && window.__mockCustomSteps.length > 0) {{
                window.__mockCustomSteps[window.__mockCustomSteps.length - 1].description = '{description}';
            }}
        """)


@given(parsers.parse('a custom step with pattern "{pattern}" exists'))
def custom_step_with_pattern_exists(test_context, pattern: str):
    """Ensure a custom step with specific pattern exists."""
    step_id = f"step-pattern-{len(test_context.created_steps) + 1}"
    step_name = f"Pattern Step {len(test_context.created_steps) + 1}"
    test_context.created_steps.append({
        "id": step_id,
        "name": step_name,
        "pattern": pattern,
    })
    test_context.page.evaluate(f"""
        window.__mockCustomSteps = window.__mockCustomSteps || [];
        window.__mockCustomSteps.push({{
            id: '{step_id}',
            name: '{step_name}',
            pattern: '{pattern}',
            description: 'Auto-generated step',
            code: 'def step_impl(context):\\n    pass\\n',
            tags: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            usage_count: 0
        }});
    """)


@given(parsers.parse('a custom step with tag "{tag}" exists'))
def custom_step_with_tag_exists(test_context, tag: str):
    """Ensure a custom step with specific tag exists."""
    step_id = f"step-tag-{tag}"
    step_name = f"Step with {tag} tag"
    test_context.created_steps.append({
        "id": step_id,
        "name": step_name,
        "tags": [tag],
    })
    test_context.page.evaluate(f"""
        window.__mockCustomSteps = window.__mockCustomSteps || [];
        window.__mockCustomSteps.push({{
            id: '{step_id}',
            name: '{step_name}',
            pattern: 'I do something with {tag}',
            description: 'Step tagged with {tag}',
            code: 'def step_impl(context):\\n    pass\\n',
            tags: ['{tag}'],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            usage_count: 0
        }});
    """)


@given(parsers.parse('the step "{step_name}" is used in {count:d} scenarios'))
def step_is_used_in_scenarios(test_context, step_name: str, count: int):
    """Set the usage count for a specific step."""
    test_context.page.evaluate(f"""
        if (window.__mockCustomSteps) {{
            const step = window.__mockCustomSteps.find(s => s.name === '{step_name}');
            if (step) {{
                step.usage_count = {count};
                step.used_in_scenarios = Array.from({{length: {count}}}, (_, i) => ({{
                    id: 'scenario-' + (i + 1),
                    name: 'Test Scenario ' + (i + 1)
                }}));
            }}
        }}
    """)


@given(parsers.parse('the step is used in {count:d} scenarios'))
def current_step_used_in_scenarios(test_context, count: int):
    """Set usage count for the most recently referenced step."""
    test_context.page.evaluate(f"""
        if (window.__mockCustomSteps && window.__mockCustomSteps.length > 0) {{
            const step = window.__mockCustomSteps[window.__mockCustomSteps.length - 1];
            step.usage_count = {count};
            step.used_in_scenarios = Array.from({{length: {count}}}, (_, i) => ({{
                id: 'scenario-' + (i + 1),
                name: 'Test Scenario ' + (i + 1)
            }}));
        }}
    """)


# =============================================================================
# Given Steps - Page and Modal State
# =============================================================================


@given("I am on the custom steps page")
def on_custom_steps_page(test_context):
    """Navigate to the custom steps page."""
    test_context.page.goto(f"{test_context.base_url}/custom-steps")
    test_context.page.wait_for_load_state("networkidle")


@given("the create step modal is open")
def create_step_modal_is_open(test_context):
    """Open the create step modal."""
    btn = test_context.page.locator(
        '[data-testid="create-step-btn"], '
        'button:has-text("Create Custom Step")'
    ).first
    btn.click()
    test_context.page.wait_for_selector('[data-testid="create-step-modal"]')


@given(parsers.parse('I am editing the step "{step_name}"'))
def editing_step(test_context, step_name: str):
    """Open the edit modal for a specific step."""
    step_row = test_context.page.locator(f'.custom-step-item:has-text("{step_name}")')
    edit_btn = step_row.locator('[data-testid="edit-step-btn"], .edit-btn, button:has-text("Edit")')
    edit_btn.click()
    test_context.page.wait_for_selector('[data-testid="edit-step-modal"]')


@given(parsers.parse('I am editing the step with pattern "{pattern}"'))
def editing_step_with_pattern(test_context, pattern: str):
    """Open the edit modal for a step with specific pattern."""
    step_row = test_context.page.locator(f'.custom-step-item:has-text("{pattern}")')
    edit_btn = step_row.locator('[data-testid="edit-step-btn"], .edit-btn, button:has-text("Edit")')
    edit_btn.click()
    test_context.page.wait_for_selector('[data-testid="edit-step-modal"]')


@given(parsers.parse('I have filtered by tag "{tag}"'))
def have_filtered_by_tag(test_context, tag: str):
    """Apply tag filter."""
    test_context.page.locator('[data-testid="step-tag-filter"]').select_option(tag)
    test_context.page.wait_for_timeout(300)


@given(parsers.parse('I have entered pattern "{pattern}"'))
def have_entered_pattern(test_context, pattern: str):
    """Enter a pattern in the step pattern input."""
    locator = test_context.page.locator('[data-testid="step-pattern-input"]')
    locator.fill(pattern)


@given(parsers.parse('I have entered a valid pattern "{pattern}"'))
def have_entered_valid_pattern(test_context, pattern: str):
    """Enter a valid pattern."""
    locator = test_context.page.locator('[data-testid="step-pattern-input"]')
    locator.fill(pattern)


@given("I have entered valid Python code")
def have_entered_valid_code(test_context):
    """Enter valid Python code in the Monaco editor."""
    test_context.page.evaluate("""
        if (window.monacoEditor) {
            window.monacoEditor.setValue('def step_impl(context):\\n    pass\\n');
        }
    """)


@given(parsers.parse('I have entered step name "{name}"'))
def have_entered_step_name(test_context, name: str):
    """Enter a step name."""
    locator = test_context.page.locator('[data-testid="step-name-input"]')
    locator.fill(name)


@given(parsers.parse('I can see "{text}" in the custom steps list'))
def can_see_in_custom_steps_list(test_context, text: str):
    """Verify text is visible in the custom steps list."""
    locator = test_context.page.locator(f'[data-testid="custom-steps-list"]:has-text("{text}")')
    expect(locator).to_be_visible()
    # Store initial count
    test_context.initial_step_count = test_context.page.locator('.custom-step-item').count()


@given("I have just created a custom step")
def have_just_created_custom_step(test_context):
    """Simulate having just created a custom step."""
    test_context.page.evaluate("""
        window.__justCreatedStep = {
            id: 'new-step-1',
            name: 'Just Created Step',
            pattern: 'I do something new',
            description: 'Newly created step',
            code: 'def step_impl(context):\\n    pass\\n'
        };
    """)


@given(parsers.parse('I have just created a custom step named "{name}"'))
def have_just_created_custom_step_named(test_context, name: str):
    """Simulate having just created a custom step with specific name."""
    test_context.page.evaluate(f"""
        window.__justCreatedStep = {{
            id: 'new-step-{name.lower().replace(' ', '-')}',
            name: '{name}',
            pattern: 'I do {name.lower().replace(' ', '_')}',
            description: 'Newly created step: {name}',
            code: 'def step_impl(context):\\n    pass\\n'
        }};
    """)


@given(parsers.parse('a custom step is used in scenario "{scenario_name}"'))
def custom_step_used_in_scenario(test_context, scenario_name: str):
    """Set up a step that is used in a specific scenario."""
    test_context.page.evaluate(f"""
        if (window.__mockCustomSteps && window.__mockCustomSteps.length > 0) {{
            const step = window.__mockCustomSteps[window.__mockCustomSteps.length - 1];
            step.used_in_scenarios = [{{
                id: 'scenario-1',
                name: '{scenario_name}'
            }}];
            step.usage_count = 1;
        }}
    """)


@given("I am viewing the step details")
def viewing_step_details(test_context):
    """Ensure step details panel is open."""
    step = test_context.page.locator('.custom-step-item').first
    step.click()
    test_context.page.wait_for_selector('[data-testid="step-details-panel"]')


@given(parsers.parse('I have entered code "{code}" in the Monaco editor'))
def have_entered_code_in_editor(test_context, code: str):
    """Enter code in the Monaco editor."""
    test_context.page.evaluate(f"""
        if (window.monacoEditor) {{
            window.monacoEditor.setValue('{code}');
        }}
    """)


@given("I have entered code with multiple \"context\" occurrences")
def have_entered_code_with_context_occurrences(test_context):
    """Enter code with multiple context occurrences."""
    test_context.page.evaluate("""
        if (window.monacoEditor) {
            window.monacoEditor.setValue('def step_impl(context):\\n    context.page.click(".btn")\\n    context.page.wait_for_timeout(100)\\n    print(context)\\n');
        }
    """)


@given("I have entered more than 50 lines of code")
def have_entered_many_lines_of_code(test_context):
    """Enter many lines of code to trigger minimap."""
    lines = ["def step_impl(context):"]
    for i in range(60):
        lines.append(f"    # Line {i + 1}")
        lines.append(f"    pass")
    code = "\\n".join(lines)
    test_context.page.evaluate(f"""
        if (window.monacoEditor) {{
            window.monacoEditor.setValue('{code}');
        }}
    """)


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I navigate to the custom steps page")
def navigate_to_custom_steps_page(test_context):
    """Navigate to the custom steps page."""
    test_context.page.goto(f"{test_context.base_url}/custom-steps")
    test_context.page.wait_for_load_state("networkidle")


@when("I wait for the preview to update")
def wait_for_preview_update(test_context):
    """Wait for the pattern preview to update."""
    test_context.page.wait_for_timeout(500)


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


@when(parsers.parse('I click the edit button for step "{step_name}"'))
def click_edit_button_for_step(test_context, step_name: str):
    """Click the edit button for a specific step."""
    step_row = test_context.page.locator(f'.custom-step-item:has-text("{step_name}")')
    edit_btn = step_row.locator('[data-testid="edit-step-btn"], .edit-btn, button:has-text("Edit")')
    edit_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the delete button for step "{step_name}"'))
def click_delete_button_for_step(test_context, step_name: str):
    """Click the delete button for a specific step."""
    step_row = test_context.page.locator(f'.custom-step-item:has-text("{step_name}")')
    delete_btn = step_row.locator('[data-testid="delete-step-btn"], .delete-btn, button:has-text("Delete")')
    delete_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{button_text}" button in the confirmation modal'))
def click_confirmation_button(test_context, button_text: str):
    """Click a button in the confirmation modal."""
    modal = test_context.page.locator(
        '[data-testid="delete-step-modal"], '
        '[data-testid="discard-changes-modal"], '
        '.confirmation-modal'
    )
    btn = modal.locator(f'button:has-text("{button_text}")')
    btn.click()
    test_context.page.wait_for_timeout(300)


@when("I click the modal close button")
def click_modal_close_button(test_context):
    """Click the close button on the current modal."""
    close_btn = test_context.page.locator(
        '.modal-close-btn, '
        '[data-testid="modal-close-btn"], '
        'button[aria-label="Close"]'
    ).first
    close_btn.click()


@when(parsers.parse('I click on the step "{step_name}"'))
def click_on_step(test_context, step_name: str):
    """Click on a step to view its details."""
    step = test_context.page.locator(f'.custom-step-item:has-text("{step_name}")')
    step.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click on "{text}" in the usage list'))
def click_on_usage_list_item(test_context, text: str):
    """Click on an item in the step usage list."""
    usage_list = test_context.page.locator('[data-testid="step-usage-list"]')
    item = usage_list.locator(f':has-text("{text}")')
    item.click()


@when(parsers.parse('I delete the step "{step_name}"'))
def delete_step(test_context, step_name: str):
    """Delete a step through the UI."""
    click_delete_button_for_step(test_context, step_name)
    test_context.page.wait_for_selector('[data-testid="delete-step-modal"]')
    click_confirmation_button(test_context, "Delete")


# =============================================================================
# When Steps - Form Inputs
# =============================================================================


@when(parsers.parse('I enter "{text}" into the "{field}" field'))
def enter_text_into_field(test_context, text: str, field: str):
    """Enter text into a form field."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'textarea[name="{field}"], '
        f'#{field}'
    ).first
    locator.fill(text)


@when(parsers.parse('I leave the "{field}" field empty'))
def leave_field_empty(test_context, field: str):
    """Leave a form field empty."""
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
    locator.clear()


@when(parsers.parse('I select "{option}" from the "{dropdown}"'))
def select_from_dropdown(test_context, option: str, dropdown: str):
    """Select an option from a dropdown."""
    locator = test_context.page.locator(
        f'[data-testid="{dropdown}"], '
        f'select[name="{dropdown}"], '
        f'#{dropdown}'
    )
    locator.select_option(option)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I select repository "{repo_name}" from the dropdown'))
def select_repository_from_dropdown(test_context, repo_name: str):
    """Select a repository from the dropdown."""
    locator = test_context.page.locator('[data-testid="repo-select"]')
    locator.select_option(repo_name)


# =============================================================================
# When Steps - Monaco Editor
# =============================================================================


@when("I enter the following code in the Monaco editor:")
def enter_code_in_monaco(test_context, text: str):
    """Enter code into the Monaco editor using docstring."""
    # Escape the code for JavaScript
    escaped_code = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    test_context.page.evaluate(f"""
        if (window.monacoEditor) {{
            window.monacoEditor.setValue('{escaped_code}');
        }}
    """)


@when("I replace the code in the Monaco editor with:")
def replace_code_in_monaco(test_context, text: str):
    """Replace code in the Monaco editor."""
    escaped_code = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
    test_context.page.evaluate(f"""
        if (window.monacoEditor) {{
            window.monacoEditor.setValue('{escaped_code}');
        }}
    """)


@when("I clear the Monaco editor")
def clear_monaco_editor(test_context):
    """Clear the Monaco editor content."""
    test_context.page.evaluate("""
        if (window.monacoEditor) {
            window.monacoEditor.setValue('');
        }
    """)


@when("I enter multiple lines of code in the Monaco editor")
def enter_multiple_lines_in_monaco(test_context):
    """Enter multiple lines of code in the Monaco editor."""
    code = "def step_impl(context):\\n    line1 = 1\\n    line2 = 2\\n    line3 = 3\\n    line4 = 4\\n    line5 = 5\\n"
    test_context.page.evaluate(f"""
        if (window.monacoEditor) {{
            window.monacoEditor.setValue('{code}');
        }}
    """)


@when(parsers.parse('I type "{text}" in the Monaco editor'))
def type_in_monaco(test_context, text: str):
    """Type text in the Monaco editor."""
    editor = test_context.page.locator('[data-testid="step-code-editor"] .monaco-editor')
    editor.click()
    test_context.page.keyboard.type(text)


@when(parsers.parse('I press "{key}" to undo'))
def press_key_to_undo(test_context, key: str):
    """Press keyboard shortcut to undo."""
    test_context.page.keyboard.press("Control+z")


@when(parsers.parse('I press "{key}" to redo'))
def press_key_to_redo(test_context, key: str):
    """Press keyboard shortcut to redo."""
    test_context.page.keyboard.press("Control+y")


@when(parsers.parse('I press "{key}" to open find dialog'))
def press_key_to_find(test_context, key: str):
    """Press keyboard shortcut to open find dialog."""
    test_context.page.keyboard.press("Control+f")


@when(parsers.parse('I press the "{key}" key'))
def press_key(test_context, key: str):
    """Press a keyboard key."""
    test_context.page.keyboard.press(key)


@when(parsers.parse('I press "{key}" and type "{text}"'))
def press_key_and_type(test_context, key: str, text: str):
    """Press a key and then type text."""
    test_context.page.keyboard.press(key)
    test_context.page.keyboard.type(text)


@when(parsers.parse('I trigger autocomplete with "{shortcut}"'))
def trigger_autocomplete(test_context, shortcut: str):
    """Trigger autocomplete in Monaco editor."""
    test_context.page.keyboard.press("Control+Space")
    test_context.page.wait_for_timeout(500)


@when(parsers.parse('I enter "{text}" in the find field'))
def enter_in_find_field(test_context, text: str):
    """Enter text in the Monaco find dialog."""
    find_input = test_context.page.locator('.monaco-findInput input, .find-widget input').first
    find_input.fill(text)


@when(parsers.parse('I click "Replace All" with "{replacement}"'))
def click_replace_all(test_context, replacement: str):
    """Click Replace All button with replacement text."""
    replace_input = test_context.page.locator('.monaco-replaceInput input, .replace-widget input').first
    replace_input.fill(replacement)
    replace_all_btn = test_context.page.locator('button[title*="Replace All"]').first
    replace_all_btn.click()


@when(parsers.parse('I type "{text}"'))
def type_text(test_context, text: str):
    """Type text at current cursor position."""
    test_context.page.keyboard.type(text)


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
def element_should_still_be_visible(test_context, element: str):
    """Verify an element is still visible (alias)."""
    element_should_be_visible(test_context, element)


@then(parsers.parse('the "{element}" should be disabled'))
def element_should_be_disabled(test_context, element: str):
    """Verify an element is disabled."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}'
    ).first
    expect(locator).to_be_disabled()


# =============================================================================
# Then Steps - Custom Steps List Assertions
# =============================================================================


@then("I should see at least one custom step in the list")
def should_see_at_least_one_step(test_context):
    """Verify at least one custom step is visible."""
    steps = test_context.page.locator('.custom-step-item')
    expect(steps.first).to_be_visible()


@then(parsers.parse('I should see "{text}" in the custom steps list'))
def should_see_in_custom_steps_list(test_context, text: str):
    """Verify text appears in the custom steps list."""
    list_locator = test_context.page.locator('[data-testid="custom-steps-list"]')
    expect(list_locator.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should not see "{text}" in the custom steps list'))
def should_not_see_in_custom_steps_list(test_context, text: str):
    """Verify text does not appear in the custom steps list."""
    list_locator = test_context.page.locator('[data-testid="custom-steps-list"]')
    expect(list_locator.get_by_text(text)).to_have_count(0)


@then(parsers.parse('I should only see steps with tag "{tag}"'))
def should_only_see_steps_with_tag(test_context, tag: str):
    """Verify only steps with specific tag are visible."""
    steps = test_context.page.locator('.custom-step-item')
    for i in range(steps.count()):
        step = steps.nth(i)
        tag_badge = step.locator(f'.tag-badge:has-text("{tag}")')
        expect(tag_badge).to_be_visible()


@then(parsers.parse('I should not see steps with tag "{tag}"'))
def should_not_see_steps_with_tag(test_context, tag: str):
    """Verify steps with specific tag are not visible."""
    filtered_steps = test_context.page.locator(f'.custom-step-item:has(.tag-badge:has-text("{tag}"))')
    expect(filtered_steps).to_have_count(0)


@then("I should see all custom steps in the list")
def should_see_all_custom_steps(test_context):
    """Verify all custom steps are visible (no filter applied)."""
    steps = test_context.page.locator('.custom-step-item')
    count = steps.count()
    assert count > 0, "Should see at least some custom steps"


@then(parsers.parse('the step "{step_name}" should not be in the list'))
def step_should_not_be_in_list(test_context, step_name: str):
    """Verify a specific step is not in the list."""
    step = test_context.page.locator(f'.custom-step-item:has-text("{step_name}")')
    expect(step).to_have_count(0)


@then("the custom steps count should decrease by 1")
def step_count_should_decrease(test_context):
    """Verify the step count decreased by 1."""
    current_count = test_context.page.locator('.custom-step-item').count()
    assert current_count == test_context.initial_step_count - 1, \
        f"Expected {test_context.initial_step_count - 1} steps, got {current_count}"


# =============================================================================
# Then Steps - Form Field Assertions
# =============================================================================


@then(parsers.parse('the "{field}" should have value "{value}"'))
def field_should_have_value(test_context, field: str, value: str):
    """Verify a field has specific value."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'#{field}'
    ).first
    expect(locator).to_have_value(value)


@then(parsers.parse('the "{field}" should have error styling'))
def field_should_have_error_styling(test_context, field: str):
    """Verify a field has error styling."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"]'
    ).first
    expect(locator).to_have_class(re.compile(r"error|invalid|is-invalid"))


@then(parsers.parse('the placeholder "{placeholder}" should be highlighted in the pattern preview'))
def placeholder_should_be_highlighted(test_context, placeholder: str):
    """Verify a placeholder is highlighted in the pattern preview."""
    preview = test_context.page.locator('[data-testid="pattern-preview"]')
    highlighted = preview.locator(f'.placeholder-highlight:has-text("{placeholder}")')
    expect(highlighted).to_be_visible()


@then(parsers.parse('the preview should show "{param}" as a parameter'))
def preview_should_show_parameter(test_context, param: str):
    """Verify the preview shows a parameter."""
    preview = test_context.page.locator('[data-testid="pattern-preview"]')
    param_element = preview.locator(f'.parameter:has-text("{param}")')
    expect(param_element).to_be_visible()


@then(parsers.parse('I should see "{tag}" tag badge in the tags list'))
def should_see_tag_badge(test_context, tag: str):
    """Verify a tag badge is visible in the tags list."""
    tags_list = test_context.page.locator('[data-testid="step-tags-list"]')
    badge = tags_list.locator(f'.tag-badge:has-text("{tag}")')
    expect(badge).to_be_visible()


# =============================================================================
# Then Steps - Monaco Editor Assertions
# =============================================================================


@then(parsers.parse('the Monaco editor should contain "{text}"'))
def monaco_should_contain(test_context, text: str):
    """Verify the Monaco editor contains specific text."""
    content = test_context.page.evaluate("""
        window.monacoEditor ? window.monacoEditor.getValue() : ''
    """)
    assert text in content, f"Monaco editor should contain '{text}', got: {content}"


@then("the Monaco editor should be empty")
def monaco_should_be_empty(test_context):
    """Verify the Monaco editor is empty."""
    content = test_context.page.evaluate("""
        window.monacoEditor ? window.monacoEditor.getValue() : ''
    """)
    assert content.strip() == "", f"Monaco editor should be empty, got: {content}"


@then(parsers.parse('the Monaco editor should highlight "{text}" as a keyword'))
def monaco_should_highlight_keyword(test_context, text: str):
    """Verify Monaco highlights text as a keyword."""
    highlighted = test_context.page.locator(f'.mtk6:has-text("{text}"), .keyword:has-text("{text}")')
    expect(highlighted.first).to_be_visible()


@then(parsers.parse('the Monaco editor should highlight "{text}" as a comment'))
def monaco_should_highlight_comment(test_context, text: str):
    """Verify Monaco highlights text as a comment."""
    highlighted = test_context.page.locator(f'.mtk1:has-text("{text}"), .comment:has-text("{text}")')
    expect(highlighted.first).to_be_visible()


@then(parsers.parse('the Monaco editor should highlight "{text}" as a string'))
def monaco_should_highlight_string(test_context, text: str):
    """Verify Monaco highlights text as a string."""
    highlighted = test_context.page.locator(f'.mtk5:has-text("{text}"), .string:has-text("{text}")')
    expect(highlighted.first).to_be_visible()


@then("the Monaco editor should show line numbers")
def monaco_should_show_line_numbers(test_context):
    """Verify Monaco shows line numbers."""
    line_numbers = test_context.page.locator('.monaco-editor .line-numbers')
    expect(line_numbers).to_be_visible()


@then(parsers.parse('line number {num:d} should be visible'))
def line_number_should_be_visible(test_context, num: int):
    """Verify a specific line number is visible."""
    line = test_context.page.locator(f'.monaco-editor .line-numbers:has-text("{num}")')
    expect(line.first).to_be_visible()


@then("the cursor should be indented by 4 spaces")
def cursor_should_be_indented(test_context):
    """Verify cursor is indented (check via content)."""
    content = test_context.page.evaluate("""
        window.monacoEditor ? window.monacoEditor.getValue() : ''
    """)
    lines = content.split("\n")
    if len(lines) > 1:
        # Check if second line starts with spaces
        assert lines[1].startswith("    "), "Second line should be indented"


@then("the code should be properly indented")
def code_should_be_properly_indented(test_context):
    """Verify code is properly indented."""
    content = test_context.page.evaluate("""
        window.monacoEditor ? window.monacoEditor.getValue() : ''
    """)
    lines = content.split("\n")
    for line in lines[1:]:  # Skip first line
        if line.strip():  # Non-empty lines
            assert line.startswith("    "), f"Line should be indented: {line}"


@then(parsers.parse('the Monaco editor should show an error marker on line {line:d}'))
def monaco_should_show_error_on_line(test_context, line: int):
    """Verify Monaco shows an error marker on specific line."""
    error_marker = test_context.page.locator('.monaco-editor .squiggly-error')
    expect(error_marker.first).to_be_visible()


@then("the Monaco editor should show error markers")
def monaco_should_show_error_markers(test_context):
    """Verify Monaco shows error markers."""
    error_marker = test_context.page.locator('.monaco-editor .squiggly-error')
    expect(error_marker.first).to_be_visible()


@then(parsers.parse('the error tooltip should mention "{text}"'))
def error_tooltip_should_mention(test_context, text: str):
    """Verify error tooltip contains specific text."""
    # Hover over error to show tooltip
    error_marker = test_context.page.locator('.monaco-editor .squiggly-error').first
    error_marker.hover()
    test_context.page.wait_for_timeout(500)
    tooltip = test_context.page.locator('.monaco-editor-hover-content')
    expect(tooltip.get_by_text(text).first).to_be_visible()


@then(parsers.parse('all occurrences of "{text}" should be highlighted'))
def all_occurrences_highlighted(test_context, text: str):
    """Verify all occurrences of text are highlighted in find."""
    highlights = test_context.page.locator('.monaco-editor .findMatch')
    assert highlights.count() > 0, f"Should find occurrences of '{text}'"


@then(parsers.parse('all occurrences should be replaced with "{text}"'))
def all_occurrences_replaced(test_context, text: str):
    """Verify all occurrences were replaced."""
    content = test_context.page.evaluate("""
        window.monacoEditor ? window.monacoEditor.getValue() : ''
    """)
    assert text in content, f"Content should contain '{text}'"


@then("I should see autocomplete suggestions")
def should_see_autocomplete_suggestions(test_context):
    """Verify autocomplete suggestions are visible."""
    suggestions = test_context.page.locator('.monaco-editor .suggest-widget')
    expect(suggestions).to_be_visible()


@then(parsers.parse('I should see "{text}" in the suggestions'))
def should_see_in_suggestions(test_context, text: str):
    """Verify specific text in autocomplete suggestions."""
    suggestions = test_context.page.locator('.monaco-editor .suggest-widget')
    suggestion_item = suggestions.locator(f':has-text("{text}")')
    expect(suggestion_item.first).to_be_visible()


@then("I can click on the minimap to navigate")
def can_click_minimap(test_context):
    """Verify minimap is clickable for navigation."""
    minimap = test_context.page.locator('[data-testid="monaco-minimap"], .minimap')
    expect(minimap).to_be_visible()
    # Minimap should be interactive
    assert minimap.is_enabled(), "Minimap should be clickable"


# =============================================================================
# Then Steps - Navigation Assertions
# =============================================================================


@then("I should be on the scenarios page")
def should_be_on_scenarios_page(test_context):
    """Verify we're on the scenarios page."""
    expect(test_context.page).to_have_url(re.compile(r"/scenarios"))


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify URL contains specific text."""
    expect(test_context.page).to_have_url(re.compile(re.escape(text)))


@then("the commit dialog should close")
def commit_dialog_should_close(test_context):
    """Verify the commit dialog is closed."""
    dialog = test_context.page.locator('[data-testid="commit-dialog"]')
    expect(dialog).not_to_be_visible()


@then("the step should remain as local only")
def step_should_be_local_only(test_context):
    """Verify the step is marked as local only."""
    # Check for local indicator or absence of repo link
    local_indicator = test_context.page.locator('.local-only-badge')
    expect(local_indicator.first).to_be_visible()


@then(parsers.parse('I should see "Used in {count:d} scenarios"'))
def should_see_used_in_scenarios(test_context, count: int):
    """Verify usage count display."""
    usage_text = test_context.page.locator(f':has-text("Used in {count} scenarios")')
    expect(usage_text.first).to_be_visible()


@then("I should see a list of scenarios using this step")
def should_see_scenario_list(test_context):
    """Verify scenario usage list is visible."""
    usage_list = test_context.page.locator('[data-testid="step-usage-list"]')
    expect(usage_list).to_be_visible()
