"""Pytest configuration and fixtures for Sliples runner."""

import os
from typing import Generator

import pytest
from playwright.sync_api import Page, Browser, BrowserContext, Playwright, sync_playwright

# Import step definitions
from steps import navigation, forms, assertions, common, api


@pytest.fixture(scope="session")
def browser_type() -> str:
    """Get browser type from environment."""
    return os.getenv("BROWSER", "chromium")


@pytest.fixture(scope="session")
def browser_url() -> str | None:
    """Get remote browser URL if configured."""
    browser = os.getenv("BROWSER", "chromium")
    if browser == "chromium" or browser == "chrome":
        return os.getenv("BROWSER_CHROME_URL")
    elif browser == "firefox":
        return os.getenv("BROWSER_FIREFOX_URL")
    return None


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get base URL for tests."""
    return os.getenv("BASE_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    """Create Playwright instance."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(
    playwright_instance: Playwright,
    browser_type: str,
    browser_url: str | None,
) -> Generator[Browser, None, None]:
    """Create browser instance."""
    browser_types = {
        "chromium": playwright_instance.chromium,
        "chrome": playwright_instance.chromium,
        "firefox": playwright_instance.firefox,
        "webkit": playwright_instance.webkit,
    }

    browser_launcher = browser_types.get(browser_type, playwright_instance.chromium)

    if browser_url:
        # Connect to remote browser
        browser = browser_launcher.connect(browser_url)
    else:
        # Launch local browser
        browser = browser_launcher.launch(headless=True)

    yield browser
    browser.close()


@pytest.fixture
def context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Create browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Create page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def screenshots_dir() -> str:
    """Get screenshots directory."""
    dir_path = os.getenv("SCREENSHOTS_DIR", "/tmp/screenshots")
    os.makedirs(dir_path, exist_ok=True)
    return dir_path


# Store test context for step definitions
class TestContext:
    """Shared context between steps."""

    def __init__(self):
        self.page: Page | None = None
        self.base_url: str = ""
        self.variables: dict = {}
        self.screenshots: list[str] = []


@pytest.fixture
def test_context(page: Page, base_url: str) -> TestContext:
    """Create test context for step definitions."""
    ctx = TestContext()
    ctx.page = page
    ctx.base_url = base_url
    return ctx


# =============================================================================
# API Testing Fixtures
# =============================================================================


class APIContext:
    """Shared context for API testing."""

    def __init__(self):
        self.base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.api_key: str | None = os.getenv("API_KEY")
        self.response = None
        self.last_json: dict | list | None = None
        self.created_ids: dict = {}
        self.variables: dict = {}


@pytest.fixture
def api_context() -> Generator[APIContext, None, None]:
    """Create API context for API testing step definitions."""
    ctx = APIContext()
    yield ctx
    # Cleanup: delete any resources created during the test
    # This is optional but helps keep the test environment clean
    _cleanup_api_resources(ctx)


def _cleanup_api_resources(ctx: APIContext) -> None:
    """Clean up resources created during API tests."""
    import requests

    headers = {"Content-Type": "application/json"}
    if ctx.api_key:
        headers["X-API-Key"] = ctx.api_key

    # Clean up created repositories (delete in reverse order)
    if "repo" in ctx.created_ids:
        repo_id = ctx.created_ids["repo"]
        try:
            requests.delete(f"{ctx.base_url}/api/v1/repos/{repo_id}", headers=headers)
        except Exception:
            pass  # Ignore cleanup errors

    # Clean up created test runs (cancel if still running)
    if "run" in ctx.created_ids:
        run_id = ctx.created_ids["run"]
        try:
            requests.delete(f"{ctx.base_url}/api/v1/runs/{run_id}", headers=headers)
        except Exception:
            pass  # Ignore cleanup errors
