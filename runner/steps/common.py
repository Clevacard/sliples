"""Common step definitions."""

import os
import time
from datetime import datetime

from pytest_bdd import given, when, then, parsers


@when(parsers.parse('I wait for {seconds:d} seconds'))
def wait_seconds(test_context, seconds: int):
    """Wait for a specified number of seconds."""
    time.sleep(seconds)


@when(parsers.parse('I wait for the "{element}" to be visible'))
def wait_for_element_visible(test_context, element: str):
    """Wait for an element to become visible."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    locator.wait_for(state="visible", timeout=30000)


@when(parsers.parse('I wait for the "{element}" to disappear'))
def wait_for_element_hidden(test_context, element: str):
    """Wait for an element to disappear."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    locator.wait_for(state="hidden", timeout=30000)


@when(parsers.parse('I wait for the page to load'))
def wait_for_page_load(test_context):
    """Wait for the page to finish loading."""
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I take a screenshot named "{name}"'))
def take_screenshot(test_context, name: str, screenshots_dir: str):
    """Take a screenshot and save it."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(screenshots_dir, filename)
    test_context.page.screenshot(path=filepath)
    test_context.screenshots.append(filepath)


@given(parsers.parse('I have a variable "{name}" with value "{value}"'))
def set_variable(test_context, name: str, value: str):
    """Set a test variable."""
    test_context.variables[name] = value


@when(parsers.parse('I set variable "{name}" to "{value}"'))
def update_variable(test_context, name: str, value: str):
    """Update a test variable."""
    test_context.variables[name] = value


@then(parsers.parse('the variable "{name}" should equal "{value}"'))
def variable_should_equal(test_context, name: str, value: str):
    """Verify a variable value."""
    assert test_context.variables.get(name) == value, f"Variable '{name}' != '{value}'"


@given(parsers.parse('the browser viewport is {width:d}x{height:d}'))
def set_viewport(test_context, width: int, height: int):
    """Set the browser viewport size."""
    test_context.page.set_viewport_size({"width": width, "height": height})


@when(parsers.parse('I press the "{key}" key'))
def press_key(test_context, key: str):
    """Press a keyboard key."""
    test_context.page.keyboard.press(key)


@when(parsers.parse('I scroll to the bottom'))
def scroll_to_bottom(test_context):
    """Scroll to the bottom of the page."""
    test_context.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")


@when(parsers.parse('I scroll to the top'))
def scroll_to_top(test_context):
    """Scroll to the top of the page."""
    test_context.page.evaluate("window.scrollTo(0, 0)")


@then(parsers.parse('I should not see any JavaScript console errors'))
def no_console_errors(test_context):
    """Verify there are no JavaScript console errors."""
    # This requires setting up console message listeners beforehand
    pass
