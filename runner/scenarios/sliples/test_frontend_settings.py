"""
Test module for Settings Page UI tests.

This module connects pytest-bdd scenarios from test_frontend_settings.feature
to step definitions for testing the Settings page including Profile, API Keys,
and Preferences tabs.
"""

import os
import re
import json
from datetime import datetime
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_frontend_settings.feature")


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

    class SettingsTestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.user_email: Optional[str] = None
            self.user_name: Optional[str] = None
            self.user_role: str = "user"
            self.auth_token: Optional[str] = None
            self.created_api_keys: list = []
            self.new_api_key_value: Optional[str] = None
            self.current_theme: str = "dark"
            self.variables: dict = {}
            self.screenshots: list = []

    return SettingsTestContext()


@pytest.fixture
def settings_state():
    """Track settings state for tests."""
    return {
        "active_tab": "profile",
        "api_keys": [],
        "preferences": {
            "theme": "dark",
            "email_notifications": True,
            "browser_notifications": False,
        },
    }


# =============================================================================
# Given Steps - Authentication and User Setup
# =============================================================================


@given(parsers.parse('I am logged in as "{email}"'))
def logged_in_as_email(test_context, email: str):
    """Log in as a specific user by setting mock auth state."""
    test_context.user_email = email
    test_context.user_name = email.split("@")[0].replace(".", " ").title()
    test_context.user_role = "user"

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


@given(parsers.parse('I am logged in as "{name}" with email "{email}"'))
def logged_in_as_name_with_email(test_context, name: str, email: str):
    """Log in as a user with specific name and email."""
    test_context.user_email = email
    test_context.user_name = name
    test_context.user_role = "user"

    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            email: '{email}',
            name: '{name}',
            role: 'user',
            picture: 'https://ui-avatars.com/api/?name={name.replace(" ", "+")}',
            created_at: '2026-01-15T10:00:00Z'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


@given(parsers.parse('I am logged in as "{email}" with role "{role}"'))
def logged_in_with_role(test_context, email: str, role: str):
    """Log in as a user with a specific role."""
    test_context.user_email = email
    test_context.user_name = email.split("@")[0].replace(".", " ").title()
    test_context.user_role = role

    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            email: '{email}',
            name: '{test_context.user_name}',
            role: '{role}',
            picture: 'https://ui-avatars.com/api/?name={test_context.user_name.replace(" ", "+")}',
            created_at: '2026-01-15T10:00:00Z'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


@given("the user has a Google profile picture")
def user_has_profile_picture(test_context):
    """Ensure user has a profile picture set (already set in login steps)."""
    pass


@given(parsers.parse('the user account was created on "{date}"'))
def user_created_on_date(test_context, date: str):
    """Set the user account creation date."""
    test_context.page.evaluate(f"""
        const user = JSON.parse(localStorage.getItem('user') || '{{}}');
        user.created_at = '{date}T10:00:00Z';
        localStorage.setItem('user', JSON.stringify(user));
    """)


# =============================================================================
# Given Steps - Page Navigation State
# =============================================================================


@given("I am on the settings page")
def on_settings_page(test_context):
    """Navigate to the settings page."""
    test_context.page.goto(f"{test_context.base_url}/settings")
    test_context.page.wait_for_load_state("networkidle")


@given("I am on the Profile tab")
def on_profile_tab(test_context):
    """Ensure we're on the Profile tab."""
    tab = test_context.page.locator('[data-testid="profile-tab"]')
    if not tab.get_attribute("aria-selected") == "true":
        tab.click()
        test_context.page.wait_for_load_state("networkidle")


@given("I am on the API Keys tab")
def on_api_keys_tab(test_context):
    """Ensure we're on the API Keys tab."""
    tab = test_context.page.locator(
        '[data-testid="api-keys-tab"], '
        'button:has-text("API Keys"), '
        '[role="tab"]:has-text("API Keys")'
    ).first
    tab.click()
    test_context.page.wait_for_timeout(300)


@given("I am on the Preferences tab")
def on_preferences_tab(test_context):
    """Ensure we're on the Preferences tab."""
    tab = test_context.page.locator(
        '[data-testid="preferences-tab"], '
        'button:has-text("Preferences"), '
        '[role="tab"]:has-text("Preferences")'
    ).first
    tab.click()
    test_context.page.wait_for_timeout(300)


@given("the Profile tab is focused")
def profile_tab_focused(test_context):
    """Focus the Profile tab for keyboard navigation."""
    tab = test_context.page.locator('[data-testid="profile-tab"]').first
    tab.focus()


# =============================================================================
# Given Steps - API Keys State
# =============================================================================


@given(parsers.parse('the user has an API key named "{name}"'))
def user_has_api_key(test_context, name: str):
    """Set up an API key for the user."""
    test_context.created_api_keys.append({
        "id": f"key-{len(test_context.created_api_keys) + 1}",
        "name": name,
        "key_prefix": "slp_abc12345",
        "created_at": "2026-03-01T10:00:00Z",
        "last_used_at": None,
        "active": True,
    })
    # Mock the API response
    test_context.page.evaluate(f"""
        window.__mockApiKeys = window.__mockApiKeys || [];
        window.__mockApiKeys.push({{
            id: 'key-{len(test_context.created_api_keys)}',
            name: '{name}',
            key_prefix: 'slp_abc12345',
            created_at: '2026-03-01T10:00:00Z',
            last_used_at: null,
            active: true
        }});
    """)


@given("the user has no API keys")
def user_has_no_api_keys(test_context):
    """Ensure user has no API keys."""
    test_context.created_api_keys = []
    test_context.page.evaluate("""
        window.__mockApiKeys = [];
    """)


@given("the create API key modal is open")
def create_api_key_modal_open(test_context):
    """Open the create API key modal."""
    btn = test_context.page.locator(
        '[data-testid="create-api-key-btn"], '
        'button:has-text("Create API Key")'
    ).first
    btn.click()
    test_context.page.wait_for_selector('[data-testid="create-api-key-modal"]')


@given(parsers.parse('I have just created an API key named "{name}"'))
def just_created_api_key(test_context, name: str):
    """Simulate having just created an API key."""
    test_context.new_api_key_value = f"slp_newkey123456789abcdef{name.replace(' ', '')}"
    test_context.page.evaluate(f"""
        window.__newApiKey = {{
            id: 'new-key-1',
            name: '{name}',
            key: 'slp_newkey123456789abcdef{name.replace(' ', '')}',
            key_prefix: 'slp_newkey12',
            created_at: new Date().toISOString(),
            last_used_at: null,
            active: true
        }};
    """)


@given("the full key is displayed")
def full_key_displayed(test_context):
    """Ensure the full API key is currently displayed."""
    expect(test_context.page.locator('[data-testid="new-api-key-display"]')).to_be_visible()


@given(parsers.parse('I have created an API key named "{name}"'))
def have_created_api_key(test_context, name: str):
    """Mark that we've created an API key."""
    test_context.created_api_keys.append({
        "id": f"created-key-{len(test_context.created_api_keys) + 1}",
        "name": name,
        "key_prefix": "slp_created1",
        "created_at": datetime.now().isoformat(),
        "last_used_at": None,
        "active": True,
    })


@given(parsers.parse('the revoke confirmation modal is open for "{name}"'))
def revoke_modal_open_for_key(test_context, name: str):
    """Open the revoke confirmation modal for a specific key."""
    # Click the revoke button for the key
    key_row = test_context.page.locator(f'.api-key-item:has-text("{name}")')
    revoke_btn = key_row.locator('[data-testid="revoke-key-btn"], .revoke-btn')
    revoke_btn.click()
    test_context.page.wait_for_selector('[data-testid="revoke-confirmation-modal"]')


@given(parsers.parse('the API key "{name}" was used just now'))
def api_key_used_just_now(test_context, name: str):
    """Mark that an API key was used recently."""
    test_context.page.evaluate(f"""
        const keys = window.__mockApiKeys || [];
        const key = keys.find(k => k.name === '{name}');
        if (key) {{
            key.last_used_at = new Date().toISOString();
        }}
    """)


# =============================================================================
# Given Steps - Preferences State
# =============================================================================


@given(parsers.parse('the current theme is "{theme}"'))
def current_theme_is(test_context, theme: str):
    """Set the current theme."""
    test_context.current_theme = theme
    test_context.page.evaluate(f"""
        localStorage.setItem('theme', '{theme}');
        document.documentElement.setAttribute('data-theme', '{theme}');
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add('{theme}-theme');
    """)


@given("email notifications are currently off")
def email_notifications_off(test_context):
    """Set email notifications to off."""
    test_context.page.evaluate("""
        const prefs = JSON.parse(localStorage.getItem('preferences') || '{}');
        prefs.email_notifications = false;
        localStorage.setItem('preferences', JSON.stringify(prefs));
    """)


@given("email notifications are currently on")
def email_notifications_on(test_context):
    """Set email notifications to on."""
    test_context.page.evaluate("""
        const prefs = JSON.parse(localStorage.getItem('preferences') || '{}');
        prefs.email_notifications = true;
        localStorage.setItem('preferences', JSON.stringify(prefs));
    """)


@given("browser notifications are currently off")
def browser_notifications_off(test_context):
    """Set browser notifications to off."""
    test_context.page.evaluate("""
        const prefs = JSON.parse(localStorage.getItem('preferences') || '{}');
        prefs.browser_notifications = false;
        localStorage.setItem('preferences', JSON.stringify(prefs));
    """)


@given("browser notifications are currently on")
def browser_notifications_on(test_context):
    """Set browser notifications to on."""
    test_context.page.evaluate("""
        const prefs = JSON.parse(localStorage.getItem('preferences') || '{}');
        prefs.browser_notifications = true;
        localStorage.setItem('preferences', JSON.stringify(prefs));
    """)


@given("I have customized preferences")
def have_customized_preferences(test_context):
    """Set custom preferences that differ from defaults."""
    test_context.page.evaluate("""
        const prefs = {
            theme: 'light',
            email_notifications: false,
            browser_notifications: true
        };
        localStorage.setItem('preferences', JSON.stringify(prefs));
        localStorage.setItem('theme', 'light');
    """)


@given(parsers.parse('I set the theme to "{theme}"'))
def set_theme_to(test_context, theme: str):
    """Set the theme preference."""
    test_context.current_theme = theme
    # Click the appropriate theme option
    if theme == "light":
        test_context.page.locator('[data-testid="theme-light-option"], .theme-option-light').click()
    else:
        test_context.page.locator('[data-testid="theme-dark-option"], .theme-option-dark').click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I navigate to the settings page")
def navigate_to_settings(test_context):
    """Navigate to the settings page."""
    test_context.page.goto(f"{test_context.base_url}/settings")
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I click on the "{tab_name}" tab'))
def click_tab(test_context, tab_name: str):
    """Click on a specific tab."""
    tab = test_context.page.locator(
        f'[data-testid="{tab_name.lower().replace(" ", "-")}-tab"], '
        f'button:has-text("{tab_name}"), '
        f'[role="tab"]:has-text("{tab_name}")'
    ).first
    tab.click()
    test_context.page.wait_for_timeout(300)


@when("I refresh the page")
def refresh_page(test_context):
    """Refresh the current page."""
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - API Key Actions
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
    """Leave a field empty (clear it)."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], '
        f'input[name="{field}"], '
        f'#{field}'
    ).first
    locator.fill("")


@when(parsers.parse('I click the revoke button for API key "{name}"'))
def click_revoke_for_key(test_context, name: str):
    """Click the revoke button for a specific API key."""
    key_row = test_context.page.locator(f'.api-key-item:has-text("{name}")')
    revoke_btn = key_row.locator('[data-testid="revoke-key-btn"], .revoke-btn, button:has-text("Revoke")')
    revoke_btn.click()


@when(parsers.parse('I click the "{button_text}" button in the confirmation modal'))
def click_confirmation_button(test_context, button_text: str):
    """Click a button in the confirmation modal."""
    modal = test_context.page.locator('[data-testid="revoke-confirmation-modal"], .confirmation-modal')
    btn = modal.locator(f'button:has-text("{button_text}")')
    btn.click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Preferences Actions
# =============================================================================


@when("I click the theme toggle")
def click_theme_toggle(test_context):
    """Click the theme toggle switch."""
    toggle = test_context.page.locator(
        '[data-testid="theme-toggle"], '
        '.theme-toggle, '
        'button[aria-label*="theme" i]'
    ).first
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when("I click the email notifications toggle")
def click_email_notifications_toggle(test_context):
    """Click the email notifications toggle."""
    toggle = test_context.page.locator(
        '[data-testid="email-notifications-toggle"], '
        '.email-notifications-toggle'
    ).first
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when("I click the browser notifications toggle")
def click_browser_notifications_toggle(test_context):
    """Click the browser notifications toggle."""
    toggle = test_context.page.locator(
        '[data-testid="browser-notifications-toggle"], '
        '.browser-notifications-toggle'
    ).first
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I change the theme to "{theme}"'))
def change_theme_to(test_context, theme: str):
    """Change the theme setting."""
    if theme == "light":
        test_context.page.locator('[data-testid="theme-light-option"], .theme-option-light').click()
    else:
        test_context.page.locator('[data-testid="theme-dark-option"], .theme-option-dark').click()
    test_context.current_theme = theme


@when("I enable email notifications")
def enable_email_notifications(test_context):
    """Enable email notifications if not already enabled."""
    toggle = test_context.page.locator('[data-testid="email-notifications-toggle"]')
    if toggle.get_attribute("aria-checked") != "true":
        toggle.click()
        test_context.page.wait_for_timeout(300)


@when(parsers.parse('I press the "{key}" key'))
def press_key(test_context, key: str):
    """Press a keyboard key."""
    test_context.page.keyboard.press(key)


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


@then(parsers.parse('the "{element}" should be active'))
def element_should_be_active(test_context, element: str):
    """Verify an element has active state."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"]'
    ).first
    expect(locator).to_have_attribute("aria-selected", "true")


@then(parsers.parse('the "{element}" should still be visible'))
def element_should_still_be_visible(test_context, element: str):
    """Verify an element is still visible (alias for should be visible)."""
    element_should_be_visible(test_context, element)


# =============================================================================
# Then Steps - Profile Assertions
# =============================================================================


@then("the profile avatar should display the user's Google picture")
def profile_avatar_displays_google_picture(test_context):
    """Verify the profile avatar shows the user's Google picture."""
    avatar = test_context.page.locator('[data-testid="profile-avatar"] img')
    expect(avatar).to_be_visible()
    src = avatar.get_attribute("src")
    assert src and len(src) > 0, "Avatar should have an image source"


@then(parsers.parse('the "{element}" should have an image source'))
def element_has_image_source(test_context, element: str):
    """Verify an element has an image source attribute."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"] img, img[data-testid="{element}"]'
    ).first
    src = locator.get_attribute("src")
    assert src and len(src) > 0, "Element should have an image source"


@then("I should see the user role displayed")
def should_see_user_role(test_context):
    """Verify the user role is displayed."""
    role_element = test_context.page.locator('[data-testid="profile-role"]')
    expect(role_element).to_be_visible()


@then(parsers.parse('I should see "{date}" or similar date format'))
def should_see_date_format(test_context, date: str):
    """Verify a date is displayed in some readable format."""
    # Look for any reasonable date display
    page_content = test_context.page.content()
    # Check for various date formats
    assert (
        date in page_content or
        "January" in page_content or
        "2026" in page_content
    ), f"Expected to see date {date} or similar format"


@then("I should see the admin badge")
def should_see_admin_badge(test_context):
    """Verify the admin badge is visible."""
    badge = test_context.page.locator(
        '[data-testid="admin-badge"], .admin-badge, .role-badge.admin'
    ).first
    expect(badge).to_be_visible()


@then("I should see the user badge")
def should_see_user_badge(test_context):
    """Verify the user badge is visible."""
    badge = test_context.page.locator(
        '[data-testid="user-badge"], .user-badge, .role-badge.user'
    ).first
    expect(badge).to_be_visible()


@then(parsers.parse('the badge should display "{text}"'))
def badge_should_display(test_context, text: str):
    """Verify a badge displays specific text."""
    badge = test_context.page.locator(
        '[data-testid="admin-badge"], [data-testid="user-badge"], .role-badge'
    ).first
    expect(badge).to_contain_text(text)


# =============================================================================
# Then Steps - API Keys Assertions
# =============================================================================


@then(parsers.parse('I should see "{name}" in the API keys list'))
def should_see_key_in_list(test_context, name: str):
    """Verify an API key name appears in the list."""
    key_list = test_context.page.locator('[data-testid="api-keys-list"]')
    expect(key_list.get_by_text(name)).to_be_visible()


@then(parsers.parse('I should not see "{name}" in the API keys list'))
def should_not_see_key_in_list(test_context, name: str):
    """Verify an API key name does not appear in the list."""
    key_list = test_context.page.locator('[data-testid="api-keys-list"]')
    expect(key_list.get_by_text(name)).not_to_be_visible()


@then('I should see the key prefix starting with "slp_"')
def should_see_key_prefix(test_context):
    """Verify API key prefix is visible."""
    prefix = test_context.page.locator('.key-prefix, [data-testid="key-prefix"]').first
    expect(prefix).to_contain_text("slp_")


@then("I should see the key creation date")
def should_see_creation_date(test_context):
    """Verify key creation date is visible."""
    date = test_context.page.locator('.key-created-at, [data-testid="key-created-at"]').first
    expect(date).to_be_visible()


@then('I should see the "last used" information')
def should_see_last_used(test_context):
    """Verify last used information is visible."""
    last_used = test_context.page.locator('.key-last-used, [data-testid="key-last-used"]').first
    expect(last_used).to_be_visible()


@then("the API key should display as masked")
def key_should_be_masked(test_context):
    """Verify API key is displayed in masked format."""
    key_display = test_context.page.locator('.key-prefix, [data-testid="key-prefix"]').first
    text = key_display.text_content()
    assert "****" in text or text.count("*") >= 4, "Key should be masked with asterisks"


@then('I should see "slp_****" pattern')
def should_see_masked_pattern(test_context):
    """Verify the masked key pattern is shown."""
    key_display = test_context.page.locator('.key-prefix, [data-testid="key-prefix"]').first
    text = key_display.text_content()
    assert text.startswith("slp_") and "*" in text, "Key should show slp_**** pattern"


@then("the full key should NOT be visible")
def full_key_not_visible(test_context):
    """Verify the full API key is not visible."""
    # Full key would be much longer than the prefix
    key_displays = test_context.page.locator('.key-prefix, [data-testid="key-prefix"]').all()
    for display in key_displays:
        text = display.text_content() or ""
        # Full key would be > 32 chars, prefix is ~12
        assert len(text.replace("*", "")) < 20, "Full key should not be visible"


@then("I should see the full API key displayed")
def should_see_full_key(test_context):
    """Verify the full API key is displayed after creation."""
    key_display = test_context.page.locator('[data-testid="new-api-key-display"], .new-key-value')
    expect(key_display).to_be_visible()
    text = key_display.text_content()
    assert text and text.startswith("slp_") and len(text) >= 32, "Should see full API key"


@then('the key should start with "slp_"')
def key_starts_with_prefix(test_context):
    """Verify the API key starts with the correct prefix."""
    key_display = test_context.page.locator(
        '[data-testid="new-api-key-display"], .new-key-value, .key-prefix'
    ).first
    text = key_display.text_content()
    assert text and text.startswith("slp_"), "Key should start with slp_"


@then(parsers.parse('I should see "{message}"'))
def should_see_message(test_context, message: str):
    """Verify a message is displayed."""
    expect(test_context.page.get_by_text(message).first).to_be_visible()


@then("the clipboard should contain the API key")
def clipboard_contains_key(test_context):
    """Verify the clipboard contains the API key (best-effort check)."""
    # Note: Direct clipboard access is restricted in browsers
    # We verify the copy success notification instead
    success = test_context.page.locator(
        '.notification.success, [data-testid="copy-success"], :text("copied")'
    ).first
    expect(success).to_be_visible()


@then(parsers.parse('the API key "{name}" should display as masked'))
def specific_key_should_be_masked(test_context, name: str):
    """Verify a specific API key is displayed as masked."""
    key_row = test_context.page.locator(f'.api-key-item:has-text("{name}")')
    key_prefix = key_row.locator('.key-prefix, [data-testid="key-prefix"]')
    text = key_prefix.text_content()
    assert "*" in text, f"Key {name} should be masked"


@then(parsers.parse('the "{name}" should show "Last used: just now" or similar'))
def key_shows_recent_use(test_context, name: str):
    """Verify a key shows recent usage time."""
    key_row = test_context.page.locator(f'.api-key-item:has-text("{name}")')
    last_used = key_row.locator('.key-last-used, [data-testid="key-last-used"]')
    text = last_used.text_content()
    assert (
        "just now" in text.lower() or
        "seconds ago" in text.lower() or
        "minute" in text.lower()
    ), "Should show recent usage"


@then('the "last-used" timestamp should be recent')
def last_used_is_recent(test_context):
    """Verify the last used timestamp is recent."""
    last_used = test_context.page.locator(
        '.key-last-used, [data-testid="key-last-used"]'
    ).first
    expect(last_used).to_be_visible()


# =============================================================================
# Then Steps - Preferences Assertions
# =============================================================================


@then(parsers.parse('the theme should change to "{theme}"'))
def theme_should_change_to(test_context, theme: str):
    """Verify the theme has changed."""
    test_context.current_theme = theme
    # Check body class or data attribute
    body = test_context.page.locator("body")
    expect(body).to_have_class(re.compile(f"{theme}"))


@then(parsers.parse('the theme should be "{theme}"'))
def theme_should_be(test_context, theme: str):
    """Verify the current theme."""
    body = test_context.page.locator("body")
    expect(body).to_have_class(re.compile(f"{theme}"))


@then(parsers.parse('the theme should still be "{theme}"'))
def theme_should_still_be(test_context, theme: str):
    """Verify the theme persists."""
    theme_should_be(test_context, theme)


@then("the page should use light theme styling")
def page_uses_light_theme(test_context):
    """Verify the page uses light theme styling."""
    body = test_context.page.locator("body, html")
    # Check for light theme indicators
    has_light_class = test_context.page.evaluate("""
        document.body.classList.contains('light-theme') ||
        document.body.classList.contains('light') ||
        document.documentElement.getAttribute('data-theme') === 'light'
    """)
    assert has_light_class, "Page should use light theme styling"


@then("the page should use dark theme styling")
def page_uses_dark_theme(test_context):
    """Verify the page uses dark theme styling."""
    has_dark_class = test_context.page.evaluate("""
        document.body.classList.contains('dark-theme') ||
        document.body.classList.contains('dark') ||
        document.documentElement.getAttribute('data-theme') === 'dark'
    """)
    assert has_dark_class, "Page should use dark theme styling"


@then(parsers.parse('the "{element}" should show "{text}" as active'))
def element_shows_text_as_active(test_context, element: str, text: str):
    """Verify an element shows specific text as active."""
    locator = test_context.page.locator(f'[data-testid="{element}"]')
    active_option = locator.locator(f'.active:has-text("{text}"), [aria-selected="true"]:has-text("{text}")')
    expect(active_option.first).to_be_visible()


@then("email notifications should be enabled")
def email_notifications_enabled(test_context):
    """Verify email notifications are enabled."""
    toggle = test_context.page.locator('[data-testid="email-notifications-toggle"]')
    expect(toggle).to_have_attribute("aria-checked", "true")


@then("email notifications should be disabled")
def email_notifications_disabled(test_context):
    """Verify email notifications are disabled."""
    toggle = test_context.page.locator('[data-testid="email-notifications-toggle"]')
    expect(toggle).to_have_attribute("aria-checked", "false")


@then("browser notifications should be enabled")
def browser_notifications_enabled(test_context):
    """Verify browser notifications are enabled."""
    toggle = test_context.page.locator('[data-testid="browser-notifications-toggle"]')
    expect(toggle).to_have_attribute("aria-checked", "true")


@then("browser notifications should be disabled")
def browser_notifications_disabled(test_context):
    """Verify browser notifications are disabled."""
    toggle = test_context.page.locator('[data-testid="browser-notifications-toggle"]')
    expect(toggle).to_have_attribute("aria-checked", "false")


@then(parsers.parse('the "{element}" should be in the "{state}" position'))
def toggle_should_be_in_state(test_context, element: str, state: str):
    """Verify a toggle is in a specific position."""
    toggle = test_context.page.locator(f'[data-testid="{element}"]')
    expected_checked = "true" if state == "on" else "false"
    expect(toggle).to_have_attribute("aria-checked", expected_checked)


@then("the preferences should be saved to localStorage")
def preferences_saved_to_localstorage(test_context):
    """Verify preferences are saved to localStorage."""
    prefs = test_context.page.evaluate("localStorage.getItem('preferences')")
    assert prefs is not None, "Preferences should be saved to localStorage"


@then("localStorage should contain the theme preference")
def localstorage_contains_theme(test_context):
    """Verify localStorage contains theme preference."""
    theme = test_context.page.evaluate("localStorage.getItem('theme')")
    assert theme is not None, "Theme should be in localStorage"


@then("localStorage should contain the notification preferences")
def localstorage_contains_notification_prefs(test_context):
    """Verify localStorage contains notification preferences."""
    prefs = test_context.page.evaluate("localStorage.getItem('preferences')")
    assert prefs is not None, "Preferences should be in localStorage"
    prefs_obj = json.loads(prefs)
    assert "email_notifications" in prefs_obj or "browser_notifications" in prefs_obj, \
        "Notification preferences should be saved"


# =============================================================================
# Then Steps - URL and Navigation Assertions
# =============================================================================


@then(parsers.parse('the URL should contain "{text}"'))
def url_should_contain(test_context, text: str):
    """Verify the URL contains specific text."""
    expect(test_context.page).to_have_url(re.compile(re.escape(text)))


@then(parsers.parse('the "{tab_name}" tab should be focused'))
def tab_should_be_focused(test_context, tab_name: str):
    """Verify a specific tab is focused."""
    tab = test_context.page.locator(
        f'[data-testid="{tab_name.lower().replace(" ", "-")}-tab"], '
        f'[role="tab"]:has-text("{tab_name}")'
    ).first
    expect(tab).to_be_focused()
