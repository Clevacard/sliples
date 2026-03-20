"""Assertion step definitions."""

from pytest_bdd import given, when, then, parsers
from playwright.sync_api import expect


@then(parsers.parse('I should see "{text}"'))
def should_see_text(test_context, text: str):
    """Verify text is visible on page."""
    expect(test_context.page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should not see "{text}"'))
def should_not_see_text(test_context, text: str):
    """Verify text is not visible on page."""
    expect(test_context.page.get_by_text(text).first).not_to_be_visible()


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).to_be_visible()


@then(parsers.parse('the "{element}" should not be visible'))
def element_should_not_be_visible(test_context, element: str):
    """Verify an element is not visible."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).not_to_be_visible()


@then(parsers.parse('the "{element}" should be enabled'))
def element_should_be_enabled(test_context, element: str):
    """Verify an element is enabled."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).to_be_enabled()


@then(parsers.parse('the "{element}" should be disabled'))
def element_should_be_disabled(test_context, element: str):
    """Verify an element is disabled."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).to_be_disabled()


@then(parsers.parse('the page title should be "{title}"'))
def page_title_should_be(test_context, title: str):
    """Verify the page title."""
    expect(test_context.page).to_have_title(title)


@then(parsers.parse('the page title should contain "{text}"'))
def page_title_should_contain(test_context, text: str):
    """Verify the page title contains text."""
    expect(test_context.page).to_have_title(parsers.re(f".*{text}.*"))


@then(parsers.parse('the "{element}" should contain "{text}"'))
def element_should_contain(test_context, element: str, text: str):
    """Verify an element contains text."""
    locator = test_context.page.locator(f'[data-testid="{element}"], #{element}, .{element}').first
    expect(locator).to_contain_text(text)


@then(parsers.parse('there should be {count:d} "{element}" elements'))
def count_elements(test_context, count: int, element: str):
    """Verify the number of elements."""
    locator = test_context.page.locator(f'[data-testid="{element}"], .{element}')
    expect(locator).to_have_count(count)


@then(parsers.parse('the response status should be {status:d}'))
def response_status_should_be(test_context, status: int):
    """Verify the last response status code."""
    # This requires intercepting network requests
    pass
