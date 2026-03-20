"""
Test module for Environments Management UI tests.

This module connects pytest-bdd scenarios from test_frontend_environments.feature
to step definitions for UI testing with Playwright.
"""

import os
import re
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_frontend_environments.feature")


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

    class TestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.user_email: Optional[str] = None
            self.user_name: Optional[str] = None
            self.auth_token: Optional[str] = None
            self.variables: dict = {}
            self.environments: list = []
            self.current_environment: Optional[dict] = None
            self.initial_env_count: int = 0

    return TestContext()


@pytest.fixture
def environment_state():
    """Track environment state for tests."""
    return {
        "environments": [],
        "current_environment": None,
        "variable_count": 0,
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
            picture: 'https://ui-avatars.com/api/?name={test_context.user_name.replace(" ", "+")}'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Given Steps - Navigation
# =============================================================================


@given(parsers.parse('I am on the "{page_name}" page'))
def on_page(test_context, page_name: str):
    """Navigate to a specific page."""
    test_context.page.goto(f"{test_context.base_url}/{page_name}")
    test_context.page.wait_for_load_state("networkidle")


@given(parsers.parse('I am on the environment details page for "{env_name}"'))
def on_environment_details_page(test_context, env_name: str):
    """Navigate to environment details page."""
    # Mock environment ID
    env_id = f"mock-env-id-{env_name}"
    test_context.page.goto(f"{test_context.base_url}/environments/{env_id}")
    test_context.page.wait_for_load_state("networkidle")
    test_context.current_environment = {"name": env_name, "id": env_id}


# =============================================================================
# Given Steps - Environment Setup
# =============================================================================


@given("at least one environment exists")
def at_least_one_environment_exists(test_context):
    """Ensure at least one environment exists in the system."""
    test_context.variables["has_environments"] = True


@given("no environments exist")
def no_environments_exist(test_context):
    """Ensure no environments exist in the system."""
    test_context.variables["has_environments"] = False


@given("multiple environments exist")
def multiple_environments_exist(test_context):
    """Ensure multiple environments exist."""
    test_context.environments = [
        {"name": "alpha-env", "url": "https://alpha.example.com"},
        {"name": "beta-env", "url": "https://beta.example.com"},
        {"name": "gamma-env", "url": "https://gamma.example.com"},
    ]


@given(parsers.parse('an environment with {count:d} variables exists'))
def environment_with_variable_count(test_context, count: int):
    """Ensure an environment with specific variable count exists."""
    test_context.variables["expected_variable_count"] = count


@given(parsers.parse('an environment with name "{name}" exists'))
def environment_with_name_exists(test_context, name: str):
    """Ensure an environment with specific name exists."""
    test_context.current_environment = {
        "name": name,
        "id": f"mock-env-id-{name}",
        "base_url": "https://test.example.com",
    }


@given(parsers.parse('an environment with name "{name}" and url "{url}" exists'))
def environment_with_name_and_url_exists(test_context, name: str, url: str):
    """Ensure an environment with specific name and URL exists."""
    test_context.current_environment = {
        "name": name,
        "id": f"mock-env-id-{name}",
        "base_url": url,
    }


@given(parsers.parse('an environment with name "{name}" and {count:d} variable exists'))
@given(parsers.parse('an environment with name "{name}" and {count:d} variables exists'))
def environment_with_name_and_variables(test_context, name: str, count: int):
    """Ensure an environment with specific name and variable count exists."""
    test_context.current_environment = {
        "name": name,
        "id": f"mock-env-id-{name}",
        "base_url": "https://test.example.com",
        "variable_count": count,
    }


@given(parsers.parse('environments "{env1}", "{env2}", "{env3}" exist'))
def specific_environments_exist(test_context, env1: str, env2: str, env3: str):
    """Ensure specific environments exist."""
    test_context.environments = [
        {"name": env1, "url": f"https://{env1}.example.com"},
        {"name": env2, "url": f"https://{env2}.example.com"},
        {"name": env3, "url": f"https://{env3}.example.com"},
    ]


@given(parsers.parse('environments "{env1}", "{env2}" exist'))
def two_environments_exist(test_context, env1: str, env2: str):
    """Ensure two specific environments exist."""
    test_context.environments = [
        {"name": env1, "url": f"https://{env1}.example.com"},
        {"name": env2, "url": f"https://{env2}.example.com"},
    ]


@given(parsers.parse('I have filtered by "{filter_text}"'))
def have_filtered_by(test_context, filter_text: str):
    """Apply a filter to the environments list."""
    search_input = test_context.page.locator(
        '[data-testid="environment-search"], input[placeholder*="search" i]'
    ).first
    search_input.fill(filter_text)
    test_context.page.wait_for_timeout(300)


@given("the create environment modal is open")
def create_environment_modal_is_open(test_context):
    """Ensure the create environment modal is open."""
    create_btn = test_context.page.locator(
        '[data-testid="create-environment-btn"], '
        'button:has-text("Create Environment")'
    ).first
    create_btn.click()
    expect(test_context.page.locator('[data-testid="create-environment-modal"]')).to_be_visible()


@given(parsers.parse('I have added {count:d} variables'))
def have_added_variables(test_context, count: int):
    """Add multiple variables in the modal."""
    for i in range(count):
        add_btn = test_context.page.locator(
            '[data-testid="add-variable-btn"], button:has-text("Add Variable")'
        ).first
        add_btn.click()
        # Fill variable data
        key_input = test_context.page.locator(f'[data-testid="variable-key-{i + 1}"]').first
        value_input = test_context.page.locator(f'[data-testid="variable-value-{i + 1}"]').first
        if i == 0:
            key_input.fill("API_KEY")
            value_input.fill("secret123")
        else:
            key_input.fill("TIMEOUT")
            value_input.fill("30")


@given(parsers.parse('the environment "{env_name}" is used by a scheduled run'))
def environment_used_by_scheduled_run(test_context, env_name: str):
    """Mark environment as being used by a scheduled run."""
    test_context.variables["environment_in_use"] = env_name


@given(parsers.parse('an environment with name "{name}" and variables exists:'))
def environment_with_specific_variables(test_context, name: str, datatable):
    """Ensure an environment with specific variables exists."""
    variables = []
    for row in datatable:
        variables.append({"key": row["key"], "value": row["value"]})
    test_context.current_environment = {
        "name": name,
        "id": f"mock-env-id-{name}",
        "base_url": "https://test.example.com",
        "variables": variables,
    }


@given(parsers.parse('an environment with name "{name}" and sensitive variables exists:'))
def environment_with_sensitive_variables(test_context, name: str, datatable):
    """Ensure an environment with sensitive variables exists."""
    variables = []
    for row in datatable:
        variables.append({
            "key": row["key"],
            "value": row["value"],
            "sensitive": row.get("sensitive", "false").lower() == "true",
        })
    test_context.current_environment = {
        "name": name,
        "id": f"mock-env-id-{name}",
        "base_url": "https://test.example.com",
        "variables": variables,
    }


@given(parsers.parse('the variable "{var_name}" is masked'))
def variable_is_masked(test_context, var_name: str):
    """Ensure a variable is in masked state."""
    pass  # Default state is masked for sensitive variables


@given(parsers.parse('the environment has variable "{var_name}" with value "{value}"'))
def environment_has_variable(test_context, var_name: str, value: str):
    """Set a specific variable on the current environment."""
    if not test_context.current_environment:
        test_context.current_environment = {"variables": []}
    if "variables" not in test_context.current_environment:
        test_context.current_environment["variables"] = []
    test_context.current_environment["variables"].append({
        "key": var_name,
        "value": value,
    })


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I wait for the page to load")
def wait_for_page_to_load(test_context):
    """Wait for the page to fully load."""
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I click on the environment "{name}"'))
def click_on_environment(test_context, name: str):
    """Click on an environment in the list."""
    env_row = test_context.page.locator(f'.environment-item:has-text("{name}")')
    env_row.click()
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I click the sort button for "{field}"'))
def click_sort_button(test_context, field: str):
    """Click the sort button for a specific field."""
    sort_btn = test_context.page.locator(
        f'[data-testid="sort-{field}-btn"], '
        f'th:has-text("{field.title()}") .sort-btn'
    ).first
    sort_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the sort button for "{field}" twice'))
def click_sort_button_twice(test_context, field: str):
    """Click the sort button twice for descending order."""
    sort_btn = test_context.page.locator(
        f'[data-testid="sort-{field}-btn"], '
        f'th:has-text("{field.title()}") .sort-btn'
    ).first
    sort_btn.click()
    test_context.page.wait_for_timeout(200)
    sort_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I enter "{text}" into the search field'))
def enter_text_into_search(test_context, text: str):
    """Enter text into the search field."""
    search_input = test_context.page.locator(
        '[data-testid="environment-search"], '
        'input[placeholder*="search" i], '
        'input[type="search"]'
    ).first
    search_input.fill(text)
    test_context.page.wait_for_timeout(300)


@when("I clear the search field")
def clear_search_field(test_context):
    """Clear the search field."""
    search_input = test_context.page.locator(
        '[data-testid="environment-search"], '
        'input[placeholder*="search" i], '
        'input[type="search"]'
    ).first
    search_input.clear()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{button_text}" button'))
def click_button_by_text(test_context, button_text: str):
    """Click a button by its text."""
    button = test_context.page.get_by_role("button", name=button_text).first
    button.click()
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I click the link "{link_text}"'))
def click_link_by_text(test_context, link_text: str):
    """Click a link by its text."""
    link = test_context.page.get_by_role("link", name=link_text).first
    link.click()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Form Interactions
# =============================================================================


@when(parsers.parse('I fill the environment form with name "{name}"'))
def fill_environment_name(test_context, name: str):
    """Fill the environment name field."""
    input_field = test_context.page.locator(
        '[data-testid="environment-name-input"], '
        'input[name="name"], '
        'input[placeholder*="name" i]'
    ).first
    input_field.fill(name)


@when(parsers.parse('I fill the environment form with url "{url}"'))
def fill_environment_url(test_context, url: str):
    """Fill the environment URL field."""
    input_field = test_context.page.locator(
        '[data-testid="environment-url-input"], '
        'input[name="base_url"], '
        'input[placeholder*="url" i]'
    ).first
    input_field.fill(url)


@when(parsers.parse('I fill variable {num:d} with key "{key}" and value "{value}"'))
def fill_variable_by_number(test_context, num: int, key: str, value: str):
    """Fill a specific variable row."""
    key_input = test_context.page.locator(
        f'[data-testid="variable-key-{num}"], '
        f'.variable-row:nth-child({num}) input[name="key"]'
    ).first
    value_input = test_context.page.locator(
        f'[data-testid="variable-value-{num}"], '
        f'.variable-row:nth-child({num}) input[name="value"]'
    ).first
    key_input.fill(key)
    value_input.fill(value)


@when(parsers.parse('I fill the new variable with key "{key}" and value "{value}"'))
def fill_new_variable(test_context, key: str, value: str):
    """Fill the most recently added variable row."""
    key_inputs = test_context.page.locator(
        '[data-testid^="variable-key-"], .variable-row input[name="key"]'
    )
    value_inputs = test_context.page.locator(
        '[data-testid^="variable-value-"], .variable-row input[name="value"]'
    )
    key_inputs.last.fill(key)
    value_inputs.last.fill(value)


@when(parsers.parse('I click the remove button for variable {num:d}'))
def click_remove_variable_button(test_context, num: int):
    """Click the remove button for a specific variable."""
    remove_btn = test_context.page.locator(
        f'[data-testid="remove-variable-{num}"], '
        f'.variable-row:nth-child({num}) .remove-btn'
    ).first
    remove_btn.click()


@when("I click the remove button for the first variable")
def click_remove_first_variable(test_context):
    """Click the remove button for the first variable."""
    remove_btn = test_context.page.locator(
        '[data-testid="remove-variable-1"], '
        '.variable-row:first-child .remove-btn, '
        '.variable-row .remove-btn'
    ).first
    remove_btn.click()


@when(parsers.parse('I click the edit button for environment "{name}"'))
def click_edit_environment_button(test_context, name: str):
    """Click the edit button for a specific environment."""
    env_row = test_context.page.locator(f'.environment-item:has-text("{name}")')
    edit_btn = env_row.locator('.edit-btn, [data-testid="edit-environment-btn"]')
    edit_btn.click()


@when(parsers.parse('I click the delete button for environment "{name}"'))
def click_delete_environment_button(test_context, name: str):
    """Click the delete button for a specific environment."""
    # Store initial count for comparison
    env_list = test_context.page.locator('.environment-item')
    test_context.initial_env_count = env_list.count()

    env_row = test_context.page.locator(f'.environment-item:has-text("{name}")')
    delete_btn = env_row.locator('.delete-btn, [data-testid="delete-environment-btn"]')
    delete_btn.click()


@when(parsers.parse('I clear the "{field}" field'))
def clear_field(test_context, field: str):
    """Clear a specific input field."""
    input_field = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field.replace("-input", "")}"]'
    ).first
    input_field.clear()


@when(parsers.parse('I enter "{text}" into the "{field}" field'))
def enter_text_into_field(test_context, text: str, field: str):
    """Enter text into a specific field."""
    input_field = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field.replace("-input", "")}"]'
    ).first
    input_field.fill(text)


@when("I refresh the page")
def refresh_page(test_context):
    """Refresh the current page."""
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Variables Editor
# =============================================================================


@when(parsers.parse('I click the show value button for "{var_name}"'))
def click_show_value_button(test_context, var_name: str):
    """Click the show value button for a variable."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    show_btn = var_row.locator(
        '.show-value-btn, '
        '[data-testid="show-value-btn"], '
        'button[aria-label*="show" i]'
    )
    show_btn.click()


@when(parsers.parse('I click the copy button for variable "{var_name}"'))
def click_copy_variable_button(test_context, var_name: str):
    """Click the copy button for a variable."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    copy_btn = var_row.locator(
        '.copy-btn, '
        '[data-testid="copy-variable-btn"], '
        'button[aria-label*="copy" i]'
    )
    copy_btn.click()


@when(parsers.parse('I click the edit button for variable "{var_name}"'))
def click_edit_variable_button(test_context, var_name: str):
    """Click the edit button for a variable."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    edit_btn = var_row.locator(
        '.edit-variable-btn, '
        '[data-testid="edit-variable-btn"]'
    )
    edit_btn.click()


@when("I clear the variable value input")
def clear_variable_value_input(test_context):
    """Clear the variable value input that is in edit mode."""
    input_field = test_context.page.locator(
        '.variable-row.editing input[name="value"], '
        '.variable-value-input:focus, '
        '[data-testid="variable-value-edit-input"]'
    ).first
    input_field.clear()


@when(parsers.parse('I enter "{text}" into the variable value input'))
def enter_variable_value(test_context, text: str):
    """Enter text into the variable value input."""
    input_field = test_context.page.locator(
        '.variable-row.editing input[name="value"], '
        '.variable-value-input:focus, '
        '[data-testid="variable-value-edit-input"]'
    ).first
    input_field.fill(text)


@when(parsers.parse('I click the "{button_text}" button for the variable'))
def click_variable_button(test_context, button_text: str):
    """Click a button within the variable editing context."""
    var_row = test_context.page.locator('.variable-row.editing, .variable-row:has(.editing)')
    button = var_row.get_by_role("button", name=button_text)
    button.click()


# =============================================================================
# Then Steps - Visibility Assertions
# =============================================================================


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible."""
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


@then(parsers.parse('I should see "{text}"'))
def should_see_text(test_context, text: str):
    """Verify text is visible on page."""
    expect(test_context.page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should not see "{text}"'))
def should_not_see_text(test_context, text: str):
    """Verify text is not visible on page."""
    locator = test_context.page.get_by_text(text, exact=True)
    expect(locator).to_have_count(0)


@then("I should see the environment name")
def should_see_environment_name(test_context):
    """Verify environment name is visible."""
    locator = test_context.page.locator(
        '.environment-name, '
        '[data-testid="environment-name"]'
    ).first
    expect(locator).to_be_visible()


@then("I should see the environment URL")
def should_see_environment_url(test_context):
    """Verify environment URL is visible."""
    locator = test_context.page.locator(
        '.environment-url, '
        '[data-testid="environment-url"]'
    ).first
    expect(locator).to_be_visible()


@then("I should see the environment base URL")
def should_see_environment_base_url(test_context):
    """Verify environment base URL is visible."""
    locator = test_context.page.locator(
        '.environment-base-url, '
        '.environment-url, '
        '[data-testid="environment-base-url"]'
    ).first
    expect(locator).to_be_visible()


@then(parsers.parse('I should see "{count} variables" for the environment'))
def should_see_variable_count(test_context, count: str):
    """Verify variable count is displayed."""
    locator = test_context.page.locator(
        f'.variable-count:has-text("{count}"), '
        f'[data-testid="variable-count"]:has-text("{count}")'
    )
    expect(locator.first).to_be_visible()


@then("I should see a variable key input")
def should_see_variable_key_input(test_context):
    """Verify variable key input is visible."""
    locator = test_context.page.locator(
        '[data-testid^="variable-key-"], '
        '.variable-row input[name="key"]'
    ).first
    expect(locator).to_be_visible()


@then("I should see a variable value input")
def should_see_variable_value_input(test_context):
    """Verify variable value input is visible."""
    locator = test_context.page.locator(
        '[data-testid^="variable-value-"], '
        '.variable-row input[name="value"]'
    ).first
    expect(locator).to_be_visible()


@then(parsers.parse('I should see {count:d} variable rows'))
@then(parsers.parse('I should see {count:d} variable row'))
def should_see_variable_row_count(test_context, count: int):
    """Verify the number of variable rows."""
    rows = test_context.page.locator('.variable-row')
    expect(rows).to_have_count(count)


@then(parsers.parse('variable {num:d} should have key "{key}"'))
def variable_should_have_key(test_context, num: int, key: str):
    """Verify a specific variable has the expected key."""
    key_input = test_context.page.locator(
        f'[data-testid="variable-key-{num}"], '
        f'.variable-row:nth-child({num}) input[name="key"]'
    ).first
    expect(key_input).to_have_value(key)


# =============================================================================
# Then Steps - Navigation Assertions
# =============================================================================


@then("I should be on the environment details page")
def should_be_on_environment_details_page(test_context):
    """Verify we're on the environment details page."""
    expect(test_context.page).to_have_url(re.compile(r"/environments/"))


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify URL contains specified text."""
    expect(test_context.page).to_have_url(re.compile(re.escape(text)))


@then(parsers.parse('I should be on the "{page_name}" page'))
def should_be_on_page(test_context, page_name: str):
    """Verify we're on a specific page."""
    expect(test_context.page).to_have_url(re.compile(rf"/{page_name}"))


# =============================================================================
# Then Steps - Form Assertions
# =============================================================================


@then(parsers.parse('the "{element}" should have value "{value}"'))
def element_should_have_value(test_context, element: str, value: str):
    """Verify an input element has a specific value."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], '
        f'input[name="{element.replace("-input", "")}"]'
    ).first
    expect(locator).to_have_value(value)


@then(parsers.parse('the "{element}" should have class "{class_name}"'))
def element_should_have_class(test_context, element: str, class_name: str):
    """Verify an element has a specific CSS class."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).to_have_class(re.compile(class_name))


# =============================================================================
# Then Steps - List Assertions
# =============================================================================


@then(parsers.parse('I should see "{name}" in the environments list'))
def should_see_name_in_environments_list(test_context, name: str):
    """Verify an environment name appears in the list."""
    locator = test_context.page.locator(
        f'[data-testid="environments-list"] .environment-name:has-text("{name}"), '
        f'.environments-list .environment-item:has-text("{name}")'
    )
    expect(locator.first).to_be_visible()


@then(parsers.parse('I should not see "{name}" in the environments list'))
def should_not_see_name_in_environments_list(test_context, name: str):
    """Verify an environment name does not appear in the list."""
    locator = test_context.page.locator(
        f'[data-testid="environments-list"] .environment-name:has-text("{name}"), '
        f'.environments-list .environment-item:has-text("{name}")'
    )
    expect(locator).to_have_count(0)


@then("the environments should be sorted by name ascending")
def environments_sorted_ascending(test_context):
    """Verify environments are sorted by name ascending."""
    names = test_context.page.locator('.environment-name').all_text_contents()
    assert names == sorted(names), f"Expected ascending order, got: {names}"


@then("the environments should be sorted by name descending")
def environments_sorted_descending(test_context):
    """Verify environments are sorted by name descending."""
    names = test_context.page.locator('.environment-name').all_text_contents()
    assert names == sorted(names, reverse=True), f"Expected descending order, got: {names}"


@then(parsers.parse('the environment "{name}" should have url "{url}"'))
def environment_should_have_url(test_context, name: str, url: str):
    """Verify an environment has a specific URL."""
    env_row = test_context.page.locator(f'.environment-item:has-text("{name}")')
    url_element = env_row.locator('.environment-url')
    expect(url_element).to_contain_text(url)


@then(parsers.parse('the environment should have {count:d} variables'))
@then(parsers.parse('the environment should have {count:d} variable'))
def environment_should_have_variable_count(test_context, count: int):
    """Verify the environment has a specific number of variables."""
    var_count = test_context.page.locator(
        '.variable-count, '
        '[data-testid="variable-count"]'
    ).first
    expect(var_count).to_contain_text(str(count))


@then(parsers.parse('the environment "{name}" should be removed from the list'))
def environment_removed_from_list(test_context, name: str):
    """Verify an environment has been removed from the list."""
    locator = test_context.page.locator(f'.environment-item:has-text("{name}")')
    expect(locator).to_have_count(0)


@then("the environments count should decrease by 1")
def environments_count_decreased(test_context):
    """Verify the environments count decreased by 1."""
    env_list = test_context.page.locator('.environment-item')
    current_count = env_list.count()
    assert current_count == test_context.initial_env_count - 1, \
        f"Expected count {test_context.initial_env_count - 1}, got {current_count}"


# =============================================================================
# Then Steps - Variables Assertions
# =============================================================================


@then(parsers.parse('I should see variable "{var_name}"'))
def should_see_variable(test_context, var_name: str):
    """Verify a variable is displayed."""
    locator = test_context.page.locator(
        f'.variable-row:has-text("{var_name}"), '
        f'[data-testid="variable-{var_name}"]'
    )
    expect(locator.first).to_be_visible()


@then(parsers.parse('the value for "{var_name}" should be masked'))
def variable_value_should_be_masked(test_context, var_name: str):
    """Verify a variable value is masked."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    value_element = var_row.locator('.variable-value')
    expect(value_element).to_have_class(re.compile(r"masked|hidden"))


@then(parsers.parse('I should see "********" for variable "{var_name}"'))
def should_see_masked_value(test_context, var_name: str):
    """Verify masked value display."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    value_element = var_row.locator('.variable-value')
    expect(value_element).to_contain_text("********")


@then(parsers.parse('the value for "{var_name}" should be visible'))
def variable_value_should_be_visible(test_context, var_name: str):
    """Verify a variable value is visible (unmasked)."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    value_element = var_row.locator('.variable-value')
    expect(value_element).not_to_have_class(re.compile(r"masked|hidden"))


@then(parsers.parse('I should see "{value}" for variable "{var_name}"'))
def should_see_variable_value(test_context, value: str, var_name: str):
    """Verify a variable has a specific value displayed."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    value_element = var_row.locator('.variable-value')
    expect(value_element).to_contain_text(value)


@then(parsers.parse('the "{element}" should be visible for "{var_name}"'))
def element_should_be_visible_for_variable(test_context, element: str, var_name: str):
    """Verify an element is visible within a variable row."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    locator = var_row.locator(f'[data-testid="{element}"], .{element}')
    expect(locator.first).to_be_visible()


@then(parsers.parse('the clipboard should contain "{text}"'))
def clipboard_should_contain(test_context, text: str):
    """Verify clipboard contains specific text."""
    # Note: Clipboard access may require browser permissions
    clipboard_content = test_context.page.evaluate("navigator.clipboard.readText()")
    assert text in clipboard_content, f"Expected '{text}' in clipboard, got '{clipboard_content}'"


@then(parsers.parse('the variable "{var_name}" should have value "{value}"'))
def variable_should_have_value(test_context, var_name: str, value: str):
    """Verify a variable has a specific value."""
    var_row = test_context.page.locator(f'.variable-row:has-text("{var_name}")')
    value_element = var_row.locator('.variable-value')
    expect(value_element).to_contain_text(value)


# =============================================================================
# Then Steps - Breadcrumb
# =============================================================================


@then(parsers.parse('I should see "{text}" in the breadcrumb'))
def should_see_text_in_breadcrumb(test_context, text: str):
    """Verify text appears in the breadcrumb."""
    breadcrumb = test_context.page.locator('[data-testid="breadcrumb"], .breadcrumb')
    expect(breadcrumb.get_by_text(text)).to_be_visible()
