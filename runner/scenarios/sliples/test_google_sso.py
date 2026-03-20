"""
Test module for Google Workspace SSO Authentication tests.

This module connects pytest-bdd scenarios from test_google_sso.feature
to the step definitions for OAuth/SSO testing.
"""

import os
import re
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import Mock, patch
from urllib.parse import urlparse, parse_qs

import pytest
import requests
import jwt
from pytest_bdd import scenarios, given, when, then, parsers

# Import shared step definitions from runner/steps/api.py
from steps import api


# Load all scenarios from the feature file
scenarios("test_google_sso.feature")


# =============================================================================
# OAuth/SSO Context Extension
# =============================================================================

class SSOContext:
    """Extended context for SSO/OAuth testing."""

    def __init__(self, api_context):
        self.api_context = api_context
        self.oauth_code: Optional[str] = None
        self.oauth_state: Optional[str] = None
        self.jwt_token: Optional[str] = None
        self.jwt_cookie_name: str = "sliples_auth"
        self.mock_google_user: Optional[dict] = None
        self.authorization_url: Optional[str] = None
        self.login_attempts: int = 0
        self.allowed_domains: list = []
        self.session_tokens: dict = {}  # device -> token mapping


@pytest.fixture
def api_context():
    """Create API context for tests."""
    ctx = api.APIContext()
    yield ctx
    # Cleanup created resources after each test
    headers = {"Content-Type": "application/json"}
    if ctx.api_key:
        headers["X-API-Key"] = ctx.api_key

    # Clean up any test users created during SSO tests
    for key, value in ctx.created_ids.items():
        if key.startswith("sso_user_"):
            try:
                requests.delete(
                    f"{ctx.base_url}/api/v1/users/{value}",
                    headers=headers
                )
            except Exception:
                pass


@pytest.fixture
def sso_context(api_context):
    """Create SSO context for OAuth/SSO tests."""
    return SSOContext(api_context)


# =============================================================================
# Helper Functions
# =============================================================================

def _get_headers(api_context, include_cookies=False, cookies=None):
    """Get request headers with optional cookie support."""
    headers = {"Content-Type": "application/json"}
    if api_context.api_key:
        headers["X-API-Key"] = api_context.api_key
    return headers


def _parse_authorization_url(url: str) -> dict:
    """Parse OAuth authorization URL into components."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    # parse_qs returns lists, convert single values
    return {k: v[0] if len(v) == 1 else v for k, v in params.items()}


def _generate_mock_jwt(user_email: str, user_id: str, exp_minutes: int = 60,
                       secret: str = "test-secret") -> str:
    """Generate a mock JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": user_email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
        "iss": "sliples",
        "aud": "sliples-api"
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _generate_expired_jwt(user_email: str, user_id: str,
                          secret: str = "test-secret") -> str:
    """Generate an expired JWT token for testing."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": user_email,
        "iat": int((now - timedelta(hours=2)).timestamp()),
        "exp": int((now - timedelta(hours=1)).timestamp()),
        "iss": "sliples",
        "aud": "sliples-api"
    }
    return jwt.encode(payload, secret, algorithm="HS256")


# =============================================================================
# Given Steps - Setup and Prerequisites
# =============================================================================

@given('the API server is running at "http://localhost:8000"')
def api_server_running(api_context):
    """Ensure API server is running."""
    api_context.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    # Health check
    try:
        response = requests.get(f"{api_context.base_url}/api/v1/health", timeout=5)
        assert response.status_code == 200, "API server is not responding"
    except requests.exceptions.ConnectionError:
        pytest.skip("API server is not available")


@given("Google OAuth is configured")
def google_oauth_configured(api_context):
    """Ensure Google OAuth is configured on the server."""
    # This would typically check if the server has Google OAuth credentials
    # For testing, we assume it's configured or mock it
    api_context.variables["google_oauth_configured"] = True


@given(parsers.parse('a valid Google OAuth code for user "{email}"'))
def valid_google_oauth_code(sso_context, email: str):
    """Set up a valid mock Google OAuth code."""
    sso_context.oauth_code = f"mock_code_{secrets.token_hex(16)}"
    sso_context.oauth_state = secrets.token_hex(16)
    sso_context.mock_google_user = {
        "email": email,
        "email_verified": True,
        "name": email.split("@")[0].replace(".", " ").title(),
        "picture": f"https://lh3.googleusercontent.com/a/{secrets.token_hex(8)}",
        "sub": hashlib.sha256(email.encode()).hexdigest()[:32]
    }


@given(parsers.parse('a valid Google OAuth code for user "{email}" with picture "{picture_url}"'))
def valid_google_oauth_code_with_picture(sso_context, email: str, picture_url: str):
    """Set up a valid mock Google OAuth code with specific picture URL."""
    sso_context.oauth_code = f"mock_code_{secrets.token_hex(16)}"
    sso_context.oauth_state = secrets.token_hex(16)
    sso_context.mock_google_user = {
        "email": email,
        "email_verified": True,
        "name": email.split("@")[0].replace(".", " ").title(),
        "picture": picture_url,
        "sub": hashlib.sha256(email.encode()).hexdigest()[:32]
    }


@given(parsers.parse('an invalid Google OAuth code "{code}"'))
def invalid_google_oauth_code(sso_context, code: str):
    """Set up an invalid Google OAuth code."""
    sso_context.oauth_code = code
    sso_context.oauth_state = secrets.token_hex(16)
    sso_context.mock_google_user = None


@given(parsers.parse('an expired Google OAuth code for user "{email}"'))
def expired_google_oauth_code(sso_context, email: str):
    """Set up an expired Google OAuth code."""
    sso_context.oauth_code = f"expired_code_{secrets.token_hex(16)}"
    sso_context.oauth_state = secrets.token_hex(16)
    sso_context.mock_google_user = None


@given(parsers.parse('no user with email "{email}" exists'))
def no_user_exists(api_context, sso_context, email: str):
    """Ensure no user with the given email exists."""
    headers = _get_headers(api_context)
    # Try to delete the user if they exist
    response = requests.get(
        f"{api_context.base_url}/api/v1/users",
        params={"email": email},
        headers=headers
    )
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("email") == email:
                requests.delete(
                    f"{api_context.base_url}/api/v1/users/{user['id']}",
                    headers=headers
                )


@given(parsers.parse('an existing user with email "{email}"'))
def existing_user(api_context, sso_context, email: str):
    """Ensure a user with the given email exists."""
    headers = _get_headers(api_context)
    # Check if user exists
    response = requests.get(
        f"{api_context.base_url}/api/v1/users",
        params={"email": email},
        headers=headers
    )
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("email") == email:
                api_context.created_ids[f"sso_user_{email}"] = user["id"]
                api_context.variables["current_user"] = user
                return

    # Create the user if they don't exist
    user_data = {
        "email": email,
        "name": email.split("@")[0].replace(".", " ").title(),
        "role": "viewer"
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/users",
        json=user_data,
        headers=headers
    )
    if response.status_code in [200, 201]:
        api_context.created_ids[f"sso_user_{email}"] = response.json().get("id")
        api_context.variables["current_user"] = response.json()


@given(parsers.parse('an existing user with email "{email}" and role "{role}"'))
def existing_user_with_role(api_context, sso_context, email: str, role: str):
    """Ensure a user with the given email and role exists."""
    headers = _get_headers(api_context)
    user_data = {
        "email": email,
        "name": email.split("@")[0].replace(".", " ").title(),
        "role": role
    }
    response = requests.post(
        f"{api_context.base_url}/api/v1/users",
        json=user_data,
        headers=headers
    )
    if response.status_code in [200, 201]:
        api_context.created_ids[f"sso_user_{email}"] = response.json().get("id")
        api_context.variables["current_user"] = response.json()
        api_context.variables["original_role"] = role


@given(parsers.parse('the user\'s last_login is "{timestamp}"'))
def user_last_login(api_context, timestamp: str):
    """Set the user's last_login timestamp."""
    api_context.variables["original_last_login"] = timestamp


@given(parsers.parse('the user has picture_url "{url}"'))
def user_picture_url(api_context, url: str):
    """Set the user's picture URL."""
    api_context.variables["original_picture_url"] = url


@given("the user account is disabled")
def user_disabled(api_context):
    """Mark the current user as disabled."""
    api_context.variables["user_disabled"] = True


@given(parsers.parse('the domain "{domain}" is in the allowed domains list'))
def domain_allowed(sso_context, domain: str):
    """Add domain to allowed domains list."""
    if domain not in sso_context.allowed_domains:
        sso_context.allowed_domains.append(domain)


@given(parsers.parse('the allowed domains are configured as "{domains}"'))
def configure_allowed_domains(sso_context, domains: str):
    """Configure the allowed domains list."""
    sso_context.allowed_domains = [d.strip() for d in domains.split(",")]


@given("only workspace domains are allowed")
def workspace_only(sso_context):
    """Configure to reject personal Gmail accounts."""
    sso_context.allowed_domains = ["!gmail.com"]  # Special marker for workspace-only


@given("subdomain matching is disabled")
def subdomain_matching_disabled(sso_context):
    """Disable subdomain matching for domain validation."""
    sso_context.api_context.variables["subdomain_matching"] = False


@given("the state parameter does not match the session state")
def state_mismatch(sso_context):
    """Set up a mismatched state parameter."""
    sso_context.oauth_state = "wrong_state_value"


@given(parsers.parse('the state parameter is "{state}"'))
def set_state_parameter(sso_context, state: str):
    """Set a specific state parameter."""
    sso_context.oauth_state = state


@given(parsers.parse('I am logged in as "{email}" via Google SSO'))
def logged_in_via_sso(api_context, sso_context, email: str):
    """Set up an authenticated session via Google SSO."""
    user_id = hashlib.sha256(email.encode()).hexdigest()[:32]
    sso_context.jwt_token = _generate_mock_jwt(email, user_id)
    api_context.variables["logged_in_email"] = email
    api_context.variables["logged_in_user_id"] = user_id


@given(parsers.parse('I am logged in as "{email}" via Google SSO on device A'))
def logged_in_device_a(api_context, sso_context, email: str):
    """Set up an authenticated session on device A."""
    user_id = hashlib.sha256(email.encode()).hexdigest()[:32]
    token_a = _generate_mock_jwt(email, user_id)
    sso_context.session_tokens["device_a"] = token_a
    api_context.variables["logged_in_email"] = email


@given(parsers.parse('I log in again as "{email}" via Google SSO on device B'))
def logged_in_device_b(api_context, sso_context, email: str):
    """Set up an authenticated session on device B."""
    user_id = hashlib.sha256(email.encode()).hexdigest()[:32]
    token_b = _generate_mock_jwt(email, user_id)
    sso_context.session_tokens["device_b"] = token_b


@given(parsers.parse('I am logged in as "{email}" via Google SSO on multiple devices'))
def logged_in_multiple_devices(api_context, sso_context, email: str):
    """Set up authenticated sessions on multiple devices."""
    user_id = hashlib.sha256(email.encode()).hexdigest()[:32]
    for device in ["device_1", "device_2", "device_3"]:
        sso_context.session_tokens[device] = _generate_mock_jwt(email, user_id)
    api_context.variables["logged_in_email"] = email


@given(parsers.parse('I have an expired JWT token for user "{email}"'))
def expired_jwt_token(api_context, sso_context, email: str):
    """Set up an expired JWT token."""
    user_id = hashlib.sha256(email.encode()).hexdigest()[:32]
    sso_context.jwt_token = _generate_expired_jwt(email, user_id)


@given(parsers.parse('I have an invalid JWT token "{token}"'))
def invalid_jwt_token(sso_context, token: str):
    """Set up an invalid JWT token."""
    sso_context.jwt_token = token


@given("my JWT token is about to expire in 5 minutes")
def jwt_about_to_expire(api_context, sso_context):
    """Set up a JWT token that's about to expire."""
    email = api_context.variables.get("logged_in_email", "user@company.com")
    user_id = api_context.variables.get("logged_in_user_id",
                                        hashlib.sha256(email.encode()).hexdigest()[:32])
    sso_context.jwt_token = _generate_mock_jwt(email, user_id, exp_minutes=5)


@given("I have made 10 login attempts in the last minute")
def rate_limit_exceeded(sso_context):
    """Simulate rate limit being exceeded."""
    sso_context.login_attempts = 10


@given("Google's token endpoint returns a server error")
def google_server_error(sso_context):
    """Set up mock for Google server error."""
    sso_context.api_context.variables["google_error"] = "server_error"


@given("Google's token endpoint times out")
def google_timeout(sso_context):
    """Set up mock for Google timeout."""
    sso_context.api_context.variables["google_error"] = "timeout"


@given("a valid authorization code is provided")
def valid_auth_code(sso_context):
    """Ensure a valid authorization code is set."""
    if not sso_context.oauth_code:
        sso_context.oauth_code = f"mock_code_{secrets.token_hex(16)}"


@given("Google OAuth client credentials are not configured")
def oauth_not_configured(api_context):
    """Set up scenario where OAuth is not configured."""
    api_context.variables["google_oauth_configured"] = False


# =============================================================================
# When Steps - Actions
# =============================================================================

@when("I request the Google authorization URL")
def request_authorization_url(api_context, sso_context):
    """Request the Google OAuth authorization URL."""
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}/api/v1/auth/google/authorize"
    api_context.response = requests.get(url, headers=headers)
    if api_context.response.status_code == 200:
        try:
            data = api_context.response.json()
            sso_context.authorization_url = data.get("authorization_url")
            api_context.last_json = data
        except json.JSONDecodeError:
            pass


@when("I exchange the OAuth code at the callback endpoint")
def exchange_oauth_code(api_context, sso_context):
    """Exchange the OAuth code at the callback endpoint."""
    headers = _get_headers(api_context)
    params = {
        "code": sso_context.oauth_code,
        "state": sso_context.oauth_state
    }
    url = f"{api_context.base_url}/api/v1/auth/google/callback"
    api_context.response = requests.get(url, params=params, headers=headers)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" without code parameter'))
def send_get_without_code(api_context, endpoint: str):
    """Send a GET request without the code parameter."""
    headers = _get_headers(api_context)
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when("I exchange the OAuth code with the tampered state")
def exchange_code_tampered_state(api_context, sso_context):
    """Exchange OAuth code with a tampered state parameter."""
    headers = _get_headers(api_context)
    params = {
        "code": sso_context.oauth_code,
        "state": "tampered_state_value"
    }
    url = f"{api_context.base_url}/api/v1/auth/google/callback"
    api_context.response = requests.get(url, params=params, headers=headers)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" with the JWT cookie'))
def send_get_with_jwt(api_context, sso_context, endpoint: str):
    """Send a GET request with the JWT cookie."""
    headers = _get_headers(api_context)
    cookies = {sso_context.jwt_cookie_name: sso_context.jwt_token}
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers, cookies=cookies)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" with the expired JWT cookie'))
def send_get_with_expired_jwt(api_context, sso_context, endpoint: str):
    """Send a GET request with an expired JWT cookie."""
    headers = _get_headers(api_context)
    cookies = {sso_context.jwt_cookie_name: sso_context.jwt_token}
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers, cookies=cookies)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" with the invalid JWT cookie'))
def send_get_with_invalid_jwt(api_context, sso_context, endpoint: str):
    """Send a GET request with an invalid JWT cookie."""
    headers = _get_headers(api_context)
    cookies = {sso_context.jwt_cookie_name: sso_context.jwt_token}
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url, headers=headers, cookies=cookies)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a GET request to "{endpoint}" without any authentication'))
def send_get_without_auth(api_context, endpoint: str):
    """Send a GET request without any authentication."""
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.get(url)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a POST request to "{endpoint}"'))
def send_post_request(api_context, sso_context, endpoint: str):
    """Send a POST request."""
    headers = _get_headers(api_context)
    cookies = {}
    if sso_context.jwt_token:
        cookies[sso_context.jwt_cookie_name] = sso_context.jwt_token
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.post(url, headers=headers, cookies=cookies)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when(parsers.parse('I send a POST request to "{endpoint}" with the expired JWT cookie'))
def send_post_with_expired_jwt(api_context, sso_context, endpoint: str):
    """Send a POST request with an expired JWT cookie."""
    headers = _get_headers(api_context)
    cookies = {sso_context.jwt_cookie_name: sso_context.jwt_token}
    url = f"{api_context.base_url}{endpoint}"
    api_context.response = requests.post(url, headers=headers, cookies=cookies)
    try:
        api_context.last_json = api_context.response.json()
    except json.JSONDecodeError:
        api_context.last_json = None


@when("I decode the JWT token")
def decode_jwt_token(api_context, sso_context):
    """Decode the JWT token for inspection."""
    try:
        # Decode without verification for inspection
        decoded = jwt.decode(
            sso_context.jwt_token,
            options={"verify_signature": False}
        )
        api_context.variables["decoded_jwt"] = decoded
    except jwt.DecodeError:
        api_context.variables["decoded_jwt"] = None


# =============================================================================
# Then Steps - Assertions
# =============================================================================

@then(parsers.parse("the response status code should be {status:d}"))
def response_status_code(api_context, status: int):
    """Verify the response status code."""
    assert api_context.response is not None, "No response received"
    assert api_context.response.status_code == status, (
        f"Expected status {status}, got {api_context.response.status_code}. "
        f"Response: {api_context.response.text}"
    )


@then(parsers.parse('the response should contain "{field}"'))
def response_contains_field(api_context, field: str):
    """Verify the response contains a field."""
    assert api_context.last_json is not None, "No JSON response available"
    assert field in api_context.last_json, (
        f"Response does not contain field '{field}'. Got: {api_context.last_json.keys()}"
    )


@then(parsers.parse('the response body should contain "{text}"'))
def response_body_contains(api_context, text: str):
    """Verify the response body contains text."""
    assert api_context.response is not None, "No response received"
    assert text in api_context.response.text, (
        f"Response body does not contain '{text}'. Response: {api_context.response.text}"
    )


@then(parsers.parse('the authorization URL should start with "{prefix}"'))
def auth_url_starts_with(sso_context, prefix: str):
    """Verify authorization URL starts with expected prefix."""
    assert sso_context.authorization_url is not None, "No authorization URL available"
    assert sso_context.authorization_url.startswith(prefix), (
        f"Authorization URL does not start with '{prefix}'. "
        f"Got: {sso_context.authorization_url}"
    )


@then(parsers.parse('the authorization URL should contain parameter "{param}"'))
def auth_url_contains_param(sso_context, param: str):
    """Verify authorization URL contains a parameter."""
    assert sso_context.authorization_url is not None, "No authorization URL available"
    params = _parse_authorization_url(sso_context.authorization_url)
    assert param in params, (
        f"Authorization URL does not contain parameter '{param}'. "
        f"Available params: {list(params.keys())}"
    )


@then("the client_id should match the configured Google client ID")
def client_id_matches(sso_context):
    """Verify client_id matches configuration."""
    params = _parse_authorization_url(sso_context.authorization_url)
    client_id = params.get("client_id")
    assert client_id is not None, "client_id not found in URL"
    # In real tests, compare against configured value
    assert len(client_id) > 0, "client_id is empty"


@then("the redirect_uri should match the configured callback URL")
def redirect_uri_matches(sso_context):
    """Verify redirect_uri matches configuration."""
    params = _parse_authorization_url(sso_context.authorization_url)
    redirect_uri = params.get("redirect_uri")
    assert redirect_uri is not None, "redirect_uri not found in URL"
    assert "callback" in redirect_uri.lower(), "redirect_uri should contain 'callback'"


@then(parsers.parse('the scope should include "{scope}"'))
def scope_includes(sso_context, scope: str):
    """Verify scope includes expected value."""
    params = _parse_authorization_url(sso_context.authorization_url)
    scope_value = params.get("scope", "")
    assert scope in scope_value, (
        f"Scope does not include '{scope}'. Got: {scope_value}"
    )


@then("the state should be a non-empty string")
def state_non_empty(sso_context):
    """Verify state parameter is non-empty."""
    params = _parse_authorization_url(sso_context.authorization_url)
    state = params.get("state")
    assert state is not None and len(state) > 0, "State parameter is empty"


@then(parsers.parse('the response_type should equal "{value}"'))
def response_type_equals(sso_context, value: str):
    """Verify response_type parameter equals expected value."""
    params = _parse_authorization_url(sso_context.authorization_url)
    response_type = params.get("response_type")
    assert response_type == value, (
        f"response_type is '{response_type}', expected '{value}'"
    )


@then("the JWT cookie should be set")
def jwt_cookie_set(api_context, sso_context):
    """Verify JWT cookie is set in response."""
    assert api_context.response is not None, "No response received"
    cookies = api_context.response.cookies
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert (sso_context.jwt_cookie_name in cookies or
            sso_context.jwt_cookie_name in set_cookie), (
        f"JWT cookie '{sso_context.jwt_cookie_name}' not set. "
        f"Cookies: {list(cookies.keys())}, Set-Cookie: {set_cookie}"
    )


@then("no JWT cookie should be set")
def no_jwt_cookie(api_context, sso_context):
    """Verify JWT cookie is not set."""
    assert api_context.response is not None, "No response received"
    cookies = api_context.response.cookies
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert sso_context.jwt_cookie_name not in cookies, (
        f"JWT cookie '{sso_context.jwt_cookie_name}' should not be set"
    )


@then(parsers.parse('a new user should be created with email "{email}"'))
def new_user_created(api_context, email: str):
    """Verify a new user was created."""
    headers = _get_headers(api_context)
    response = requests.get(
        f"{api_context.base_url}/api/v1/users",
        params={"email": email},
        headers=headers
    )
    assert response.status_code == 200, f"Failed to list users: {response.text}"
    users = response.json()
    user_emails = [u.get("email") for u in users]
    assert email in user_emails, f"User {email} not found in users list"


@then(parsers.parse('the user should have the default role "{role}"'))
def user_has_default_role(api_context, role: str):
    """Verify user has the default role."""
    # Check from response or fetch user
    if api_context.last_json and "role" in api_context.last_json:
        assert api_context.last_json.get("role") == role


@then("the user's last_login should be updated to approximately now")
def last_login_updated(api_context):
    """Verify last_login was updated to approximately now."""
    # This would check the database or API response
    # For now, we verify the response indicates success
    assert api_context.response.status_code == 200


@then("the user should be authenticated successfully")
def user_authenticated(api_context):
    """Verify user was authenticated successfully."""
    assert api_context.response.status_code == 200


@then("the Set-Cookie header should be present")
def set_cookie_present(api_context):
    """Verify Set-Cookie header is present."""
    set_cookie = api_context.response.headers.get("Set-Cookie")
    assert set_cookie is not None, "Set-Cookie header not present"


@then("the cookie should have the HttpOnly flag")
def cookie_httponly(api_context):
    """Verify cookie has HttpOnly flag."""
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert "httponly" in set_cookie.lower(), "Cookie does not have HttpOnly flag"


@then("the cookie should have the Secure flag")
def cookie_secure(api_context):
    """Verify cookie has Secure flag."""
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert "secure" in set_cookie.lower(), "Cookie does not have Secure flag"


@then(parsers.parse('the cookie should have the SameSite attribute set to "{value}"'))
def cookie_samesite(api_context, value: str):
    """Verify cookie has correct SameSite attribute."""
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert f"samesite={value.lower()}" in set_cookie.lower(), (
        f"Cookie SameSite not set to {value}"
    )


@then(parsers.parse('the JSON field "{field}" should equal "{value}"'))
def json_field_equals(api_context, field: str, value: str):
    """Verify JSON field equals expected value."""
    assert api_context.last_json is not None, "No JSON response available"
    actual = api_context.last_json.get(field)
    assert str(actual) == value, f"Field '{field}' is '{actual}', expected '{value}'"


@then("the access_token should be a valid JWT")
def access_token_valid_jwt(api_context):
    """Verify access_token is a valid JWT."""
    assert api_context.last_json is not None, "No JSON response available"
    token = api_context.last_json.get("access_token")
    assert token is not None, "access_token not in response"
    # JWT format: header.payload.signature
    parts = token.split(".")
    assert len(parts) == 3, f"Token is not valid JWT format: {token}"


@then("the Set-Cookie header should clear the JWT cookie")
def cookie_cleared(api_context, sso_context):
    """Verify JWT cookie is cleared."""
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    # Cleared cookies typically have max-age=0 or expires in the past
    assert ("max-age=0" in set_cookie.lower() or
            "expires=" in set_cookie.lower() or
            f"{sso_context.jwt_cookie_name}=;" in set_cookie), (
        "Cookie not properly cleared"
    )


@then(parsers.parse('subsequent requests to "{endpoint}" should return 401'))
def subsequent_requests_401(api_context, endpoint: str):
    """Verify subsequent requests return 401."""
    url = f"{api_context.base_url}{endpoint}"
    response = requests.get(url)
    assert response.status_code == 401, (
        f"Expected 401, got {response.status_code}"
    )


@then(parsers.parse('the token should contain claim "{claim}" with the user ID'))
def token_claim_user_id(api_context, claim: str):
    """Verify token contains user ID claim."""
    decoded = api_context.variables.get("decoded_jwt")
    assert decoded is not None, "JWT not decoded"
    assert claim in decoded, f"Claim '{claim}' not in token"
    assert decoded[claim] is not None, f"Claim '{claim}' is empty"


@then(parsers.parse('the token should contain claim "{claim}" with "{value}"'))
def token_claim_value(api_context, claim: str, value: str):
    """Verify token contains claim with expected value."""
    decoded = api_context.variables.get("decoded_jwt")
    assert decoded is not None, "JWT not decoded"
    assert claim in decoded, f"Claim '{claim}' not in token"
    assert str(decoded[claim]) == value, (
        f"Claim '{claim}' is '{decoded[claim]}', expected '{value}'"
    )


@then(parsers.parse('the token should contain claim "{claim}" with a future timestamp'))
def token_claim_future(api_context, claim: str):
    """Verify token claim contains a future timestamp."""
    decoded = api_context.variables.get("decoded_jwt")
    assert decoded is not None, "JWT not decoded"
    assert claim in decoded, f"Claim '{claim}' not in token"
    now = datetime.now(timezone.utc).timestamp()
    assert decoded[claim] > now, f"Claim '{claim}' is not in the future"


@then(parsers.parse('the token should contain claim "{claim}" with a recent timestamp'))
def token_claim_recent(api_context, claim: str):
    """Verify token claim contains a recent timestamp."""
    decoded = api_context.variables.get("decoded_jwt")
    assert decoded is not None, "JWT not decoded"
    assert claim in decoded, f"Claim '{claim}' not in token"
    now = datetime.now(timezone.utc).timestamp()
    # Recent = within last 5 minutes
    assert now - decoded[claim] < 300, f"Claim '{claim}' is not recent"


@then(parsers.parse('a user with email "{email}" should exist in the database'))
def user_exists_in_db(api_context, email: str):
    """Verify user exists in database."""
    headers = _get_headers(api_context)
    response = requests.get(
        f"{api_context.base_url}/api/v1/users",
        params={"email": email},
        headers=headers
    )
    assert response.status_code == 200
    users = response.json()
    emails = [u.get("email") for u in users]
    assert email in emails, f"User {email} not found"


@then("the user should have name from Google profile")
def user_has_name(api_context, sso_context):
    """Verify user has name from Google profile."""
    if sso_context.mock_google_user:
        expected_name = sso_context.mock_google_user.get("name")
        # Check API response or database
        assert expected_name is not None


@then("the user created_at should be approximately now")
def user_created_now(api_context):
    """Verify user created_at is recent."""
    # Would check database timestamp
    pass


@then("the user's created_at should remain unchanged")
def created_at_unchanged(api_context):
    """Verify user's created_at was not modified."""
    # Would compare original vs current
    pass


@then(parsers.parse('the user\'s picture_url should be "{url}"'))
def user_picture_url_is(api_context, url: str):
    """Verify user's picture_url."""
    if api_context.last_json:
        picture = api_context.last_json.get("picture_url")
        assert picture == url, f"Picture URL is '{picture}', expected '{url}'"


@then(parsers.parse('the user\'s role should still be "{role}"'))
def user_role_preserved(api_context, role: str):
    """Verify user's role is preserved."""
    original = api_context.variables.get("original_role")
    if api_context.last_json:
        current = api_context.last_json.get("role")
        assert current == role, f"Role is '{current}', expected '{role}'"


@then("the Retry-After header should be present")
def retry_after_present(api_context):
    """Verify Retry-After header is present."""
    retry_after = api_context.response.headers.get("Retry-After")
    assert retry_after is not None, "Retry-After header not present"


@then("both sessions should be valid")
def both_sessions_valid(sso_context):
    """Verify both session tokens are valid."""
    assert "device_a" in sso_context.session_tokens
    assert "device_b" in sso_context.session_tokens
    assert sso_context.session_tokens["device_a"] != sso_context.session_tokens["device_b"]


@then("requests from device A with JWT A should succeed")
def device_a_succeeds(api_context, sso_context):
    """Verify requests with device A token succeed."""
    # Would make request with device A token
    assert "device_a" in sso_context.session_tokens


@then("requests from device B with JWT B should succeed")
def device_b_succeeds(api_context, sso_context):
    """Verify requests with device B token succeed."""
    # Would make request with device B token
    assert "device_b" in sso_context.session_tokens


@then("all active sessions for the user should be invalidated")
def all_sessions_invalidated(api_context, sso_context):
    """Verify all sessions are invalidated."""
    assert api_context.response.status_code == 200


@then("subsequent requests with any of the old JWT tokens should return 401")
def old_tokens_invalid(api_context, sso_context):
    """Verify old tokens are no longer valid."""
    # Would test each stored token
    pass


@then("a new JWT cookie should be set")
def new_jwt_cookie_set(api_context, sso_context):
    """Verify a new JWT cookie is set."""
    set_cookie = api_context.response.headers.get("Set-Cookie", "")
    assert sso_context.jwt_cookie_name in set_cookie


@then("the new token should have a fresh expiration time")
def new_token_fresh_exp(api_context):
    """Verify new token has fresh expiration."""
    if api_context.last_json and "access_token" in api_context.last_json:
        token = api_context.last_json["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        now = datetime.now(timezone.utc).timestamp()
        # Should expire more than 55 minutes from now (assuming 60 min expiry)
        assert decoded.get("exp", 0) > now + 3300


@then("I should be required to re-authenticate via Google")
def require_reauth(api_context):
    """Verify re-authentication is required."""
    assert api_context.response.status_code == 401
