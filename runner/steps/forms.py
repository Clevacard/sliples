"""Form interaction step definitions."""

from pytest_bdd import given, when, then, parsers


@when(parsers.parse('I enter "{value}" into the "{field}" field'))
def enter_into_field(test_context, value: str, field: str):
    """Enter text into a form field."""
    # Try multiple selectors
    locator = test_context.page.locator(
        f'input[name="{field}"], '
        f'input[placeholder*="{field}" i], '
        f'textarea[name="{field}"], '
        f'[data-testid="{field}"]'
    ).first
    locator.fill(value)


@when(parsers.parse('I type "{value}" into the "{field}" field'))
def type_into_field(test_context, value: str, field: str):
    """Type text into a form field (key by key)."""
    locator = test_context.page.locator(
        f'input[name="{field}"], '
        f'input[placeholder*="{field}" i], '
        f'textarea[name="{field}"], '
        f'[data-testid="{field}"]'
    ).first
    locator.type(value)


@when(parsers.parse('I clear the "{field}" field'))
def clear_field(test_context, field: str):
    """Clear a form field."""
    locator = test_context.page.locator(
        f'input[name="{field}"], '
        f'input[placeholder*="{field}" i], '
        f'textarea[name="{field}"], '
        f'[data-testid="{field}"]'
    ).first
    locator.clear()


@when(parsers.parse('I select "{option}" from "{dropdown}"'))
def select_from_dropdown(test_context, option: str, dropdown: str):
    """Select an option from a dropdown."""
    locator = test_context.page.locator(
        f'select[name="{dropdown}"], '
        f'[data-testid="{dropdown}"]'
    ).first
    locator.select_option(label=option)


@when(parsers.parse('I check the "{checkbox}" checkbox'))
def check_checkbox(test_context, checkbox: str):
    """Check a checkbox."""
    locator = test_context.page.locator(
        f'input[type="checkbox"][name="{checkbox}"], '
        f'input[type="checkbox"][id="{checkbox}"], '
        f'[data-testid="{checkbox}"]'
    ).first
    locator.check()


@when(parsers.parse('I uncheck the "{checkbox}" checkbox'))
def uncheck_checkbox(test_context, checkbox: str):
    """Uncheck a checkbox."""
    locator = test_context.page.locator(
        f'input[type="checkbox"][name="{checkbox}"], '
        f'input[type="checkbox"][id="{checkbox}"], '
        f'[data-testid="{checkbox}"]'
    ).first
    locator.uncheck()


@when(parsers.parse('I submit the form'))
def submit_form(test_context):
    """Submit the current form."""
    test_context.page.locator('form').first.locator('button[type="submit"]').click()


@then(parsers.parse('the "{field}" field should have value "{value}"'))
def field_should_have_value(test_context, field: str, value: str):
    """Verify a field has the expected value."""
    locator = test_context.page.locator(
        f'input[name="{field}"], '
        f'textarea[name="{field}"], '
        f'[data-testid="{field}"]'
    ).first
    assert locator.input_value() == value, f"Field '{field}' has unexpected value"


@then(parsers.parse('the "{field}" field should be empty'))
def field_should_be_empty(test_context, field: str):
    """Verify a field is empty."""
    locator = test_context.page.locator(
        f'input[name="{field}"], '
        f'textarea[name="{field}"], '
        f'[data-testid="{field}"]'
    ).first
    assert locator.input_value() == "", f"Field '{field}' is not empty"
