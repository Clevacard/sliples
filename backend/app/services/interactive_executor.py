"""Interactive test executor service for human testers."""

import asyncio
import base64
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from uuid import UUID

from app.config import get_settings
from app.services.test_executor import GherkinStepRegistry

logger = logging.getLogger(__name__)


@dataclass
class StepExecutionResult:
    """Result of executing a single interactive step."""

    step_name: str
    status: str  # passed, failed, skipped, error
    duration_ms: int = 0
    error_message: Optional[str] = None
    screenshot_base64: Optional[str] = None
    current_url: Optional[str] = None
    page_title: Optional[str] = None


@dataclass
class SessionState:
    """Current state of an interactive session."""

    session_id: str
    status: str
    current_step_index: int
    total_steps: int
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    last_screenshot: Optional[str] = None
    step_results: list = field(default_factory=list)
    logs: list = field(default_factory=list)


class InteractiveExecutor:
    """Manages interactive browser sessions for human testers."""

    _sessions: dict[str, "InteractiveSession"] = {}

    @classmethod
    async def create_session(
        cls,
        session_id: str,
        browser_type: str = "chromium",
        base_url: str = "",
        headless: bool = False,
    ) -> "InteractiveSession":
        """
        Create a new interactive session.

        Args:
            session_id: Unique session identifier
            browser_type: Browser to use ('chromium', 'firefox', 'webkit')
            base_url: Base URL for the test environment
            headless: Whether to run browser headless (False for interactive)

        Returns:
            InteractiveSession instance
        """
        session = InteractiveSession(
            session_id=session_id,
            browser_type=browser_type,
            base_url=base_url,
            headless=headless,
        )
        await session.start()
        cls._sessions[session_id] = session
        logger.info(f"Created interactive session {session_id}")
        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional["InteractiveSession"]:
        """Get an existing session by ID."""
        return cls._sessions.get(session_id)

    @classmethod
    async def end_session(cls, session_id: str) -> bool:
        """End and cleanup a session."""
        session = cls._sessions.pop(session_id, None)
        if session:
            await session.stop()
            logger.info(f"Ended interactive session {session_id}")
            return True
        return False

    @classmethod
    def list_active_sessions(cls) -> list[str]:
        """List all active session IDs."""
        return list(cls._sessions.keys())


class InteractiveSession:
    """An interactive browser session for step-by-step test execution."""

    def __init__(
        self,
        session_id: str,
        browser_type: str = "chromium",
        base_url: str = "",
        headless: bool = False,
    ):
        self.session_id = session_id
        self.browser_type = browser_type
        self.base_url = base_url
        self.headless = headless
        self.settings = get_settings()

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

        self.step_registry = GherkinStepRegistry()
        self.step_results: list[dict] = []
        self.logs: list[str] = []
        self.current_step_index = 0
        self.scenario_steps: list[dict] = []

        self._started_at = None
        self._status = "initializing"

    def _get_browser_url(self) -> str:
        """Get the WebSocket URL for the browser container."""
        if self.browser_type in ("chromium", "chrome"):
            return self.settings.browser_chrome_url
        elif self.browser_type == "firefox":
            return self.settings.browser_firefox_url
        else:
            # Default to Chrome for webkit or unknown types
            return self.settings.browser_chrome_url

    @property
    def status(self) -> str:
        return self._status

    def _log(self, message: str, level: str = "info"):
        """Add a log message."""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.logs.append(log_entry)
        if level == "error":
            logger.error(f"Session {self.session_id}: {message}")
        else:
            logger.info(f"Session {self.session_id}: {message}")

    async def start(self) -> None:
        """Start the browser session."""
        from playwright.async_api import async_playwright

        self._log("Starting browser session...")
        self._playwright = await async_playwright().start()

        # Connect to remote browser container
        browser_url = self._get_browser_url()
        self._log(f"Connecting to browser at {browser_url}...")

        try:
            self._browser = await self._playwright.chromium.connect(browser_url)
        except Exception as e:
            self._log(f"Failed to connect to remote browser: {e}", "error")
            # Fallback to local launch for development outside Docker
            self._log("Falling back to local browser launch...")
            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = await browser_launcher.launch(
                headless=self.headless,
                slow_mo=100,
            )

        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )

        self._page = await self._context.new_page()
        self._page._base_url = self.base_url

        self._started_at = datetime.utcnow()
        self._status = "active"
        self._log(f"Browser session started with {self.browser_type}")

        # Navigate to base URL if provided
        if self.base_url:
            await self._page.goto(self.base_url, wait_until="domcontentloaded")
            self._log(f"Navigated to base URL: {self.base_url}")

    async def stop(self) -> None:
        """Stop and cleanup the browser session."""
        self._log("Stopping browser session...")
        self._status = "terminated"

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

        self._log("Browser session stopped")

    async def load_scenario(self, content: str) -> list[dict]:
        """
        Load a Gherkin scenario and parse its steps.

        Args:
            content: Gherkin feature file content

        Returns:
            List of parsed steps
        """
        self.scenario_steps = await self._parse_gherkin_content(content)
        self.current_step_index = 0
        self.step_results = []
        self._log(f"Loaded scenario with {len(self.scenario_steps)} steps")
        return self.scenario_steps

    async def _parse_gherkin_content(self, content: str) -> list[dict]:
        """Parse Gherkin content and extract steps."""
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
                        "index": len(steps),
                        "keyword": keyword,
                        "text": text,
                        "full": line,
                        "status": "pending",
                    })
                    break

        return steps

    async def execute_step(
        self,
        step_index: Optional[int] = None,
        custom_steps: Optional[dict[str, str]] = None,
    ) -> StepExecutionResult:
        """
        Execute a single step.

        Args:
            step_index: Index of step to execute (defaults to current)
            custom_steps: Optional custom step definitions

        Returns:
            StepExecutionResult with execution details
        """
        if step_index is None:
            step_index = self.current_step_index

        if step_index >= len(self.scenario_steps):
            return StepExecutionResult(
                step_name="No more steps",
                status="completed",
                error_message="All steps have been executed",
            )

        step = self.scenario_steps[step_index]
        step_text = step["text"]
        step_full = step["full"]

        self._log(f"Executing step {step_index + 1}: {step_full}")
        start_time = time.time()

        try:
            # First, check custom steps
            if custom_steps:
                for pattern, code in custom_steps.items():
                    regex = re.compile(pattern, re.IGNORECASE)
                    match = regex.fullmatch(step_text)
                    if match:
                        # Execute custom step code
                        local_vars = {"page": self._page, "args": match.groups()}
                        exec(code, {"__builtins__": {}}, local_vars)  # noqa: S102
                        if "execute" in local_vars and callable(local_vars["execute"]):
                            await local_vars["execute"]()

                        return await self._create_step_result(
                            step_full, "passed", start_time
                        )

            # Check built-in steps
            handler_result = self.step_registry.find_handler(step_text)
            if handler_result:
                handler, args = handler_result
                await handler(self._page, *args)
                return await self._create_step_result(step_full, "passed", start_time)

            # No matching step definition
            self._log(f"No step definition found for: {step_text}", "error")
            return await self._create_step_result(
                step_full,
                "error",
                start_time,
                error_message=f"No step definition found for: {step_text}",
            )

        except Exception as e:
            self._log(f"Step failed: {str(e)}", "error")
            return await self._create_step_result(
                step_full, "failed", start_time, error_message=str(e)
            )

    async def _create_step_result(
        self,
        step_name: str,
        status: str,
        start_time: float,
        error_message: Optional[str] = None,
    ) -> StepExecutionResult:
        """Create a step result with screenshot and page info."""
        duration_ms = int((time.time() - start_time) * 1000)

        # Capture screenshot
        screenshot_base64 = None
        try:
            screenshot_bytes = await self._page.screenshot(type="png")
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            self._log(f"Failed to capture screenshot: {e}", "error")

        # Get current page info
        current_url = None
        page_title = None
        try:
            current_url = self._page.url
            page_title = await self._page.title()
        except Exception:
            pass

        result = StepExecutionResult(
            step_name=step_name,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            screenshot_base64=screenshot_base64,
            current_url=current_url,
            page_title=page_title,
        )

        # Update scenario step status
        if self.current_step_index < len(self.scenario_steps):
            self.scenario_steps[self.current_step_index]["status"] = status
            self.step_results.append({
                "step_index": self.current_step_index,
                "step_name": step_name,
                "status": status,
                "duration_ms": duration_ms,
                "error_message": error_message,
                "executed_at": datetime.utcnow().isoformat(),
            })

        # Move to next step if passed
        if status == "passed":
            self.current_step_index += 1

        self._log(f"Step completed with status: {status} in {duration_ms}ms")
        return result

    async def skip_step(self) -> StepExecutionResult:
        """Skip the current step."""
        if self.current_step_index >= len(self.scenario_steps):
            return StepExecutionResult(
                step_name="No more steps",
                status="completed",
                error_message="All steps have been executed",
            )

        step = self.scenario_steps[self.current_step_index]
        step_name = step["full"]

        self._log(f"Skipping step: {step_name}")
        step["status"] = "skipped"
        self.step_results.append({
            "step_index": self.current_step_index,
            "step_name": step_name,
            "status": "skipped",
            "duration_ms": 0,
            "error_message": None,
            "executed_at": datetime.utcnow().isoformat(),
        })

        self.current_step_index += 1

        # Capture screenshot
        screenshot_base64 = None
        try:
            screenshot_bytes = await self._page.screenshot(type="png")
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception:
            pass

        return StepExecutionResult(
            step_name=step_name,
            status="skipped",
            screenshot_base64=screenshot_base64,
            current_url=self._page.url if self._page else None,
            page_title=await self._page.title() if self._page else None,
        )

    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot and return as base64."""
        try:
            screenshot_bytes = await self._page.screenshot(type="png")
            return base64.b64encode(screenshot_bytes).decode("utf-8")
        except Exception as e:
            self._log(f"Failed to take screenshot: {e}", "error")
            return None

    async def get_state(self) -> SessionState:
        """Get the current session state."""
        current_url = None
        page_title = None
        screenshot = None

        if self._page:
            try:
                current_url = self._page.url
                page_title = await self._page.title()
                screenshot_bytes = await self._page.screenshot(type="png")
                screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
            except Exception:
                pass

        return SessionState(
            session_id=self.session_id,
            status=self._status,
            current_step_index=self.current_step_index,
            total_steps=len(self.scenario_steps),
            current_url=current_url,
            page_title=page_title,
            last_screenshot=screenshot,
            step_results=self.step_results,
            logs=self.logs[-100:],  # Last 100 log entries
        )

    async def navigate(self, url: str) -> StepExecutionResult:
        """Navigate to a URL manually."""
        start_time = time.time()
        self._log(f"Manual navigation to: {url}")

        try:
            # Handle relative URLs
            if not url.startswith(("http://", "https://")):
                url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

            await self._page.goto(url, wait_until="domcontentloaded")
            return await self._create_step_result(
                f"Navigate to {url}", "passed", start_time
            )
        except Exception as e:
            return await self._create_step_result(
                f"Navigate to {url}", "failed", start_time, error_message=str(e)
            )

    async def run_custom_action(self, action: str, selector: str = "", value: str = "") -> StepExecutionResult:
        """
        Run a custom browser action.

        Args:
            action: Action type ('click', 'fill', 'select', etc.)
            selector: CSS selector for the element
            value: Value for input actions

        Returns:
            StepExecutionResult
        """
        start_time = time.time()
        action_desc = f"{action} on '{selector}'" + (f" with '{value}'" if value else "")
        self._log(f"Running custom action: {action_desc}")

        try:
            if action == "click":
                await self._page.click(selector)
            elif action == "fill":
                await self._page.fill(selector, value)
            elif action == "select":
                await self._page.select_option(selector, value)
            elif action == "check":
                await self._page.check(selector)
            elif action == "uncheck":
                await self._page.uncheck(selector)
            elif action == "hover":
                await self._page.hover(selector)
            elif action == "press":
                await self._page.keyboard.press(value)
            elif action == "type":
                await self._page.keyboard.type(value)
            elif action == "wait":
                await asyncio.sleep(float(value) if value else 1)
            else:
                return await self._create_step_result(
                    action_desc, "error", start_time,
                    error_message=f"Unknown action: {action}"
                )

            return await self._create_step_result(action_desc, "passed", start_time)

        except Exception as e:
            return await self._create_step_result(
                action_desc, "failed", start_time, error_message=str(e)
            )

    def pause(self) -> None:
        """Pause the session."""
        self._status = "paused"
        self._log("Session paused")

    def resume(self) -> None:
        """Resume the session."""
        if self._status == "paused":
            self._status = "active"
            self._log("Session resumed")

    async def complete(self) -> None:
        """Mark session as completed."""
        self._status = "completed"
        self._log("Session completed")
