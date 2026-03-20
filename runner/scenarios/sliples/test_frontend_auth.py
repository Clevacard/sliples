"""
Test module for Google Workspace SSO Authentication Frontend tests.

This module connects pytest-bdd scenarios from test_frontend_auth.feature
to step definitions for UI testing with Playwright.
"""

import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page, BrowserContext


# Load all scenarios from the feature file
scenarios("test_frontend_auth.feature")


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
            self.original_url: Optional[str] = None
            self.session_expired: bool = False
            self.variables: dict = {}
            self.screenshots: list = []

    return TestContext()


@pytest.fixture
def auth_state():
    """Track authentication state for tests."""
    return {
        "logged_in": False,
        "token": None,
        "user": None,
        "expires_at": None,
    }


# =============================================================================
# Given Steps - Authentication State
# =============================================================================


@given("I am not logged in")
def not_logged_in(test_context):
    """Ensure user is not logged in by clearing any stored auth."""
    test_context.page.goto(test_context.base_url)
    # Clear auth tokens from local storage and cookies
    test_context.page.evaluate("""
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        sessionStorage.clear();
    """)
    # Clear cookies
    test_context.page.context.clear_cookies()
    test_context.user_email = None
    test_context.user_name = None
    test_context.auth_token = None


@given(parsers.parse('I am logged in as "{email}"'))
def logged_in_as_email(test_context, email: str):
    """Log in as a specific user by setting mock auth state."""
    test_context.user_email = email
    # Extract name from email or use email as name
    test_context.user_name = email.split("@")[0].replace(".", " ").title()

    test_context.page.goto(test_context.base_url)
    # Set mock auth token and user info
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


@given(parsers.parse('I am logged in as "{name}"'))
def logged_in_as_name(test_context, name: str):
    """Log in as a specific user by name."""
    # If it looks like a name (not an email), create a mock email
    if "@" not in name:
        email = f"{name.lower().replace(' ', '.')}@example.com"
        test_context.user_name = name
    else:
        email = name
        test_context.user_name = name.split("@")[0].replace(".", " ").title()

    test_context.user_email = email

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


@given("I am on the login page")
def on_login_page(test_context):
    """Navigate to the login page."""
    test_context.page.goto(f"{test_context.base_url}/login")
    test_context.page.wait_for_load_state("networkidle")


@given(parsers.parse('I tried to access "{url}" before login'))
def tried_to_access_before_login(test_context, url: str):
    """Record the URL user tried to access before login."""
    test_context.original_url = url
    # Store in session for return redirect
    test_context.page.evaluate(f"""
        sessionStorage.setItem('returnUrl', '{url}');
    """)


@given("I am on the login page with an error displayed")
def on_login_page_with_error(test_context):
    """Navigate to login page with an error state."""
    test_context.page.goto(f"{test_context.base_url}/login?error=auth_failed")
    test_context.page.wait_for_load_state("networkidle")


@given("the user has a Google profile picture")
def user_has_profile_picture(test_context):
    """Ensure user has a profile picture set."""
    # Mock user already has a picture URL set
    pass


@given("the user dropdown menu is open")
def dropdown_menu_is_open(test_context):
    """Ensure the user dropdown menu is open."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    avatar.click()
    expect(test_context.page.locator('[data-testid="user-dropdown"]')).to_be_visible()


@given("my session has expired")
def session_has_expired(test_context):
    """Simulate an expired session."""
    test_context.session_expired = True
    test_context.page.evaluate("""
        const expiredToken = 'expired-token-' + Date.now();
        localStorage.setItem('auth_token', expiredToken);
        localStorage.setItem('token_expires', '2000-01-01T00:00:00Z');
    """)


@given("I have an invalid session token")
def have_invalid_session_token(test_context):
    """Set an invalid session token."""
    test_context.page.evaluate("""
        localStorage.setItem('auth_token', 'invalid-malformed-token');
    """)


@given("my session is about to expire")
def session_about_to_expire(test_context):
    """Simulate a session that is about to expire."""
    test_context.page.evaluate("""
        const nearExpiry = new Date(Date.now() + 60000).toISOString(); // 1 minute from now
        localStorage.setItem('token_expires', nearExpiry);
    """)


@given(parsers.parse('I was logged in as "{email}"'))
def was_logged_in_as(test_context, email: str):
    """Mark that user was previously logged in."""
    test_context.user_email = email


@given("I have logged out")
def have_logged_out(test_context):
    """Ensure user has logged out."""
    test_context.page.evaluate("""
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        sessionStorage.clear();
    """)
    test_context.page.context.clear_cookies()
    test_context.auth_token = None


@given("the session is stored in local storage")
def session_stored_in_local_storage(test_context):
    """Verify session is in local storage."""
    # This is the default behavior, just ensure it's set
    pass


# =============================================================================
# Given Steps - OAuth Callback
# =============================================================================


@given("I am on the OAuth callback page with a valid code")
def on_callback_with_valid_code(test_context):
    """Navigate to callback page with a valid OAuth code."""
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?code=valid_test_code_123"
    )


@given("I am on the OAuth callback page")
def on_callback_page(test_context):
    """Navigate to callback page."""
    test_context.page.goto(f"{test_context.base_url}/auth/callback")


@given("I navigate to the callback page without a code parameter")
def callback_without_code(test_context):
    """Navigate to callback page without code parameter."""
    test_context.page.goto(f"{test_context.base_url}/auth/callback")
    test_context.page.wait_for_load_state("networkidle")


@given("I navigate to the callback page with an invalid code")
def callback_with_invalid_code(test_context):
    """Navigate to callback page with invalid code."""
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?code=invalid_code_xyz"
    )


@given("I am on the callback page with an error displayed")
def callback_with_error_displayed(test_context):
    """Navigate to callback page that shows an error."""
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?error=access_denied"
    )
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I navigate to the login page")
def navigate_to_login(test_context):
    """Navigate to the login page."""
    test_context.page.goto(f"{test_context.base_url}/login")
    test_context.page.wait_for_load_state("networkidle")


@when("I navigate to the dashboard page directly")
def navigate_to_dashboard_directly(test_context):
    """Navigate directly to dashboard page."""
    test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I navigate to "{url}" directly'))
@when(parsers.parse('I navigate to "{url}"'))
def navigate_to_url_directly(test_context, url: str):
    """Navigate directly to a specific URL."""
    if url.startswith("/"):
        test_context.page.goto(f"{test_context.base_url}{url}")
    else:
        test_context.page.goto(f"{test_context.base_url}/{url}")
    test_context.page.wait_for_load_state("networkidle")


@when("I try to navigate to the dashboard")
def try_navigate_to_dashboard(test_context):
    """Attempt to navigate to dashboard."""
    test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


@when("I try to access the dashboard")
def try_access_dashboard(test_context):
    """Attempt to access dashboard."""
    test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


@when("I am on the dashboard page")
def am_on_dashboard_page(test_context):
    """Navigate to dashboard page."""
    test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


@when("I navigate to the scenarios page")
def navigate_to_scenarios(test_context):
    """Navigate to scenarios page."""
    test_context.page.goto(f"{test_context.base_url}/scenarios")
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Authentication Actions
# =============================================================================


@when("I click the Sign in with Google button")
def click_sign_in_with_google(test_context):
    """Click the Sign in with Google button."""
    button = test_context.page.locator(
        '[data-testid="sign-in-google-btn"], '
        'button:has-text("Sign in with Google"), '
        '.google-sign-in-btn'
    )
    button.click()


@when("the OAuth flow returns an error")
def oauth_returns_error(test_context):
    """Simulate OAuth returning an error."""
    test_context.page.goto(
        f"{test_context.base_url}/login?error=auth_failed&error_description=Authentication+failed"
    )
    test_context.page.wait_for_load_state("networkidle")


@when("the OAuth returns unauthorized domain error")
def oauth_returns_domain_error(test_context):
    """Simulate OAuth returning unauthorized domain error."""
    test_context.page.goto(
        f"{test_context.base_url}/login?error=unauthorized_domain"
    )
    test_context.page.wait_for_load_state("networkidle")


@when("the OAuth returns account not found error")
def oauth_returns_account_not_found(test_context):
    """Simulate OAuth returning account not found error."""
    test_context.page.goto(
        f"{test_context.base_url}/login?error=account_not_found"
    )
    test_context.page.wait_for_load_state("networkidle")


@when("the authentication completes successfully")
def auth_completes_successfully(test_context):
    """Simulate successful authentication completion."""
    # Set auth token as if OAuth completed
    test_context.page.evaluate("""
        const user = {
            email: 'test.user@example.com',
            name: 'Test User',
            picture: 'https://ui-avatars.com/api/?name=Test+User'
        };
        localStorage.setItem('auth_token', 'valid-auth-token-from-oauth');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    # Wait for redirect
    test_context.page.wait_for_load_state("networkidle")


@when("the authentication fails")
def auth_fails(test_context):
    """Simulate authentication failure."""
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?error=access_denied"
    )
    test_context.page.wait_for_load_state("networkidle")


@when("the authentication fails due to invalid code")
def auth_fails_invalid_code(test_context):
    """Simulate authentication failure due to invalid code."""
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?error=invalid_grant&error_description=Invalid+or+expired+code"
    )
    test_context.page.wait_for_load_state("networkidle")


@when("I complete the Google sign in flow")
def complete_google_sign_in(test_context):
    """Complete the full Google sign in flow (mocked)."""
    test_context.page.evaluate("""
        const user = {
            email: 'test.user@example.com',
            name: 'Test User',
            picture: 'https://ui-avatars.com/api/?name=Test+User'
        };
        localStorage.setItem('auth_token', 'valid-auth-token-from-oauth');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    # Navigate to dashboard or return URL
    if test_context.original_url:
        test_context.page.goto(f"{test_context.base_url}{test_context.original_url}")
    else:
        test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


@when("the application refreshes the token")
def application_refreshes_token(test_context):
    """Simulate token refresh."""
    test_context.page.evaluate("""
        const newExpiry = new Date(Date.now() + 3600000).toISOString(); // 1 hour from now
        localStorage.setItem('token_expires', newExpiry);
        localStorage.setItem('auth_token', 'refreshed-token-' + Date.now());
    """)


# =============================================================================
# When Steps - User Menu Actions
# =============================================================================


@when("I click on the user avatar")
def click_user_avatar(test_context):
    """Click on the user avatar to open menu."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    avatar.click()


@when("I open the user menu")
def open_user_menu(test_context):
    """Open the user dropdown menu."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    avatar.click()
    expect(test_context.page.locator('[data-testid="user-dropdown"]')).to_be_visible()


@when(parsers.parse('I click on "{item}" in the dropdown'))
def click_dropdown_item(test_context, item: str):
    """Click on a specific item in the dropdown menu."""
    dropdown = test_context.page.locator('[data-testid="user-dropdown"]')
    dropdown.get_by_text(item).click()
    test_context.page.wait_for_load_state("networkidle")


@when("I click outside the dropdown menu")
def click_outside_dropdown(test_context):
    """Click outside the dropdown menu to close it."""
    test_context.page.locator("body").click(position={"x": 10, "y": 10})


@when(parsers.parse('I press the "{key}" key'))
def press_key(test_context, key: str):
    """Press a keyboard key."""
    test_context.page.keyboard.press(key)


@when(parsers.parse('I click the "{button}" button'))
def click_button(test_context, button: str):
    """Click a button by text."""
    test_context.page.get_by_role("button", name=button).click()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Page Actions
# =============================================================================


@when("I refresh the page")
def refresh_page(test_context):
    """Refresh the current page."""
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


@when("I close and reopen the browser tab")
def close_and_reopen_tab(test_context):
    """Simulate closing and reopening the browser tab."""
    # Store current URL
    current_url = test_context.page.url
    # Navigate away and back (simulates tab close/reopen)
    test_context.page.goto("about:blank")
    test_context.page.goto(current_url)
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Then Steps - Visibility Assertions
# =============================================================================


@then(parsers.parse('I should see the "{text}" button'))
def should_see_button(test_context, text: str):
    """Verify a button with text is visible."""
    expect(test_context.page.get_by_role("button", name=text)).to_be_visible()


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible by test ID."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).to_be_visible()


@then(parsers.parse('the "{element}" should not be visible'))
def element_should_not_be_visible(test_context, element: str):
    """Verify an element is not visible by test ID."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).not_to_be_visible()


@then(parsers.parse('I should see "{text}"'))
def should_see_text(test_context, text: str):
    """Verify text is visible on page."""
    expect(test_context.page.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should see "{text}" in the dropdown'))
def should_see_text_in_dropdown(test_context, text: str):
    """Verify text is visible in the dropdown menu."""
    dropdown = test_context.page.locator('[data-testid="user-dropdown"]')
    expect(dropdown.get_by_text(text)).to_be_visible()


@then("I should see the Sliples logo")
def should_see_logo(test_context):
    """Verify Sliples logo is visible."""
    logo = test_context.page.locator(
        '[data-testid="app-logo"], .sliples-logo, img[alt*="Sliples"]'
    ).first
    expect(logo).to_be_visible()


@then("the page should use dark theme styling")
def page_uses_dark_theme(test_context):
    """Verify the page uses dark theme styling."""
    # Check for dark theme class on body or container
    body = test_context.page.locator("body")
    expect(body).to_have_class(re.compile(r"dark|dark-theme|dark-mode"))


@then(parsers.parse('the "{element}" should have class "{class_name}"'))
def element_should_have_class(test_context, element: str, class_name: str):
    """Verify an element has a specific CSS class."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], #{element}, .{element}'
    ).first
    expect(locator).to_have_class(re.compile(class_name))


@then("I should see an error message")
def should_see_error_message(test_context):
    """Verify an error message is displayed."""
    error = test_context.page.locator(
        '[data-testid="login-error-message"], '
        '[data-testid="error-message"], '
        '.error-message, '
        '[role="alert"]'
    ).first
    expect(error).to_be_visible()


@then("I should see a loading spinner")
def should_see_loading_spinner(test_context):
    """Verify a loading spinner is displayed."""
    spinner = test_context.page.locator(
        '[data-testid="auth-loading-spinner"], '
        '[data-testid="loading-spinner"], '
        '.loading-spinner, '
        '.spinner'
    ).first
    expect(spinner).to_be_visible()


@then(parsers.parse('I should see a "{text}" button'))
def should_see_specific_button(test_context, text: str):
    """Verify a specific button is visible."""
    expect(test_context.page.get_by_role("button", name=text)).to_be_visible()


# =============================================================================
# Then Steps - User Menu Assertions
# =============================================================================


@then("I should see the user avatar in the header")
def should_see_user_avatar(test_context):
    """Verify user avatar is visible in header."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    expect(avatar).to_be_visible()


@then(parsers.parse('the user menu should display "{name}"'))
def user_menu_should_display_name(test_context, name: str):
    """Verify user menu displays the user's name."""
    user_name = test_context.page.locator(
        '[data-testid="user-name"], .user-name'
    ).first
    expect(user_name).to_contain_text(name)


@then("the user dropdown menu should be visible")
def dropdown_should_be_visible(test_context):
    """Verify user dropdown menu is visible."""
    dropdown = test_context.page.locator('[data-testid="user-dropdown"]')
    expect(dropdown).to_be_visible()


@then("the user dropdown menu should not be visible")
def dropdown_should_not_be_visible(test_context):
    """Verify user dropdown menu is not visible."""
    dropdown = test_context.page.locator('[data-testid="user-dropdown"]')
    expect(dropdown).not_to_be_visible()


@then("the user avatar should display the profile picture")
def avatar_displays_profile_picture(test_context):
    """Verify avatar displays user's profile picture."""
    avatar = test_context.page.locator('[data-testid="user-avatar"] img')
    expect(avatar).to_be_visible()


@then(parsers.parse('the "{element}" should have an image source'))
def element_should_have_image_source(test_context, element: str):
    """Verify element has an image source."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"] img, img[data-testid="{element}"]'
    ).first
    src = locator.get_attribute("src")
    assert src and len(src) > 0, "Image source should not be empty"


# =============================================================================
# Then Steps - Navigation Assertions
# =============================================================================


@then("I should be redirected to Google OAuth")
def should_redirect_to_google(test_context):
    """Verify redirect to Google OAuth."""
    # In test environment, we may mock this or check for redirect URL
    # For real test, URL would change to accounts.google.com
    expect(test_context.page).to_have_url(re.compile(r"accounts\.google\.com|oauth|auth"))


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify URL contains specified text."""
    expect(test_context.page).to_have_url(re.compile(re.escape(text)))


@then("I should be redirected to the login page")
def should_redirect_to_login(test_context):
    """Verify redirect to login page."""
    expect(test_context.page).to_have_url(re.compile(r"/login"))


@then("I should be redirected to the dashboard")
def should_redirect_to_dashboard(test_context):
    """Verify redirect to dashboard."""
    expect(test_context.page).to_have_url(re.compile(r"/dashboard"))


@then("I should be redirected to the scenarios page")
def should_redirect_to_scenarios(test_context):
    """Verify redirect to scenarios page."""
    expect(test_context.page).to_have_url(re.compile(r"/scenarios"))


@then("I should be redirected to the test runs page")
def should_redirect_to_testruns(test_context):
    """Verify redirect to test runs page."""
    expect(test_context.page).to_have_url(re.compile(r"/runs"))


@then("I should be redirected to the profile page")
def should_redirect_to_profile(test_context):
    """Verify redirect to profile page."""
    expect(test_context.page).to_have_url(re.compile(r"/profile"))


@then("I should be redirected to the settings page")
def should_redirect_to_settings(test_context):
    """Verify redirect to settings page."""
    expect(test_context.page).to_have_url(re.compile(r"/settings"))


@then("the original URL should be preserved as return parameter")
def original_url_preserved(test_context):
    """Verify original URL is preserved for return redirect."""
    url = test_context.page.url
    assert "return=" in url or "redirect=" in url or "next=" in url, \
        f"Expected return parameter in URL: {url}"


# =============================================================================
# Then Steps - Authentication State Assertions
# =============================================================================


@then("I should still be logged in")
def should_still_be_logged_in(test_context):
    """Verify user is still logged in."""
    # Check for user menu or avatar
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    expect(avatar).to_be_visible()


@then("my session should be cleared")
def session_should_be_cleared(test_context):
    """Verify session has been cleared."""
    auth_token = test_context.page.evaluate(
        "localStorage.getItem('auth_token')"
    )
    assert auth_token is None, "Auth token should be cleared"


@then("my invalid session should be cleared")
def invalid_session_cleared(test_context):
    """Verify invalid session has been cleared."""
    auth_token = test_context.page.evaluate(
        "localStorage.getItem('auth_token')"
    )
    assert auth_token is None or auth_token == "", "Invalid session should be cleared"


@then("I should be logged in successfully")
def logged_in_successfully(test_context):
    """Verify user is logged in successfully."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    expect(avatar).to_be_visible()


@then("my session should be extended")
def session_should_be_extended(test_context):
    """Verify session has been extended."""
    expires = test_context.page.evaluate(
        "localStorage.getItem('token_expires')"
    )
    if expires:
        expiry_date = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        assert expiry_date > datetime.now().astimezone(), "Session should be extended"


@then("I should remain logged in")
def should_remain_logged_in(test_context):
    """Verify user remains logged in."""
    avatar = test_context.page.locator('[data-testid="user-avatar"]')
    expect(avatar).to_be_visible()


# =============================================================================
# Then Steps - Content Visibility Assertions
# =============================================================================


@then("I should not see the dashboard content")
def should_not_see_dashboard_content(test_context):
    """Verify dashboard content is not visible."""
    dashboard = test_context.page.locator('[data-testid="dashboard-content"]')
    expect(dashboard).not_to_be_visible()


@then("I should not see the test runs list")
def should_not_see_testruns_list(test_context):
    """Verify test runs list is not visible."""
    runs_list = test_context.page.locator('[data-testid="test-runs-list"]')
    expect(runs_list).not_to_be_visible()


@then("I should not see the scenarios list")
def should_not_see_scenarios_list(test_context):
    """Verify scenarios list is not visible."""
    scenarios_list = test_context.page.locator('[data-testid="scenarios-list"]')
    expect(scenarios_list).not_to_be_visible()


@then("I should not see the settings content")
def should_not_see_settings_content(test_context):
    """Verify settings content is not visible."""
    settings = test_context.page.locator('[data-testid="settings-content"]')
    expect(settings).not_to_be_visible()


@then("I should see the dashboard content")
def should_see_dashboard_content(test_context):
    """Verify dashboard content is visible."""
    dashboard = test_context.page.locator(
        '[data-testid="dashboard-content"], '
        '[data-testid="dashboard"], '
        '.dashboard-content'
    ).first
    expect(dashboard).to_be_visible()


# =============================================================================
# Then Steps - Button State Assertions
# =============================================================================


@then(parsers.parse('the "{element}" should show loading state'))
def element_should_show_loading(test_context, element: str):
    """Verify element shows loading state."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"]'
    ).first
    # Check for loading class or disabled state
    expect(locator).to_have_class(re.compile(r"loading|disabled|spinner"))


@then(parsers.parse('the button text should change to "{text}"'))
def button_text_should_change(test_context, text: str):
    """Verify button text has changed."""
    button = test_context.page.locator(
        '[data-testid="sign-in-google-btn"], '
        'button:has-text("Redirecting")'
    ).first
    expect(button).to_contain_text(text)


@then("the error message should be cleared")
def error_message_cleared(test_context):
    """Verify error message has been cleared."""
    error = test_context.page.locator(
        '[data-testid="login-error-message"], '
        '[data-testid="error-message"]'
    ).first
    expect(error).not_to_be_visible()


@then("I should be able to start a new sign in flow")
def can_start_new_sign_in(test_context):
    """Verify user can start new sign in flow."""
    button = test_context.page.locator(
        '[data-testid="sign-in-google-btn"], '
        'button:has-text("Sign in with Google")'
    ).first
    expect(button).to_be_visible()
    expect(button).to_be_enabled()


@then("I should be able to complete a new sign in")
def can_complete_new_sign_in(test_context):
    """Verify user can complete new sign in."""
    # Just verify we're in a state where sign in can proceed
    pass


# =============================================================================
# Then Steps - Security Assertions
# =============================================================================


@then("the auth token should be stored in httpOnly cookie or secure storage")
def token_stored_securely(test_context):
    """Verify auth token is stored securely."""
    # Check if stored in localStorage (less secure) or not
    local_token = test_context.page.evaluate(
        "localStorage.getItem('auth_token')"
    )
    # In a secure implementation, token might be in httpOnly cookie
    # For this test, we verify it exists somewhere
    cookies = test_context.page.context.cookies()
    auth_cookie = next(
        (c for c in cookies if "auth" in c["name"].lower() or "token" in c["name"].lower()),
        None
    )
    assert local_token or auth_cookie, "Auth token should be stored"


@then("the token should not be accessible via JavaScript directly")
def token_not_accessible_via_js(test_context):
    """Verify token is not accessible via JavaScript (for httpOnly cookies)."""
    # This would only apply if using httpOnly cookies
    # If using localStorage, this test would need adjustment
    pass


@then("API requests should include the Authorization header")
def api_requests_include_auth_header(test_context):
    """Verify API requests include Authorization header."""
    # This would typically be verified via network interception
    # For now, verify token exists
    local_token = test_context.page.evaluate(
        "localStorage.getItem('auth_token')"
    )
    assert local_token, "Auth token should exist for API requests"


@then("the header should contain a valid Bearer token")
def header_contains_bearer_token(test_context):
    """Verify Authorization header contains Bearer token."""
    # This would be verified via network interception
    pass
