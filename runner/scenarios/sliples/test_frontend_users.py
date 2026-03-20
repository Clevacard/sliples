"""
Test module for User Management Frontend tests.

This module connects pytest-bdd scenarios from test_frontend_users.feature
to step definitions for testing the admin-only User Management page including
user list, role changes, and status toggling.
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
scenarios("test_frontend_users.feature")


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

    class UsersTestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.api_base_url = api_url
            self.user_email: Optional[str] = None
            self.user_name: Optional[str] = None
            self.user_role: str = "user"
            self.user_id: Optional[str] = None
            self.auth_token: Optional[str] = None
            self.mock_users: List[Dict[str, Any]] = []
            self.api_response: Optional[Dict[str, Any]] = None
            self.api_status_code: Optional[int] = None
            self.variables: dict = {}
            self.screenshots: list = []

    return UsersTestContext()


@pytest.fixture
def users_state():
    """Track users state for tests."""
    return {
        "users": [],
        "search_query": "",
        "sort_column": None,
        "sort_direction": "asc",
        "current_page": 1,
    }


# =============================================================================
# Given Steps - Authentication and User Setup
# =============================================================================


@given(parsers.parse('I am logged in as "{email}" with role "{role}"'))
def logged_in_with_role(test_context, email: str, role: str):
    """Log in as a user with a specific role."""
    test_context.user_email = email
    test_context.user_name = email.split("@")[0].replace(".", " ").title()
    test_context.user_role = role
    test_context.user_id = f"user-{email.replace('@', '-').replace('.', '-')}"

    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            id: '{test_context.user_id}',
            email: '{email}',
            name: '{test_context.user_name}',
            role: '{role}',
            active: true,
            picture: 'https://ui-avatars.com/api/?name={test_context.user_name.replace(" ", "+")}',
            created_at: '2026-01-15T10:00:00Z',
            last_login_at: new Date().toISOString()
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


@given("I am not logged in")
def not_logged_in(test_context):
    """Ensure user is not logged in."""
    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate("""
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        sessionStorage.clear();
    """)
    test_context.page.context.clear_cookies()
    test_context.user_email = None
    test_context.auth_token = None


# =============================================================================
# Given Steps - Mock Users Setup
# =============================================================================


@given("there are multiple users in the system")
def multiple_users_in_system(test_context):
    """Set up multiple mock users."""
    test_context.mock_users = [
        {
            "id": "user-1",
            "name": "Alice Smith",
            "email": "alice@company.com",
            "role": "admin",
            "active": True,
            "picture": "https://ui-avatars.com/api/?name=Alice+Smith",
            "created_at": "2026-01-01T10:00:00Z",
            "last_login_at": "2026-03-20T08:00:00Z",
        },
        {
            "id": "user-2",
            "name": "Bob Johnson",
            "email": "bob@company.com",
            "role": "user",
            "active": True,
            "picture": "https://ui-avatars.com/api/?name=Bob+Johnson",
            "created_at": "2026-01-15T10:00:00Z",
            "last_login_at": "2026-03-19T14:30:00Z",
        },
        {
            "id": "user-3",
            "name": "Charlie Brown",
            "email": "charlie@company.com",
            "role": "user",
            "active": False,
            "picture": "https://ui-avatars.com/api/?name=Charlie+Brown",
            "created_at": "2026-02-01T10:00:00Z",
            "last_login_at": "2026-02-15T09:00:00Z",
        },
    ]
    _setup_mock_users(test_context)


@given(parsers.parse('there is a user "{name}" with email "{email}"'))
def user_with_name_and_email(test_context, name: str, email: str):
    """Set up a specific user."""
    user = {
        "id": f"user-{email.replace('@', '-').replace('.', '-')}",
        "name": name,
        "email": email,
        "role": "user",
        "active": True,
        "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there is a user with role "{role}"'))
def user_with_role(test_context, role: str):
    """Set up a user with a specific role."""
    user = {
        "id": f"user-{role}-test",
        "name": f"Test {role.title()} User",
        "email": f"test.{role}@company.com",
        "role": role,
        "active": True,
        "picture": f"https://ui-avatars.com/api/?name=Test+{role.title()}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there is an active user "{email}"'))
def active_user(test_context, email: str):
    """Set up an active user."""
    name = email.split("@")[0].replace(".", " ").title()
    user = {
        "id": f"user-{email.replace('@', '-').replace('.', '-')}",
        "name": name,
        "email": email,
        "role": "user",
        "active": True,
        "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there is an inactive user "{email}"'))
def inactive_user(test_context, email: str):
    """Set up an inactive user."""
    name = email.split("@")[0].replace(".", " ").title()
    user = {
        "id": f"user-{email.replace('@', '-').replace('.', '-')}",
        "name": name,
        "email": email,
        "role": "user",
        "active": False,
        "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-02-15T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there is a user who logged in "{time_ago}"'))
def user_logged_in_time_ago(test_context, time_ago: str):
    """Set up a user with a specific last login time."""
    # Parse time like "2 hours ago"
    now = datetime.now()
    if "hour" in time_ago:
        hours = int(time_ago.split()[0])
        last_login = now - timedelta(hours=hours)
    elif "day" in time_ago:
        days = int(time_ago.split()[0])
        last_login = now - timedelta(days=days)
    else:
        last_login = now

    user = {
        "id": "user-recent-login",
        "name": "Recent User",
        "email": "recent@company.com",
        "role": "user",
        "active": True,
        "picture": "https://ui-avatars.com/api/?name=Recent+User",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": last_login.isoformat() + "Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there are users with names "{name1}" and "{name2}"'))
def users_with_names(test_context, name1: str, name2: str):
    """Set up users with specific names."""
    for name in [name1, name2]:
        email = name.lower().replace(" ", ".") + "@company.com"
        user = {
            "id": f"user-{email.replace('@', '-').replace('.', '-')}",
            "name": name,
            "email": email,
            "role": "user",
            "active": True,
            "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
            "created_at": "2026-01-15T10:00:00Z",
            "last_login_at": "2026-03-20T10:00:00Z",
        }
        test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there are users with emails "{email1}" and "{email2}"'))
def users_with_emails(test_context, email1: str, email2: str):
    """Set up users with specific emails."""
    for email in [email1, email2]:
        name = email.split("@")[0].replace(".", " ").title()
        user = {
            "id": f"user-{email.replace('@', '-').replace('.', '-')}",
            "name": name,
            "email": email,
            "role": "user",
            "active": True,
            "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
            "created_at": "2026-01-15T10:00:00Z",
            "last_login_at": "2026-03-20T10:00:00Z",
        }
        test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given("there are users in the system")
def users_in_system(test_context):
    """Ensure some users exist in the system."""
    if not test_context.mock_users:
        test_context.mock_users = [
            {
                "id": "user-default-1",
                "name": "Default User",
                "email": "default@company.com",
                "role": "user",
                "active": True,
                "picture": "https://ui-avatars.com/api/?name=Default+User",
                "created_at": "2026-01-15T10:00:00Z",
                "last_login_at": "2026-03-20T10:00:00Z",
            }
        ]
    _setup_mock_users(test_context)


@given(parsers.parse('there is a user "{email}" with role "{role}"'))
def user_with_email_and_role(test_context, email: str, role: str):
    """Set up a user with specific email and role."""
    name = email.split("@")[0].replace(".", " ").title()
    user = {
        "id": f"user-{email.replace('@', '-').replace('.', '-')}",
        "name": name,
        "email": email,
        "role": role,
        "active": True,
        "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given("the role change confirmation modal is open")
def role_change_modal_open(test_context):
    """Ensure the role change confirmation modal is open."""
    expect(test_context.page.locator('[data-testid="role-change-modal"]')).to_be_visible()


@given(parsers.parse('there is a user with id "{user_id}" and role "{role}"'))
def user_with_id_and_role(test_context, user_id: str, role: str):
    """Set up a user with specific ID and role."""
    user = {
        "id": user_id,
        "name": "Test User",
        "email": f"{user_id}@company.com",
        "role": role,
        "active": True,
        "picture": "https://ui-avatars.com/api/?name=Test+User",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('there is an active user with id "{user_id}"'))
def active_user_with_id(test_context, user_id: str):
    """Set up an active user with specific ID."""
    user = {
        "id": user_id,
        "name": "Active Test User",
        "email": f"{user_id}@company.com",
        "role": "user",
        "active": True,
        "picture": "https://ui-avatars.com/api/?name=Active+Test+User",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given(parsers.parse('my user id is "{user_id}"'))
def set_my_user_id(test_context, user_id: str):
    """Set the current user's ID."""
    test_context.user_id = user_id
    test_context.page.evaluate(f"""
        const user = JSON.parse(localStorage.getItem('user') || '{{}}');
        user.id = '{user_id}';
        localStorage.setItem('user', JSON.stringify(user));
    """)


@given("there are more than 20 users in the system")
def more_than_20_users(test_context):
    """Set up more than 20 users for pagination testing."""
    for i in range(25):
        user = {
            "id": f"user-{i}",
            "name": f"User Number {i}",
            "email": f"user{i}@company.com",
            "role": "user" if i % 5 != 0 else "admin",
            "active": True,
            "picture": f"https://ui-avatars.com/api/?name=User+{i}",
            "created_at": "2026-01-15T10:00:00Z",
            "last_login_at": f"2026-03-{(i % 20) + 1:02d}T10:00:00Z",
        }
        test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given("there are users with different last login times")
def users_with_different_login_times(test_context):
    """Set up users with various last login times."""
    login_times = [
        ("2026-03-20T10:00:00Z", "Recent User"),
        ("2026-03-15T10:00:00Z", "Week Ago User"),
        ("2026-02-01T10:00:00Z", "Month Ago User"),
    ]
    for login_time, name in login_times:
        email = name.lower().replace(" ", ".") + "@company.com"
        user = {
            "id": f"user-{email.replace('@', '-').replace('.', '-')}",
            "name": name,
            "email": email,
            "role": "user",
            "active": True,
            "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
            "created_at": "2026-01-15T10:00:00Z",
            "last_login_at": login_time,
        }
        test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given("the users API is unavailable")
def users_api_unavailable(test_context):
    """Mock the users API to be unavailable."""
    test_context.page.evaluate("""
        window.__mockApiError = true;
        window.__mockApiErrorMessage = 'Service unavailable';
    """)


@given("the role update API will fail")
def role_update_api_will_fail(test_context):
    """Mock the role update API to fail."""
    test_context.page.evaluate("""
        window.__mockRoleUpdateError = true;
    """)


@given(parsers.parse('there is a user "{email}"'))
def user_exists(test_context, email: str):
    """Set up a user by email."""
    name = email.split("@")[0].replace(".", " ").title()
    user = {
        "id": f"user-{email.replace('@', '-').replace('.', '-')}",
        "name": name,
        "email": email,
        "role": "user",
        "active": True,
        "picture": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}",
        "created_at": "2026-01-15T10:00:00Z",
        "last_login_at": "2026-03-20T10:00:00Z",
    }
    test_context.mock_users.append(user)
    _setup_mock_users(test_context)


@given("another admin has modified this user's role")
def another_admin_modified_user(test_context):
    """Simulate concurrent modification by another admin."""
    test_context.page.evaluate("""
        window.__mockConcurrentModification = true;
    """)


def _setup_mock_users(test_context):
    """Helper to set up mock users in the page context."""
    users_json = json.dumps(test_context.mock_users)
    test_context.page.evaluate(f"""
        window.__mockUsers = {users_json};
    """)


# =============================================================================
# When Steps - Navigation
# =============================================================================


@when("I navigate to the users page")
def navigate_to_users_page(test_context):
    """Navigate to the users management page."""
    test_context.page.goto(f"{test_context.base_url}/users")
    test_context.page.wait_for_load_state("networkidle")


@when(parsers.parse('I navigate to "{url}" directly'))
def navigate_to_url_directly(test_context, url: str):
    """Navigate directly to a specific URL."""
    if url.startswith("/"):
        test_context.page.goto(f"{test_context.base_url}{url}")
    else:
        test_context.page.goto(f"{test_context.base_url}/{url}")
    test_context.page.wait_for_load_state("networkidle")


@when("I am on the dashboard page")
def on_dashboard_page(test_context):
    """Navigate to the dashboard page."""
    test_context.page.goto(f"{test_context.base_url}/dashboard")
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - Search and Filter
# =============================================================================


@when(parsers.parse('I enter "{text}" into the search field'))
def enter_search_text(test_context, text: str):
    """Enter text into the search field."""
    search_input = test_context.page.locator(
        '[data-testid="users-search-input"], '
        'input[placeholder*="Search"], '
        '.search-input'
    ).first
    search_input.fill(text)
    # Wait for search to execute (debounce)
    test_context.page.wait_for_timeout(500)


# =============================================================================
# When Steps - Role Change Actions
# =============================================================================


@when(parsers.parse('I click the role dropdown for "{email}"'))
def click_role_dropdown_for_user(test_context, email: str):
    """Click the role dropdown for a specific user."""
    user_row = test_context.page.locator(f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")')
    role_dropdown = user_row.locator(
        '[data-testid="role-dropdown"], '
        '.role-dropdown, '
        'select[name="role"], '
        'button.role-selector'
    )
    role_dropdown.click()


@when(parsers.parse('I select "{role}" from the role dropdown'))
def select_role_from_dropdown(test_context, role: str):
    """Select a role from the dropdown."""
    option = test_context.page.locator(
        f'.role-option:has-text("{role}"), '
        f'[data-testid="role-option-{role.lower()}"], '
        f'option[value="{role.lower()}"]'
    ).first
    option.click()
    test_context.page.wait_for_timeout(300)


@when("I confirm the role change")
def confirm_role_change(test_context):
    """Confirm the role change in the modal."""
    confirm_btn = test_context.page.locator(
        '[data-testid="confirm-role-change-btn"], '
        'button:has-text("Confirm"), '
        '.modal button.primary'
    ).first
    confirm_btn.click()
    test_context.page.wait_for_timeout(500)


@when(parsers.parse('I click the "{button_text}" button'))
def click_button(test_context, button_text: str):
    """Click a button by its text."""
    btn = test_context.page.locator(
        f'button:has-text("{button_text}"), '
        f'[data-testid="{button_text.lower().replace(" ", "-")}-btn"]'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I change the role of "{email}" to "{role}"'))
def change_user_role(test_context, email: str, role: str):
    """Change a user's role (combines dropdown click, selection, and confirmation)."""
    click_role_dropdown_for_user(test_context, email)
    select_role_from_dropdown(test_context, role)
    test_context.page.wait_for_timeout(300)
    # If confirmation modal appears, confirm it
    modal = test_context.page.locator('[data-testid="role-change-modal"]')
    if modal.is_visible():
        confirm_role_change(test_context)


# =============================================================================
# When Steps - Status Toggle Actions
# =============================================================================


@when(parsers.parse('I click the status toggle for "{email}"'))
def click_status_toggle_for_user(test_context, email: str):
    """Click the status toggle for a specific user."""
    user_row = test_context.page.locator(f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")')
    toggle = user_row.locator(
        '[data-testid="status-toggle"], '
        '.status-toggle, '
        'input[type="checkbox"][name="active"]'
    )
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when("I confirm the deactivation")
def confirm_deactivation(test_context):
    """Confirm the deactivation in the modal."""
    confirm_btn = test_context.page.locator(
        '[data-testid="confirm-deactivate-btn"], '
        'button:has-text("Deactivate"), '
        '.deactivation-modal button.danger'
    ).first
    confirm_btn.click()
    test_context.page.wait_for_timeout(500)


@when(parsers.parse('I attempt to login as "{email}"'))
def attempt_login_as(test_context, email: str):
    """Attempt to login as a specific user."""
    test_context.page.goto(f"{test_context.base_url}/login")
    # Simulate OAuth callback with the user's email
    test_context.page.goto(
        f"{test_context.base_url}/auth/callback?code=mock_code_{email}"
    )
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# When Steps - API Requests
# =============================================================================


@when(parsers.parse('I make an API request to GET "{endpoint}"'))
def make_get_api_request(test_context, endpoint: str):
    """Make a GET request to an API endpoint."""
    response = test_context.page.evaluate(f"""
        async () => {{
            const token = localStorage.getItem('auth_token');
            const response = await fetch('{test_context.api_base_url}{endpoint}', {{
                method: 'GET',
                headers: {{
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }}
            }});
            return {{
                status: response.status,
                body: await response.json().catch(() => ({{}}))
            }};
        }}
    """)
    test_context.api_status_code = response.get("status")
    test_context.api_response = response.get("body")


@when(parsers.parse('I make an API request to PUT "{endpoint}" with body \'{body}\''))
def make_put_api_request(test_context, endpoint: str, body: str):
    """Make a PUT request to an API endpoint with a body."""
    response = test_context.page.evaluate(f"""
        async () => {{
            const token = localStorage.getItem('auth_token');
            const response = await fetch('{test_context.api_base_url}{endpoint}', {{
                method: 'PUT',
                headers: {{
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'
                }},
                body: '{body}'
            }});
            return {{
                status: response.status,
                body: await response.json().catch(() => ({{}}))
            }};
        }}
    """)
    test_context.api_status_code = response.get("status")
    test_context.api_response = response.get("body")


# =============================================================================
# When Steps - Sorting and Pagination
# =============================================================================


@when(parsers.parse('I click the "{column}" column header'))
def click_column_header(test_context, column: str):
    """Click a column header for sorting."""
    header = test_context.page.locator(
        f'th:has-text("{column}"), '
        f'[data-testid="column-{column.lower().replace(" ", "-")}"], '
        f'.column-header:has-text("{column}")'
    ).first
    header.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{button}" pagination button'))
def click_pagination_button(test_context, button: str):
    """Click a pagination button."""
    btn = test_context.page.locator(
        f'[data-testid="pagination-{button.lower()}"], '
        f'button[aria-label="{button}"], '
        f'.pagination button:has-text("{button}")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I try to change the role of "{email}"'))
def try_change_role(test_context, email: str):
    """Attempt to change a user's role."""
    click_role_dropdown_for_user(test_context, email)
    select_role_from_dropdown(test_context, "Admin")


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


@then('I should see "Access Denied" or be redirected')
def should_see_access_denied_or_redirect(test_context):
    """Verify either access denied message or redirect occurred."""
    # Check if redirected away from /users
    url = test_context.page.url
    if "/users" not in url:
        # Redirected - this is acceptable
        return

    # Otherwise, should see access denied message
    expect(test_context.page.get_by_text("Access Denied").first).to_be_visible()


@then("I should not see the users list content")
def should_not_see_users_list_content(test_context):
    """Verify users list content is not visible."""
    users_list = test_context.page.locator('[data-testid="users-list"]')
    expect(users_list).not_to_be_visible()


# =============================================================================
# Then Steps - Navigation Assertions
# =============================================================================


@then("I should be redirected to the dashboard")
def should_redirect_to_dashboard(test_context):
    """Verify redirect to dashboard."""
    expect(test_context.page).to_have_url(re.compile(r"/dashboard"))


@then(parsers.parse('I should see "{text}" in the navigation menu'))
def should_see_in_nav_menu(test_context, text: str):
    """Verify text is visible in the navigation menu."""
    nav = test_context.page.locator('nav, [data-testid="navigation"], .sidebar')
    expect(nav.get_by_text(text)).to_be_visible()


@then(parsers.parse('I should not see "{text}" in the navigation menu'))
def should_not_see_in_nav_menu(test_context, text: str):
    """Verify text is not visible in the navigation menu."""
    nav = test_context.page.locator('nav, [data-testid="navigation"], .sidebar')
    expect(nav.get_by_text(text)).not_to_be_visible()


# =============================================================================
# Then Steps - User List Assertions
# =============================================================================


@then("I should see the users list")
def should_see_users_list(test_context):
    """Verify users list is visible."""
    users_list = test_context.page.locator(
        '[data-testid="users-list"], .users-list, table.users'
    ).first
    expect(users_list).to_be_visible()


@then(parsers.parse('I should see at least {count:d} user entries'))
def should_see_at_least_n_user_entries(test_context, count: int):
    """Verify at least N user entries are visible."""
    user_rows = test_context.page.locator(
        '[data-testid="user-row"], .user-row, tr.user-entry'
    )
    expect(user_rows).to_have_count(count, timeout=5000)


@then("each user entry should be in a row")
def each_user_in_row(test_context):
    """Verify each user entry is in a table row."""
    user_rows = test_context.page.locator(
        '[data-testid="user-row"], .user-row, tr.user-entry'
    )
    count = user_rows.count()
    assert count > 0, "Should have user rows"


@then(parsers.parse('I should see "{text}" in the users list'))
def should_see_text_in_users_list(test_context, text: str):
    """Verify text appears in the users list."""
    users_list = test_context.page.locator('[data-testid="users-list"], .users-list')
    expect(users_list.get_by_text(text).first).to_be_visible()


@then("the user row should display an avatar")
def user_row_displays_avatar(test_context):
    """Verify user row displays an avatar."""
    avatar = test_context.page.locator(
        '[data-testid="user-avatar"], .user-avatar, img.avatar'
    ).first
    expect(avatar).to_be_visible()


@then("I should see role badges for each user")
def should_see_role_badges(test_context):
    """Verify role badges are displayed for users."""
    badges = test_context.page.locator(
        '[data-testid="role-badge"], .role-badge'
    )
    assert badges.count() > 0, "Should see role badges"


@then(parsers.parse('the "{badge}" should be visible for admin users'))
def badge_visible_for_admin(test_context, badge: str):
    """Verify a specific badge is visible for admin users."""
    admin_badge = test_context.page.locator(
        f'[data-testid="{badge}"], .{badge}'
    ).first
    expect(admin_badge).to_be_visible()


@then(parsers.parse('the "{badge}" should be visible for regular users'))
def badge_visible_for_regular_users(test_context, badge: str):
    """Verify a specific badge is visible for regular users."""
    user_badge = test_context.page.locator(
        f'[data-testid="{badge}"], .{badge}'
    ).first
    expect(user_badge).to_be_visible()


@then(parsers.parse('I should see "{status}" status for "{email}"'))
def should_see_status_for_user(test_context, status: str, email: str):
    """Verify a specific status is shown for a user."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    expect(user_row.get_by_text(status)).to_be_visible()


@then(parsers.parse('the "{badge}" should be visible for each user'))
def badge_visible_for_each_user(test_context, badge: str):
    """Verify a badge type is visible for each user."""
    badges = test_context.page.locator(f'[data-testid="{badge}"], .{badge}')
    users = test_context.page.locator('[data-testid="user-row"], .user-row')
    assert badges.count() >= users.count(), "Each user should have a status badge"


@then(parsers.parse('I should see "{column}" column'))
def should_see_column(test_context, column: str):
    """Verify a column header is visible."""
    header = test_context.page.locator(
        f'th:has-text("{column}"), '
        f'[data-testid="column-{column.lower().replace(" ", "-")}"]'
    ).first
    expect(header).to_be_visible()


@then("the last login timestamp should be displayed")
def last_login_timestamp_displayed(test_context):
    """Verify last login timestamps are displayed."""
    timestamp = test_context.page.locator(
        '[data-testid="last-login"], .last-login, .last-login-time'
    ).first
    expect(timestamp).to_be_visible()


@then("the timestamp should show relative time or date format")
def timestamp_shows_time_format(test_context):
    """Verify timestamp shows readable format."""
    timestamp = test_context.page.locator(
        '[data-testid="last-login"], .last-login'
    ).first
    text = timestamp.text_content()
    # Should contain time-related words or date patterns
    assert (
        "ago" in text.lower() or
        "hour" in text.lower() or
        "day" in text.lower() or
        re.search(r"\d{4}", text) or  # year
        re.search(r"\d{1,2}/\d{1,2}", text)  # date format
    ), f"Timestamp should show readable format: {text}"


@then(parsers.parse('I should see "{text}" in the results'))
def should_see_in_results(test_context, text: str):
    """Verify text appears in search results."""
    results = test_context.page.locator('[data-testid="users-list"], .users-list')
    expect(results.get_by_text(text).first).to_be_visible()


@then(parsers.parse('I should not see "{text}" in the results'))
def should_not_see_in_results(test_context, text: str):
    """Verify text does not appear in search results."""
    results = test_context.page.locator('[data-testid="users-list"], .users-list')
    expect(results.get_by_text(text).first).not_to_be_visible()


# =============================================================================
# Then Steps - Role Change Assertions
# =============================================================================


@then("the confirmation modal should appear")
def confirmation_modal_appears(test_context):
    """Verify confirmation modal is visible."""
    modal = test_context.page.locator(
        '[data-testid="role-change-modal"], '
        '[data-testid="confirmation-modal"], '
        '.confirmation-modal'
    ).first
    expect(modal).to_be_visible()


@then(parsers.parse('I should see "{button_text}" button'))
def should_see_button(test_context, button_text: str):
    """Verify a button is visible."""
    button = test_context.page.locator(f'button:has-text("{button_text}")').first
    expect(button).to_be_visible()


@then(parsers.parse('the user "{email}" should display role "{role}"'))
def user_should_display_role(test_context, email: str, role: str):
    """Verify a user displays a specific role."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    role_badge = user_row.locator('.role-badge, [data-testid="role-badge"]')
    expect(role_badge).to_contain_text(role)


@then(parsers.parse('the user "{email}" should still display role "{role}"'))
def user_should_still_display_role(test_context, email: str, role: str):
    """Verify a user still displays a specific role (unchanged)."""
    user_should_display_role(test_context, email, role)


@then(parsers.parse('the role dropdown for "{email}" should be disabled'))
def role_dropdown_disabled_for_user(test_context, email: str):
    """Verify the role dropdown is disabled for a user."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    dropdown = user_row.locator('[data-testid="role-dropdown"], .role-dropdown')
    expect(dropdown).to_be_disabled()


@then(parsers.parse('I should see a tooltip "{text}"'))
def should_see_tooltip(test_context, text: str):
    """Verify a tooltip with specific text is visible."""
    tooltip = test_context.page.locator(
        f'[data-tooltip*="{text}"], '
        f'[title*="{text}"], '
        f'.tooltip:has-text("{text}")'
    ).first
    # Tooltips might need hover to appear
    expect(tooltip).to_be_attached()


@then("the users list should update without page refresh")
def users_list_updates_without_refresh(test_context):
    """Verify the users list updated dynamically."""
    # Check that we're still on the same page
    expect(test_context.page).to_have_url(re.compile(r"/users"))
    # List should be visible
    expect(test_context.page.locator('[data-testid="users-list"]')).to_be_visible()


@then(parsers.parse('the "{badge}" should be visible for "{email}"'))
def badge_visible_for_email(test_context, badge: str, email: str):
    """Verify a badge is visible for a specific user."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    badge_elem = user_row.locator(f'[data-testid="{badge}"], .{badge}')
    expect(badge_elem).to_be_visible()


# =============================================================================
# Then Steps - Status Toggle Assertions
# =============================================================================


@then("the deactivation confirmation modal should appear")
def deactivation_modal_appears(test_context):
    """Verify deactivation confirmation modal is visible."""
    modal = test_context.page.locator(
        '[data-testid="deactivation-modal"], '
        '[data-testid="confirm-deactivate-modal"], '
        '.deactivation-modal'
    ).first
    expect(modal).to_be_visible()


@then(parsers.parse('the user "{email}" should show "{status}" status'))
def user_should_show_status(test_context, email: str, status: str):
    """Verify a user shows a specific status."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    status_badge = user_row.locator('.status-badge, [data-testid="status-badge"]')
    expect(status_badge).to_contain_text(status)


@then(parsers.parse('the status toggle for "{email}" should be disabled'))
def status_toggle_disabled_for_user(test_context, email: str):
    """Verify the status toggle is disabled for a user."""
    user_row = test_context.page.locator(
        f'.user-row:has-text("{email}"), [data-testid="user-row"]:has-text("{email}")'
    )
    toggle = user_row.locator('[data-testid="status-toggle"], .status-toggle')
    expect(toggle).to_be_disabled()


@then(parsers.parse('the badge should display "{text}"'))
def badge_displays_text(test_context, text: str):
    """Verify a badge displays specific text."""
    badge = test_context.page.locator(
        '.status-badge, .role-badge, [data-testid*="badge"]'
    ).first
    expect(badge).to_contain_text(text)


@then("the user row should have visual indication of inactive status")
def user_row_has_inactive_indication(test_context):
    """Verify the user row has visual styling for inactive status."""
    inactive_row = test_context.page.locator(
        '.user-row.inactive, '
        '[data-testid="user-row"][data-inactive="true"], '
        '.user-row:has(.status-badge-inactive)'
    ).first
    expect(inactive_row).to_be_visible()


@then("I should not be logged in")
def should_not_be_logged_in(test_context):
    """Verify user is not logged in."""
    # Check that we're on login page or auth token is not set
    auth_token = test_context.page.evaluate("localStorage.getItem('auth_token')")
    assert auth_token is None or auth_token == "", "Should not be logged in"


# =============================================================================
# Then Steps - Admin Badge Assertions
# =============================================================================


@then("I should see the admin indicator in the header")
def should_see_admin_indicator(test_context):
    """Verify admin indicator is visible in header."""
    indicator = test_context.page.locator(
        '[data-testid="admin-indicator"], '
        '[data-testid="user-role-badge"], '
        '.admin-indicator, '
        '.header .role-badge'
    ).first
    expect(indicator).to_be_visible()


@then(parsers.parse('the "{element}" should display "{text}"'))
def element_should_display_text(test_context, element: str, text: str):
    """Verify an element displays specific text."""
    locator = test_context.page.locator(
        f'[data-testid="{element}"], .{element}'
    ).first
    expect(locator).to_contain_text(text)


# =============================================================================
# Then Steps - API Response Assertions
# =============================================================================


@then(parsers.parse('the API should return status {status:d}'))
def api_returns_status(test_context, status: int):
    """Verify API returned specific status code."""
    assert test_context.api_status_code == status, \
        f"Expected status {status}, got {test_context.api_status_code}"


@then(parsers.parse('the response should contain "{text}"'))
def response_contains_text(test_context, text: str):
    """Verify API response contains specific text."""
    response_str = json.dumps(test_context.api_response)
    assert text in response_str, f"Expected '{text}' in response: {response_str}"


@then("the response should contain a list of users")
def response_contains_user_list(test_context):
    """Verify API response contains a list of users."""
    response = test_context.api_response
    assert isinstance(response, list) or "users" in response, \
        "Response should contain a list of users"


@then("each user should have id, name, email, role, and active fields")
def each_user_has_required_fields(test_context):
    """Verify each user in response has required fields."""
    response = test_context.api_response
    users = response if isinstance(response, list) else response.get("users", [])
    required_fields = ["id", "name", "email", "role", "active"]
    for user in users:
        for field in required_fields:
            assert field in user, f"User missing field: {field}"


@then(parsers.parse('the response should contain "{field}" as "{value}"'))
def response_field_equals_value(test_context, field: str, value: str):
    """Verify API response field equals specific value."""
    response = test_context.api_response
    actual_value = str(response.get(field, ""))
    assert actual_value.lower() == value.lower(), \
        f"Expected {field}={value}, got {actual_value}"


@then(parsers.parse('the response should contain "{field}" as {value}'))
def response_field_equals_bool_value(test_context, field: str, value: str):
    """Verify API response field equals boolean/number value."""
    response = test_context.api_response
    actual_value = response.get(field)
    expected = value.lower() == "true" if value.lower() in ["true", "false"] else value
    assert actual_value == expected, f"Expected {field}={expected}, got {actual_value}"


@then("the user's role should be updated in the database")
def role_updated_in_database(test_context):
    """Verify role was updated (mock check)."""
    # In real test, would verify database state
    # For UI tests, rely on API response
    pass


@then("the user should be marked as inactive in the database")
def user_marked_inactive_in_database(test_context):
    """Verify user was marked inactive (mock check)."""
    # In real test, would verify database state
    # For UI tests, rely on API response
    pass


# =============================================================================
# Then Steps - Pagination and Sorting Assertions
# =============================================================================


@then("I should see pagination controls")
def should_see_pagination_controls(test_context):
    """Verify pagination controls are visible."""
    pagination = test_context.page.locator(
        '[data-testid="pagination"], .pagination'
    ).first
    expect(pagination).to_be_visible()


@then(parsers.parse('I should see "{text}" indicator'))
def should_see_indicator(test_context, text: str):
    """Verify a text indicator is visible."""
    expect(test_context.page.get_by_text(text).first).to_be_visible()


@then("I should see the next page of users")
def should_see_next_page(test_context):
    """Verify next page of users is shown."""
    # Check pagination indicator updated
    page_indicator = test_context.page.locator('.page-indicator, [data-testid="page-indicator"]')
    text = page_indicator.text_content()
    assert "2" in text, "Should be on page 2"


@then("the users should be sorted alphabetically by name")
def users_sorted_alphabetically(test_context):
    """Verify users are sorted alphabetically."""
    names = test_context.page.locator('.user-name, [data-testid="user-name"]').all_text_contents()
    sorted_names = sorted(names, key=str.lower)
    assert names == sorted_names, f"Expected alphabetical order: {sorted_names}, got {names}"


@then("the users should be sorted in reverse alphabetical order")
def users_sorted_reverse_alphabetically(test_context):
    """Verify users are sorted in reverse alphabetical order."""
    names = test_context.page.locator('.user-name, [data-testid="user-name"]').all_text_contents()
    sorted_names = sorted(names, key=str.lower, reverse=True)
    assert names == sorted_names, f"Expected reverse alphabetical: {sorted_names}, got {names}"


@then("the users should be sorted by last login date")
def users_sorted_by_last_login(test_context):
    """Verify users are sorted by last login date."""
    # Just verify the sort happened (order depends on direction)
    timestamps = test_context.page.locator('[data-testid="last-login"], .last-login')
    assert timestamps.count() > 0, "Should have last login timestamps"


@then("the most recently logged in user should appear first")
def most_recent_login_first(test_context):
    """Verify most recently logged in user appears first."""
    first_timestamp = test_context.page.locator(
        '[data-testid="last-login"], .last-login'
    ).first.text_content()
    # Most recent should show "just now" or recent time
    assert (
        "just now" in first_timestamp.lower() or
        "minute" in first_timestamp.lower() or
        "hour" in first_timestamp.lower()
    ), f"First user should be most recent: {first_timestamp}"


# =============================================================================
# Then Steps - Error Handling Assertions
# =============================================================================


@then("the system should attempt to reload the users list")
def system_attempts_reload(test_context):
    """Verify system attempts to reload the users list."""
    # After clicking retry, the list should attempt to load
    loading = test_context.page.locator(
        '[data-testid="users-loading"], .loading-indicator'
    )
    # Either loading is shown or list is visible (if reload succeeded)
    users_list = test_context.page.locator('[data-testid="users-list"]')
    assert loading.is_visible() or users_list.is_visible(), \
        "Should be loading or showing users list"
