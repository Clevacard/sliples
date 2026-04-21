"""Playback executor for recording replay."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeout

from app.config import get_settings
from app.models import RecordedEvent, PlaybackStepResult, PlaybackStepStatus

logger = logging.getLogger(__name__)


class PlaybackExecutor:
    """Executes recorded events against a browser."""

    def __init__(self, browser: str = "chrome"):
        self.browser = browser
        self.settings = get_settings()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page: Optional[Page] = None

    def _get_browser_url(self) -> str:
        """Get the WebSocket URL for the selected browser."""
        if self.browser == "firefox":
            return self.settings.browser_firefox_url
        return self.settings.browser_chrome_url

    async def connect(self) -> None:
        """Connect to remote browser."""
        self._playwright = await async_playwright().start()
        browser_url = self._get_browser_url()
        logger.info(f"Connecting to browser at {browser_url}")

        if self.browser == "firefox":
            self._browser = await self._playwright.firefox.connect(browser_url)
        else:
            self._browser = await self._playwright.chromium.connect(browser_url)
        logger.info(f"Connected to {self.browser} browser")

    async def disconnect(self) -> None:
        """Disconnect from browser."""
        if self._page:
            await self._page.close()
            self._page = None
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
        viewport_width: int = 1280,
        viewport_height: int = 720,
        locale: str = "en-GB",
        timezone_id: str = "Europe/London",
    ) -> None:
        """Create a new browser context with specified viewport."""
        self._context = await self._browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            ignore_https_errors=True,
            locale=locale,
            timezone_id=timezone_id,
        )
        self._page = await self._context.new_page()

    async def take_screenshot(self) -> bytes:
        """Take a screenshot of current page."""
        return await self._page.screenshot(full_page=False)

    async def _find_element(self, event: RecordedEvent, timeout: int = 5000) -> Optional[Locator]:
        """Try to find element using multiple selector strategies."""
        selectors_to_try = []

        # Priority order: test_id > aria > text > css > xpath
        if event.selector_test_id:
            selectors_to_try.append((f'[data-testid="{event.selector_test_id}"]', 'test_id'))
        if event.selector_aria:
            selectors_to_try.append((f'[aria-label="{event.selector_aria}"]', 'aria'))
        if event.element_role and event.label_text:
            selectors_to_try.append((f'role={event.element_role}[name="{event.label_text}"]', 'role'))
        if event.label_text:
            selectors_to_try.append((f'text="{event.label_text}"', 'text'))
        if event.selector_css:
            selectors_to_try.append((event.selector_css, 'css'))
        if event.selector_xpath:
            selectors_to_try.append((f'xpath={event.selector_xpath}', 'xpath'))
        # Fallback: element ID
        if event.element_id:
            selectors_to_try.append((f'#{event.element_id}', 'id'))

        for selector, selector_type in selectors_to_try:
            try:
                locator = self._page.locator(selector).first
                # Check if element exists and is visible
                await locator.wait_for(state="visible", timeout=timeout)
                logger.debug(f"Found element using {selector_type}: {selector}")
                return locator
            except PlaywrightTimeout:
                continue
            except Exception as e:
                logger.debug(f"Selector {selector_type} failed: {e}")
                continue

        return None

    async def execute_event(
        self,
        event: RecordedEvent,
        take_screenshot: bool = False,
    ) -> tuple[PlaybackStepStatus, Optional[str], Optional[str], Optional[bytes]]:
        """
        Execute a single recorded event.

        Returns: (status, error_message, selector_used, screenshot_bytes)
        """
        start_time = datetime.utcnow()
        screenshot = None
        selector_used = None

        try:
            if event.event_type == "navigation":
                # Navigate to URL
                if event.url:
                    await self._page.goto(event.url, wait_until="domcontentloaded", timeout=30000)
                    logger.info(f"Navigated to {event.url}")
                    selector_used = event.url

            elif event.event_type == "click":
                locator = await self._find_element(event)
                if not locator:
                    raise Exception(f"Element not found for click: {event.selector_css or event.label_text or 'unknown'}")
                await locator.click()
                selector_used = str(locator)
                logger.info(f"Clicked element")

            elif event.event_type == "input":
                locator = await self._find_element(event)
                if not locator:
                    raise Exception(f"Element not found for input: {event.selector_css or event.label_text or 'unknown'}")
                # Clear existing value and type new one
                await locator.fill(event.value or "")
                selector_used = str(locator)
                logger.info(f"Filled input with value")

            elif event.event_type == "change":
                locator = await self._find_element(event)
                if not locator:
                    raise Exception(f"Element not found for change: {event.selector_css or event.label_text or 'unknown'}")
                # Handle select elements
                tag = await locator.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    await locator.select_option(event.value or "")
                else:
                    await locator.fill(event.value or "")
                selector_used = str(locator)
                logger.info(f"Changed element value")

            elif event.event_type == "submit":
                locator = await self._find_element(event)
                if locator:
                    # Try to submit the form
                    await locator.evaluate("el => el.form ? el.form.submit() : el.click()")
                    selector_used = str(locator)
                logger.info(f"Submitted form")

            elif event.event_type == "keydown":
                # Handle keyboard events
                key_info = event.key_info or {}
                key = key_info.get("key", "")
                if key:
                    await self._page.keyboard.press(key)
                    selector_used = f"key:{key}"
                logger.info(f"Pressed key: {key}")

            elif event.event_type == "scroll":
                # Handle scroll events
                extra_data = event.extra_data or {}
                scroll_x = extra_data.get("scrollX", 0)
                scroll_y = extra_data.get("scrollY", 0)
                await self._page.evaluate(f"window.scrollTo({scroll_x}, {scroll_y})")
                selector_used = f"scroll:{scroll_x},{scroll_y}"
                logger.info(f"Scrolled to {scroll_x}, {scroll_y}")

            else:
                logger.warning(f"Unknown event type: {event.event_type}")

            # Wait a bit for any animations/transitions
            await self._page.wait_for_timeout(200)

            # Take screenshot if requested
            if take_screenshot:
                screenshot = await self.take_screenshot()

            return PlaybackStepStatus.passed, None, selector_used, screenshot

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Event execution failed: {error_msg}")
            # Always take screenshot on failure
            try:
                screenshot = await self.take_screenshot()
            except Exception:
                pass
            return PlaybackStepStatus.failed, error_msg, selector_used, screenshot


async def run_playback(
    executor: PlaybackExecutor,
    events: list[RecordedEvent],
    start_url: str,
    viewport_width: int,
    viewport_height: int,
    locale: str = "en-GB",
    timezone_id: str = "Europe/London",
    on_step_complete: callable = None,
) -> list[dict]:
    """
    Execute a full playback run.

    Args:
        executor: PlaybackExecutor instance
        events: List of recorded events to replay
        start_url: URL to start playback
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
        locale: Browser locale
        timezone_id: Browser timezone
        on_step_complete: Callback for progress updates

    Returns:
        List of step results
    """
    results = []

    await executor.connect()
    try:
        await executor.create_context(
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            locale=locale,
            timezone_id=timezone_id,
        )

        # Navigate to start URL
        await executor._page.goto(start_url, wait_until="domcontentloaded", timeout=30000)

        for i, event in enumerate(events):
            start_time = datetime.utcnow()

            # Determine if we should take screenshot
            take_screenshot = event.should_screenshot

            status, error_msg, selector_used, screenshot = await executor.execute_event(
                event,
                take_screenshot=take_screenshot,
            )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            result = {
                "event_id": event.id,
                "sequence": event.sequence,
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_msg,
                "selector_used": selector_used,
                "screenshot": screenshot,
                "event": event,
            }
            results.append(result)

            if on_step_complete:
                on_step_complete(i + 1, len(events), status, error_msg, event)

            # If step failed, take screenshot and continue (don't abort)
            if status == PlaybackStepStatus.failed:
                logger.warning(f"Step {event.sequence} failed, continuing...")

    finally:
        await executor.disconnect()

    return results
