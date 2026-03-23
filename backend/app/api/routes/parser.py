"""Gherkin parser and step validation endpoints."""

import re
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import CustomStep, Project
from app.api.deps import get_api_key_or_user, verify_project_access

router = APIRouter()


# Built-in step patterns that are always available
BUILTIN_PATTERNS = [
    # Navigation - with quotes
    (r'I (?:am on|navigate to|go to|open|visit) the "([^"]+)" page', "Navigate to a named page"),
    (r'I (?:navigate to|go to|visit) "([^"]+)"', "Navigate to URL or page"),
    # Navigation - without quotes (for named pages like Home, Dashboard)
    (r'I (?:navigate to|go to|visit) (\w+)', "Navigate to named page"),
    (r'I am on (\w+)', "Assert on named page"),
    (r'I (?:navigate|go) to the (\w+) page', "Navigate to named page"),
    (r'I am on the (\w+) page', "Assert on named page"),
    # Other navigation
    (r'I (?:refresh|reload) the page', "Refresh the current page"),
    (r'I go back', "Navigate back in browser history"),
    (r'I go forward', "Navigate forward in browser history"),

    # Clicking
    (r'I click (?:on )?(?:the )?"([^"]+)"(?: button| link| element)?', "Click an element"),
    (r'I click (?:on )?(?:the )?([^"]+)(?: button| link)?', "Click an element by text"),
    (r'I double[- ]?click (?:on )?"([^"]+)"', "Double-click an element"),
    (r'I right[- ]?click (?:on )?"([^"]+)"', "Right-click an element"),

    # Form inputs
    (r'I (?:fill in|type|enter|input) "([^"]+)" (?:in(?:to)?|with) "([^"]+)"', "Fill a field with value"),
    (r'I (?:fill in|type|enter) "([^"]+)" (?:in(?:to)? )?(?:the )?"([^"]+)"(?: field)?', "Fill a field"),
    (r'I clear (?:the )?"([^"]+)"(?: field)?', "Clear a field"),
    (r'I select "([^"]+)" from "([^"]+)"', "Select option from dropdown"),
    (r'I check (?:the )?"([^"]+)"(?: checkbox)?', "Check a checkbox"),
    (r'I uncheck (?:the )?"([^"]+)"(?: checkbox)?', "Uncheck a checkbox"),
    (r'I upload "([^"]+)" to "([^"]+)"', "Upload file to input"),

    # Keyboard
    (r'I press (?:the )?(?:key )?"?(\w+)"?', "Press a keyboard key"),
    (r'I press Enter', "Press Enter key"),
    (r'I press Tab', "Press Tab key"),
    (r'I press Escape', "Press Escape key"),

    # Waiting
    (r'I wait (?:for )?(\d+) seconds?', "Wait for specified seconds"),
    (r'I wait (?:for )?"([^"]+)" to (?:be )?(?:visible|appear)', "Wait for element to appear"),
    (r'I wait (?:for )?"([^"]+)" to (?:be )?(?:hidden|disappear)', "Wait for element to disappear"),
    (r'I wait (?:for )?(?:the )?page to load', "Wait for page load"),

    # Assertions - visibility
    (r'I should see "([^"]+)"', "Assert text is visible"),
    (r'I should not see "([^"]+)"', "Assert text is not visible"),
    (r'(?:the )?"([^"]+)" should be visible', "Assert element is visible"),
    (r'(?:the )?"([^"]+)" should not be visible', "Assert element is not visible"),
    (r'(?:the )?"([^"]+)" should be hidden', "Assert element is hidden"),
    (r'"([^"]+)" is visible', "Assert CSS selector is visible"),
    (r'"([^"]+)" is (?:hidden|not visible)', "Assert CSS selector is hidden"),

    # Assertions - state
    (r'(?:the )?"([^"]+)" should be (?:enabled|clickable)', "Assert element is enabled"),
    (r'(?:the )?"([^"]+)" should (?:be disabled|not be (?:enabled|clickable))', "Assert element is disabled"),
    (r'(?:the )?"([^"]+)" should be checked', "Assert checkbox is checked"),
    (r'(?:the )?"([^"]+)" should not be checked', "Assert checkbox is not checked"),
    (r'(?:the )?"([^"]+)" should be selected', "Assert option is selected"),

    # Assertions - content
    (r'(?:the )?"([^"]+)" should (?:contain|have text) "([^"]+)"', "Assert element contains text"),
    (r'(?:the )?"([^"]+)" should (?:equal|be|have value) "([^"]+)"', "Assert element value"),
    (r'(?:the )?page title should (?:be|equal) "([^"]+)"', "Assert page title"),
    (r'(?:the )?(?:current )?(?:url|URL) should (?:contain|include) "([^"]+)"', "Assert URL contains"),
    (r'(?:the )?(?:current )?(?:url|URL) should (?:be|equal) "([^"]+)"', "Assert URL equals"),

    # Assertions - count
    (r'I should see (\d+) "([^"]+)" elements?', "Assert element count"),
    (r'(?:the )?(?:number|count) of "([^"]+)" should be (\d+)', "Assert element count"),

    # Authentication
    (r'I (?:am )?logged in as "([^"]+)"', "Login as user"),
    (r'I log ?(?:in|out)', "Login or logout"),
    (r'I am (?:not )?authenticated', "Authentication state"),

    # Screenshots
    (r'I take a screenshot', "Take a screenshot"),
    (r'I take a screenshot (?:named )?"([^"]+)"', "Take a named screenshot"),

    # Scrolling
    (r'I scroll (?:to )?(?:the )?"([^"]+)"', "Scroll to element"),
    (r'I scroll to (?:the )?(?:top|bottom) of (?:the )?page', "Scroll to top/bottom"),
    (r'I scroll down(?: (\d+) pixels)?', "Scroll down"),
    (r'I scroll up(?: (\d+) pixels)?', "Scroll up"),

    # Hover
    (r'I (?:hover|mouse) over "([^"]+)"', "Hover over element"),

    # Frames/Windows
    (r'I switch to (?:the )?"([^"]+)" (?:frame|iframe)', "Switch to frame"),
    (r'I switch to (?:the )?(?:main|default) (?:content|frame)', "Switch to main content"),
    (r'I switch to (?:the )?(?:new|popup) window', "Switch to new window"),
    (r'I close (?:the )?(?:current )?window', "Close window"),

    # Storage
    (r'I (?:set|store) "([^"]+)" (?:as|to|=) "([^"]+)"', "Store a variable"),
    (r'I clear (?:local )?storage', "Clear storage"),
    (r'I clear cookies', "Clear cookies"),

    # Alerts/Dialogs
    (r'I accept (?:the )?(?:alert|dialog|confirm)', "Accept alert/dialog"),
    (r'I dismiss (?:the )?(?:alert|dialog|confirm)', "Dismiss alert/dialog"),
    (r'(?:the )?(?:alert|dialog) should (?:say|contain) "([^"]+)"', "Assert alert text"),
]


class StepValidation(BaseModel):
    line_number: int
    keyword: str  # Given, When, Then, And, But
    text: str  # The step text after the keyword
    full_line: str  # The complete line
    is_matched: bool
    matched_pattern: Optional[str] = None
    match_source: Optional[str] = None  # "builtin" or "custom"
    custom_step_id: Optional[UUID] = None


class ParseRequest(BaseModel):
    content: str


class ParseResponse(BaseModel):
    valid: bool
    total_steps: int
    matched_steps: int
    unmatched_steps: int
    steps: list[StepValidation]
    errors: list[str] = []


def extract_steps(content: str) -> list[tuple[int, str, str, str]]:
    """Extract steps from Gherkin content.

    Returns list of (line_number, keyword, step_text, full_line)
    """
    steps = []
    lines = content.split('\n')

    step_pattern = re.compile(r'^\s*(Given|When|Then|And|But)\s+(.+)$', re.IGNORECASE)

    for i, line in enumerate(lines, 1):
        match = step_pattern.match(line)
        if match:
            keyword = match.group(1)
            text = match.group(2).strip()
            steps.append((i, keyword, text, line.strip()))

    return steps


def match_step(step_text: str, custom_steps: list[CustomStep]) -> tuple[bool, Optional[str], Optional[str], Optional[UUID]]:
    """Match a step against patterns.

    Returns (is_matched, matched_pattern, match_source, custom_step_id)
    """
    # First try custom steps (they take precedence)
    for custom in custom_steps:
        try:
            if re.match(custom.pattern, step_text, re.IGNORECASE):
                return True, custom.pattern, "custom", custom.id
        except re.error:
            # Invalid regex in custom step
            pass

    # Then try built-in patterns
    for pattern, description in BUILTIN_PATTERNS:
        try:
            if re.match(pattern, step_text, re.IGNORECASE):
                return True, description, "builtin", None
        except re.error:
            pass

    return False, None, None, None


@router.post("/parser/validate", response_model=ParseResponse)
async def validate_steps(
    request: ParseRequest,
    db: Session = Depends(get_db),
    auth=Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """Parse and validate Gherkin content.

    Extracts all steps and checks if they match known patterns
    (built-in or custom). Returns validation results for each step.
    """
    errors = []

    # Get custom steps for the project
    custom_steps = []
    if project:
        custom_steps = db.query(CustomStep).filter(
            CustomStep.project_id == project.id
        ).all()
    else:
        # If no project, get all custom steps (for backward compatibility)
        custom_steps = db.query(CustomStep).all()

    # Extract steps from content
    extracted = extract_steps(request.content)

    # Validate each step
    validations = []
    for line_num, keyword, text, full_line in extracted:
        is_matched, pattern, source, step_id = match_step(text, custom_steps)

        validations.append(StepValidation(
            line_number=line_num,
            keyword=keyword,
            text=text,
            full_line=full_line,
            is_matched=is_matched,
            matched_pattern=pattern,
            match_source=source,
            custom_step_id=step_id,
        ))

    matched = sum(1 for v in validations if v.is_matched)
    unmatched = len(validations) - matched

    return ParseResponse(
        valid=unmatched == 0,
        total_steps=len(validations),
        matched_steps=matched,
        unmatched_steps=unmatched,
        steps=validations,
        errors=errors,
    )


@router.get("/parser/patterns")
async def list_builtin_patterns(
    auth=Depends(get_api_key_or_user),
):
    """List all built-in step patterns.

    Returns the patterns that are available out of the box.
    """
    return [
        {"pattern": pattern, "description": description}
        for pattern, description in BUILTIN_PATTERNS
    ]
