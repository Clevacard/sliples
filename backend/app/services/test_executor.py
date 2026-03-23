"""Test executor service for running Playwright tests."""

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    """Result of executing a single test step."""

    step_name: str
    status: str  # passed, failed, skipped, error
    duration_ms: int = 0
    error_message: Optional[str] = None
    screenshot_data: Optional[bytes] = None


@dataclass
class ScenarioResult:
    """Result of executing a scenario."""

    scenario_id: str
    scenario_name: str
    status: str  # passed, failed, error
    steps: list[StepResult] = field(default_factory=list)


@dataclass
class TestExecutionResult:
    """Result of executing all tests in a run."""

    run_id: str
    status: str  # passed, failed, error
    scenarios: list[ScenarioResult] = field(default_factory=list)
    total_duration_ms: int = 0


class GherkinStepRegistry:
    """Registry of Gherkin step definitions with their implementations."""

    # CSS class patterns that indicate a disabled element
    DISABLED_CSS_PATTERNS = ["disabled", "is-disabled", "btn-disabled", "disabled-true"]

    def __init__(self, pages: Optional[dict[str, str]] = None):
        """Initialize the step registry with built-in steps.

        Args:
            pages: Optional dict of page_name -> path for named page navigation
        """
        self._steps: dict[str, tuple[re.Pattern, Callable]] = {}
        self._pages = pages or {}  # page_name -> path mapping
        self._register_builtin_steps()

    def set_pages(self, pages: dict[str, str]):
        """Set the pages mapping for navigation."""
        self._pages = pages

    def resolve_page(self, name: str) -> Optional[str]:
        """Resolve a page name to its path.

        Args:
            name: Page name (case-insensitive)

        Returns:
            Path if found, None otherwise
        """
        # Try exact match first
        if name in self._pages:
            return self._pages[name]
        # Try case-insensitive match
        name_lower = name.lower()
        for page_name, path in self._pages.items():
            if page_name.lower() == name_lower:
                return path
        return None

    def _register_builtin_steps(self):
        """Register built-in Gherkin step definitions."""
        # Navigation steps - with quotes
        self.register(
            r'I navigate to "([^"]*)"',
            self._step_navigate,
        )
        self.register(
            r'I go to "([^"]*)"',
            self._step_navigate,
        )
        self.register(
            r'I am on the "([^"]*)" page',
            self._step_navigate,
        )
        self.register(
            r'I visit "([^"]*)"',
            self._step_navigate,
        )
        # Navigation steps - without quotes (for named pages)
        self.register(
            r'I navigate to (\w+)',
            self._step_navigate,
        )
        self.register(
            r'I go to (\w+)',
            self._step_navigate,
        )
        self.register(
            r'I am on (\w+)',
            self._step_navigate,
        )
        self.register(
            r'I visit (\w+)',
            self._step_navigate,
        )
        # Navigation to "the X page" pattern
        self.register(
            r'I (?:navigate|go) to the (\w+) page',
            self._step_navigate,
        )
        self.register(
            r'I am on the (\w+) page',
            self._step_navigate,
        )

        # Click steps
        self.register(
            r'I click (?:on )?(?:the )?"([^"]*)"(?: button| link| element)?',
            self._step_click,
        )
        self.register(
            r'I click (?:on )?(?:the )?element with (?:text|label) "([^"]*)"',
            self._step_click_text,
        )
        self.register(
            r'I click (?:on )?(?:the )?element "([^"]*)"',
            self._step_click_selector,
        )

        # Input steps
        self.register(
            r'I press Tab',
            self._step_press_tab,
        )
        self.register(
            r'I (?:enter|type|fill in) "([^"]*)" (?:in|into) (?:the )?"([^"]*)"(?: field| input)?',
            self._step_fill,
        )
        self.register(
            r'I fill "([^"]*)" with "([^"]*)"',
            self._step_fill_reversed,
        )
        self.register(
            r'I clear (?:the )?"([^"]*)"(?: field| input)?',
            self._step_clear,
        )
        self.register(
            r'I fill input "([^"]*)" with "([^"]*)"',
            self._step_fill_selector,
        )

        # Assertion steps
        self.register(
            r'I should see "([^"]*)"',
            self._step_should_see,
        )
        self.register(
            r'I should not see "([^"]*)"',
            self._step_should_not_see,
        )
        self.register(
            r'(?:the )?page should contain "([^"]*)"',
            self._step_should_see,
        )
        self.register(
            r'(?:the )?title should (?:be|contain) "([^"]*)"',
            self._step_title_contains,
        )
        self.register(
            r'(?:the )?URL should (?:be|contain) "([^"]*)"',
            self._step_url_contains,
        )
        self.register(
            r'(?:the )?element "([^"]*)" should (?:be )?visible',
            self._step_element_visible,
        )
        self.register(
            r'(?:the )?element "([^"]*)" should not (?:be )?visible',
            self._step_element_not_visible,
        )
        self.register(
            r'(?:the )?element "([^"]*)" should have (?:text|value) "([^"]*)"',
            self._step_element_has_text,
        )
        self.register(
            r'(?:the )?"([^"]+)" should be (?:enabled|clickable)',
            self._step_element_enabled,
        )
        self.register(
            r'(?:the )?"([^"]+)" should (?:be disabled|not be (?:enabled|clickable))',
            self._step_element_disabled,
        )

        # CSS selector visibility assertions (e.g., ".cardArtwork" is visible)
        self.register(
            r'"([^"]+)" is visible',
            self._step_selector_visible,
        )
        self.register(
            r'"([^"]+)" is (?:hidden|not visible)',
            self._step_selector_hidden,
        )
        self.register(
            r'"([^"]+)" should be visible',
            self._step_selector_visible,
        )
        self.register(
            r'"([^"]+)" should be hidden',
            self._step_selector_hidden,
        )
        self.register(
            r'"([^"]+)" should not be visible',
            self._step_selector_hidden,
        )

        # Wait steps
        self.register(
            r'I wait (?:for )?(\d+) seconds?',
            self._step_wait,
        )
        self.register(
            r'I wait for (?:the )?element "([^"]*)" to (?:be )?visible',
            self._step_wait_visible,
        )
        self.register(
            r'I wait for (?:the )?page to load',
            self._step_wait_load,
        )

        # Select/checkbox steps
        self.register(
            r'I select "([^"]*)" from "([^"]*)"',
            self._step_select,
        )
        self.register(
            r'I check (?:the )?"([^"]*)"(?: checkbox)?',
            self._step_check,
        )
        self.register(
            r'I uncheck (?:the )?"([^"]*)"(?: checkbox)?',
            self._step_uncheck,
        )

        # Screenshot step
        self.register(
            r'I take a screenshot',
            self._step_screenshot,
        )

        # Form steps
        self.register(
            r'I submit (?:the )?form',
            self._step_submit_form,
        )
        self.register(
            r'I press (?:the )?"([^"]*)" key',
            self._step_press_key,
        )

    def register(self, pattern: str, handler: Callable):
        """Register a step pattern with its handler."""
        self._steps[pattern] = (re.compile(pattern, re.IGNORECASE), handler)

    def find_handler(self, step_text: str) -> Optional[tuple[Callable, tuple]]:
        """Find a handler for the given step text."""
        for pattern, (regex, handler) in self._steps.items():
            match = regex.fullmatch(step_text)
            if match:
                return handler, match.groups()
        return None

    # Built-in step implementations
    # These are async methods that take (page, *args) where page is a Playwright page

    async def _step_navigate(self, page, url_or_page: str):
        """Navigate to URL or named page.

        If the input matches a named page, uses the page's configured path.
        Otherwise treats it as a URL/path.
        """
        # Check if this is a named page
        resolved_path = self.resolve_page(url_or_page)
        if resolved_path:
            url = resolved_path
            logger.info(f"Resolved page '{url_or_page}' to path '{url}'")
        else:
            url = url_or_page

        # Handle relative URLs
        if not url.startswith(("http://", "https://")):
            base_url = getattr(page, "_base_url", "")
            logger.info(f"Navigation: resolved path='{url}', base_url='{base_url}'")
            # Ensure path starts with /
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"{base_url.rstrip('/')}{url}"

        logger.info(f"Navigating to: {url}")
        await page.goto(url, wait_until="domcontentloaded")

    async def _step_click(self, page, text: str):
        """Click element by test-id, text, or role."""
        # Try multiple strategies: test-id first, then role, then text
        locator = page.get_by_test_id(text).or_(
            page.get_by_role("button", name=text)
        ).or_(
            page.get_by_role("link", name=text)
        ).or_(
            page.get_by_text(text, exact=True)
        )
        await locator.first.click()

    async def _step_click_text(self, page, text: str):
        """Click element by text content."""
        await page.get_by_text(text, exact=True).first.click()

    async def _step_click_selector(self, page, selector: str):
        """Click element by CSS selector."""
        await page.locator(selector).first.click()

    async def _step_press_tab(self, page):
        await page.locator("body").press("Tab")  # Trigger blur/validation

    async def _step_fill(self, page, value: str, field: str):
        """Fill input field with simulated typing to trigger validation."""
        locator = page.get_by_label(field).or_(
            page.get_by_placeholder(field)
        ).or_(
            page.locator(f'[name="{field}"]')
        ).or_(
            page.locator(f'#{field}')
        )
        element = locator.first
        await element.clear()
        await element.press_sequentially(value)


    async def _step_fill_reversed(self, page, field: str, value: str):
        """Fill input field (reversed argument order)."""
        await self._step_fill(page, value, field)


    async def _step_fill_selector(self, page, selector: str, value: str):
        """Fill input by CSS selector with simulated typing."""
        element = page.locator(selector).first
        await element.clear()
        await element.press_sequentially(value)


    async def _step_clear(self, page, field: str):
        """Clear input field."""
        locator = page.get_by_label(field).or_(
            page.get_by_placeholder(field)
        ).or_(
            page.locator(f'[name="{field}"]')
        )
        await locator.first.clear()

    async def _step_should_see(self, page, text: str):
        """Assert text is visible on page."""
        await page.get_by_text(text).first.wait_for(state="visible", timeout=10000)

    async def _step_should_not_see(self, page, text: str):
        """Assert text is not visible on page."""
        await page.get_by_text(text).first.wait_for(state="hidden", timeout=10000)

    async def _step_title_contains(self, page, text: str):
        """Assert page title contains text."""
        import asyncio
        from playwright.async_api import expect
        await expect(page).to_have_title(re.compile(re.escape(text), re.IGNORECASE))

    async def _step_url_contains(self, page, text: str):
        """Assert URL contains text."""
        from playwright.async_api import expect
        await expect(page).to_have_url(re.compile(re.escape(text)))

    async def _step_element_visible(self, page, selector: str):
        """Assert element is visible."""
        await page.locator(selector).first.wait_for(state="visible", timeout=10000)

    async def _step_element_not_visible(self, page, selector: str):
        """Assert element is not visible."""
        await page.locator(selector).first.wait_for(state="hidden", timeout=10000)

    async def _step_element_has_text(self, page, selector: str, text: str):
        """Assert element has specific text."""
        from playwright.async_api import expect
        await expect(page.locator(selector).first).to_have_text(text)

    async def _step_element_enabled(self, page, text: str):
        """Assert element is enabled/clickable (checks both HTML disabled and CSS classes)."""
        from playwright.async_api import expect
        locator = page.get_by_test_id(text).or_(
            page.get_by_role("button", name=text)
        ).or_(
            page.get_by_role("link", name=text)
        ).or_(
            page.get_by_text(text, exact=True)
        )
        element = locator.first
        # Check HTML disabled attribute
        await expect(element).to_be_enabled()
        # Check common CSS disabled patterns
        class_attr = await element.get_attribute("class") or ""
        classes = {c.lower() for c in class_attr.split()}
        for pattern in self.DISABLED_CSS_PATTERNS:
            if pattern.lower() in classes:
                raise AssertionError(f"Element has disabled CSS class: {class_attr}")

    async def _step_element_disabled(self, page, text: str):
        """Assert element is disabled (checks both HTML disabled and CSS classes)."""
        locator = page.get_by_test_id(text).or_(
            page.get_by_role("button", name=text)
        ).or_(
            page.get_by_role("link", name=text)
        ).or_(
            page.get_by_text(text, exact=True)
        )
        element = locator.first
        # Check common CSS disabled patterns first
        class_attr = await element.get_attribute("class") or ""
        classes = {c.lower() for c in class_attr.split()}
        has_disabled_class = bool(classes & {p.lower() for p in self.DISABLED_CSS_PATTERNS})
        # Check HTML disabled attribute
        is_html_disabled = await element.is_disabled()
        if not has_disabled_class and not is_html_disabled:
            raise AssertionError(f"Element is not disabled. Class: {class_attr}")

    async def _step_selector_visible(self, page, selector: str):
        """Assert element matching CSS selector is visible."""
        await page.locator(selector).first.wait_for(state="visible", timeout=10000)

    async def _step_selector_hidden(self, page, selector: str):
        """Assert element matching CSS selector is hidden."""
        await page.locator(selector).first.wait_for(state="hidden", timeout=10000)

    async def _step_wait(self, page, seconds: str):
        """Wait for specified seconds."""
        import asyncio
        await asyncio.sleep(int(seconds))

    async def _step_wait_visible(self, page, selector: str):
        """Wait for element to be visible."""
        await page.locator(selector).first.wait_for(state="visible", timeout=30000)

    async def _step_wait_load(self, page):
        """Wait for page to load."""
        await page.wait_for_load_state("domcontentloaded")

    async def _step_select(self, page, value: str, field: str):
        """Select option from dropdown."""
        locator = page.get_by_label(field).or_(
            page.locator(f'[name="{field}"]')
        ).or_(
            page.locator(f'#{field}')
        )
        await locator.first.select_option(label=value)

    async def _step_check(self, page, field: str):
        """Check checkbox."""
        locator = page.get_by_label(field).or_(
            page.locator(f'[name="{field}"]')
        )
        await locator.first.check()

    async def _step_uncheck(self, page, field: str):
        """Uncheck checkbox."""
        locator = page.get_by_label(field).or_(
            page.locator(f'[name="{field}"]')
        )
        await locator.first.uncheck()

    async def _step_screenshot(self, page):
        """Take screenshot (handled by executor)."""
        pass  # Screenshot capture is handled at executor level

    async def _step_submit_form(self, page):
        """Submit current form."""
        await page.locator("form").first.locator('button[type="submit"], input[type="submit"]').first.click()

    async def _step_press_key(self, page, key: str):
        """Press keyboard key."""
        await page.keyboard.press(key)


class TestExecutor:
    """Executes Gherkin scenarios using Playwright."""

    def __init__(self, browser: str = "chrome", pages: Optional[dict[str, str]] = None):
        """
        Initialize the test executor.

        Args:
            browser: Browser to use ('chrome' or 'firefox')
            pages: Optional dict of page_name -> path for named page navigation
        """
        self.settings = get_settings()
        self.browser = browser
        self.step_registry = GherkinStepRegistry(pages=pages)
        self._playwright = None
        self._browser = None
        self._context = None

    def set_pages(self, pages: dict[str, str]):
        """Set pages for named page navigation."""
        self.step_registry.set_pages(pages)

    def _get_browser_url(self) -> str:
        """Get the WebSocket URL for the selected browser."""
        if self.browser == "firefox":
            return self.settings.browser_firefox_url
        return self.settings.browser_chrome_url

    async def connect(self) -> None:
        """Connect to remote browser."""
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()

        browser_url = self._get_browser_url()
        logger.info(f"Connecting to browser at {browser_url}")

        try:
            if self.browser == "firefox":
                self._browser = await self._playwright.firefox.connect(browser_url)
            else:
                self._browser = await self._playwright.chromium.connect(browser_url)
            logger.info(f"Connected to {self.browser} browser")
        except Exception as e:
            logger.error(f"Failed to connect to browser: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from browser."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Disconnected from browser")

    async def create_context(
        self,
        base_url: str,
        locale: str = "en-GB",
        timezone_id: str = "Europe/London",
    ) -> None:
        """Create a new browser context."""
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
            locale=locale,
            timezone_id=timezone_id,
        )
        # Store base URL for relative navigation
        self._base_url = base_url

    async def _parse_gherkin_content(self, content: str) -> list[dict]:
        """
        Parse Gherkin content and extract steps.

        Args:
            content: Gherkin feature file content

        Returns:
            List of step dictionaries with 'keyword' and 'text'
        """
        steps = []
        lines = content.strip().split("\n")

        keywords = ("Given", "When", "Then", "And", "But")
        current_keyword = None

        for line in lines:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Check for step keywords
            for keyword in keywords:
                if line.startswith(keyword + " "):
                    text = line[len(keyword) + 1:].strip()
                    # 'And' and 'But' inherit the previous keyword
                    if keyword in ("And", "But"):
                        keyword = current_keyword or "Given"
                    else:
                        current_keyword = keyword

                    steps.append({
                        "keyword": keyword,
                        "text": text,
                        "full": line,
                    })
                    break

        return steps

    async def _execute_custom_step_code(
        self,
        page,
        code: str,
        params: dict,
    ) -> None:
        """
        Execute custom step code with proper Playwright context.

        The code can be in two formats:
        1. pytest-bdd style with decorators (legacy from seed data)
        2. Simple function body that uses 'page' and named params

        Args:
            page: Playwright page object
            code: Python code to execute
            params: Dict of captured parameters from step pattern
        """
        # Try to extract the function body from decorator-style code
        lines = code.strip().split('\n')
        func_body_lines = []
        in_function = False
        base_indent = None

        for line in lines:
            # Skip import lines and decorators
            if line.strip().startswith(('from ', 'import ', '@')):
                continue
            # Look for function definition
            if line.strip().startswith('def '):
                in_function = True
                continue
            # Collect function body
            if in_function:
                if line.strip():  # Non-empty line
                    if base_indent is None:
                        base_indent = len(line) - len(line.lstrip())
                    # Dedent to base level
                    if len(line) >= base_indent:
                        func_body_lines.append(line[base_indent:])
                    else:
                        func_body_lines.append(line.strip())
                else:
                    func_body_lines.append('')

        # If we found a function body, use it; otherwise use the whole code
        if func_body_lines:
            exec_code = '\n'.join(func_body_lines)
        else:
            exec_code = code

        # Convert sync Playwright calls to async by adding 'await'
        # Common patterns: .fill(), .click(), .wait_for(), .locator(), etc.
        async_code_lines = []
        for line in exec_code.split('\n'):
            modified_line = line
            # Add await before common Playwright async methods
            # Pattern: something.method() where method is async
            async_methods = [
                '.fill(', '.click(', '.wait_for(', '.type(', '.press(',
                '.check(', '.uncheck(', '.select_option(', '.hover(',
                '.focus(', '.blur(', '.scroll_into_view_if_needed(',
                '.screenshot(', '.inner_text(', '.inner_html(',
                '.text_content(', '.get_attribute(', '.is_visible(',
                '.is_enabled(', '.is_checked(', '.evaluate(',
            ]
            for method in async_methods:
                if method in modified_line and 'await ' not in modified_line:
                    # Find where to insert await (before the expression)
                    stripped = modified_line.lstrip()
                    indent = modified_line[:len(modified_line) - len(stripped)]
                    modified_line = indent + 'await ' + stripped
                    break
            async_code_lines.append(modified_line)

        async_exec_code = '\n'.join(async_code_lines)

        # Build parameter assignments
        param_assignments = '\n'.join(
            f'    {name} = __params__["{name}"]'
            for name in params.keys()
        )

        # Indent the code body
        indented_body = '\n'.join('    ' + line for line in async_exec_code.split('\n'))

        # Wrap in async function and execute
        wrapped_code = f'''
async def __custom_step__(page, __params__):
{param_assignments}
{indented_body}
'''

        # Create execution context
        exec_globals = {
            '__builtins__': __builtins__,
        }

        # Execute to define the function
        exec(wrapped_code, exec_globals)  # noqa: S102

        # Call and await the function
        await exec_globals['__custom_step__'](page, params)

    async def execute_scenario(
        self,
        scenario_id: str,
        scenario_name: str,
        content: str,
        base_url: str,
        custom_steps: Optional[dict[str, str]] = None,
        capture_screenshots: bool = True,
    ) -> ScenarioResult:
        """
        Execute a single Gherkin scenario.

        Args:
            scenario_id: Scenario ID
            scenario_name: Scenario name
            content: Gherkin content
            base_url: Base URL for the test
            custom_steps: Optional dict of pattern -> Python code for custom steps
            capture_screenshots: Whether to capture screenshots

        Returns:
            ScenarioResult with step results
        """
        result = ScenarioResult(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            status="passed",
            steps=[],
        )

        # Parse steps from content
        steps = await self._parse_gherkin_content(content)
        if not steps:
            result.status = "error"
            result.steps.append(StepResult(
                step_name="Parse scenario",
                status="error",
                error_message="No steps found in scenario",
            ))
            return result

        # Create a new page for this scenario
        page = await self._context.new_page()
        page._base_url = base_url

        try:
            for step in steps:
                step_result = await self._execute_step(
                    page,
                    step,
                    custom_steps,
                    capture_screenshots,
                )
                result.steps.append(step_result)

                # Stop on first failure
                if step_result.status in ("failed", "error"):
                    result.status = "failed"
                    # Mark remaining steps as skipped
                    remaining_idx = steps.index(step) + 1
                    for remaining_step in steps[remaining_idx:]:
                        result.steps.append(StepResult(
                            step_name=remaining_step["full"],
                            status="skipped",
                        ))
                    break

        finally:
            await page.close()

        return result

    async def _execute_step(
        self,
        page,
        step: dict,
        custom_steps: Optional[dict[str, str]],
        capture_screenshots: bool,
    ) -> StepResult:
        """Execute a single step."""
        step_text = step["text"]
        step_full = step["full"]
        start_time = time.time()

        try:
            # First, check custom steps
            if custom_steps:
                for pattern, code in custom_steps.items():
                    # Convert placeholder pattern {name} to regex capture group
                    regex_pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>.+)', pattern)
                    regex_pattern = re.sub(r'\{(\w+):d\}', r'(?P<\1>\\d+)', regex_pattern)

                    try:
                        regex = re.compile(regex_pattern, re.IGNORECASE)
                        match = regex.fullmatch(step_text)
                    except re.error:
                        continue

                    if match:
                        # Extract captured parameters
                        params = match.groupdict()

                        # Execute custom step code with proper context
                        await self._execute_custom_step_code(page, code, params)

                        duration_ms = int((time.time() - start_time) * 1000)

                        screenshot_data = None
                        if capture_screenshots:
                            screenshot_data = await page.screenshot(type="png")

                        return StepResult(
                            step_name=step_full,
                            status="passed",
                            duration_ms=duration_ms,
                            screenshot_data=screenshot_data,
                        )

            # Check built-in steps
            handler_result = self.step_registry.find_handler(step_text)
            if handler_result:
                handler, args = handler_result
                await handler(page, *args)

                duration_ms = int((time.time() - start_time) * 1000)

                screenshot_data = None
                if capture_screenshots:
                    screenshot_data = await page.screenshot(type="png")

                return StepResult(
                    step_name=step_full,
                    status="passed",
                    duration_ms=duration_ms,
                    screenshot_data=screenshot_data,
                )

            # No matching step definition
            return StepResult(
                step_name=step_full,
                status="error",
                error_message=f"No step definition found for: {step_text}",
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Step failed: {step_full} - {e}")

            # Try to capture failure screenshot
            screenshot_data = None
            if capture_screenshots:
                try:
                    screenshot_data = await page.screenshot(type="png")
                except Exception:
                    pass

            return StepResult(
                step_name=step_full,
                status="failed",
                duration_ms=duration_ms,
                error_message=str(e),
                screenshot_data=screenshot_data,
            )

    def register_custom_step(self, pattern: str, handler: Callable) -> None:
        """Register a custom step handler."""
        self.step_registry.register(pattern, handler)


async def run_test_execution(
    run_id: str,
    scenarios: list[dict],
    browser: str,
    base_url: str,
    locale: str = "en-GB",
    timezone_id: str = "Europe/London",
    custom_steps: Optional[dict[str, str]] = None,
    pages: Optional[dict[str, str]] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> TestExecutionResult:
    """
    Run test execution for a test run.

    Args:
        run_id: Test run ID
        scenarios: List of scenario dicts with 'id', 'name', 'content'
        browser: Browser name
        base_url: Base URL for tests
        custom_steps: Optional custom step definitions
        pages: Optional dict of page_name -> path for named page navigation
        progress_callback: Optional callback for progress updates

    Returns:
        TestExecutionResult with all scenario results
    """
    def report_progress(message: str):
        if progress_callback:
            progress_callback(message)

    result = TestExecutionResult(
        run_id=run_id,
        status="passed",
        scenarios=[],
    )

    start_time = time.time()
    executor = TestExecutor(browser=browser, pages=pages)

    try:
        report_progress(f"Connecting to {browser} browser...")
        await executor.connect()

        report_progress(f"Creating browser context for {base_url} (locale={locale})...")
        await executor.create_context(base_url, locale=locale, timezone_id=timezone_id)

        total_scenarios = len(scenarios)
        for idx, scenario in enumerate(scenarios, 1):
            report_progress(f"Running scenario {idx}/{total_scenarios}: {scenario['name']}")

            scenario_result = await executor.execute_scenario(
                scenario_id=str(scenario["id"]),
                scenario_name=scenario["name"],
                content=scenario["content"],
                base_url=base_url,
                custom_steps=custom_steps,
            )
            result.scenarios.append(scenario_result)

            # Update overall status
            if scenario_result.status != "passed":
                result.status = "failed"

        report_progress("Finalizing test results...")

    except Exception as e:
        logger.error(f"Test execution error: {e}")
        result.status = "error"
        report_progress(f"Error: {str(e)}")
    finally:
        report_progress("Closing browser...")
        await executor.disconnect()

    result.total_duration_ms = int((time.time() - start_time) * 1000)
    return result
