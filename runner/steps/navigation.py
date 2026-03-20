"""Navigation step definitions."""

from pytest_bdd import given, when, then, parsers


@given(parsers.parse('I am on the "{page_name}" page'))
def given_on_page(test_context, page_name: str):
    """Navigate to a named page."""
    page_urls = {
        "home": "/",
        "dashboard": "/dashboard",
        "login": "/login",
        "scenarios": "/scenarios",
        "runs": "/runs",
        "environments": "/environments",
        "settings": "/settings",
    }
    url = page_urls.get(page_name.lower(), f"/{page_name.lower()}")
    full_url = f"{test_context.base_url}{url}"
    test_context.page.goto(full_url)


@given(parsers.parse('I navigate to "{url}"'))
@when(parsers.parse('I navigate to "{url}"'))
def navigate_to_url(test_context, url: str):
    """Navigate to a specific URL."""
    if url.startswith("http"):
        test_context.page.goto(url)
    else:
        test_context.page.goto(f"{test_context.base_url}{url}")


@when(parsers.parse('I click the "{element}" button'))
def click_button(test_context, element: str):
    """Click a button by text or role."""
    test_context.page.get_by_role("button", name=element).click()


@when(parsers.parse('I click on "{text}"'))
def click_on_text(test_context, text: str):
    """Click on element containing text."""
    test_context.page.get_by_text(text).click()


@when(parsers.parse('I click the link "{text}"'))
def click_link(test_context, text: str):
    """Click a link by text."""
    test_context.page.get_by_role("link", name=text).click()


@when(parsers.parse('I go back'))
def go_back(test_context):
    """Navigate back in browser history."""
    test_context.page.go_back()


@when(parsers.parse('I go forward'))
def go_forward(test_context):
    """Navigate forward in browser history."""
    test_context.page.go_forward()


@when(parsers.parse('I refresh the page'))
def refresh_page(test_context):
    """Refresh the current page."""
    test_context.page.reload()


@then(parsers.parse('I should be on the "{page_name}" page'))
def should_be_on_page(test_context, page_name: str):
    """Verify we're on the expected page."""
    page_patterns = {
        "home": r"/$",
        "dashboard": r"/dashboard",
        "login": r"/login",
        "scenarios": r"/scenarios",
        "runs": r"/runs",
        "environments": r"/environments",
        "settings": r"/settings",
    }
    pattern = page_patterns.get(page_name.lower(), f"/{page_name.lower()}")
    test_context.page.wait_for_url(f"**{pattern}*")


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify URL contains text."""
    assert text in test_context.page.url, f"URL '{test_context.page.url}' does not contain '{text}'"
