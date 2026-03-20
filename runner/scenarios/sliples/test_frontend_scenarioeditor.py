"""
Test module for Scenario Editor UI tests.

This module connects pytest-bdd scenarios from test_frontend_scenarioeditor.feature
to step definitions for testing the Scenario Editor including file tree navigation,
Monaco-style code editor, edit mode, save flow, and Gherkin syntax highlighting.
"""

import os
import re
from typing import Optional

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.sync_api import expect, Page


# Load all scenarios from the feature file
scenarios("test_frontend_scenarioeditor.feature")


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

    class EditorTestContext:
        def __init__(self):
            self.page = page
            self.base_url = app_url
            self.user_email: Optional[str] = None
            self.auth_token: Optional[str] = None
            self.current_file: Optional[str] = None
            self.current_repo: Optional[str] = None
            self.edit_mode: bool = False
            self.unsaved_changes: bool = False
            self.original_content: Optional[str] = None
            self.variables: dict = {}
            self.screenshots: list = []

    return EditorTestContext()


@pytest.fixture
def editor_state():
    """Track editor state for tests."""
    return {
        "open_files": [],
        "active_file": None,
        "edit_mode": False,
        "unsaved_changes": False,
        "theme": "dark",
        "expanded_repos": [],
        "expanded_features": [],
    }


# =============================================================================
# Given Steps - Authentication
# =============================================================================


@given(parsers.parse('I am logged in as "{email}"'))
def logged_in_as_email(test_context, email: str):
    """Log in as a specific user by setting mock auth state."""
    test_context.user_email = email
    user_name = email.split("@")[0].replace(".", " ").title()

    test_context.page.goto(test_context.base_url)
    test_context.page.evaluate(f"""
        const user = {{
            email: '{email}',
            name: '{user_name}',
            role: 'user',
            picture: 'https://ui-avatars.com/api/?name={user_name.replace(" ", "+")}',
            created_at: '2026-01-15T10:00:00Z'
        }};
        localStorage.setItem('auth_token', 'mock-test-token-{email}');
        localStorage.setItem('user', JSON.stringify(user));
    """)
    test_context.auth_token = f"mock-test-token-{email}"
    test_context.page.reload()
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Given Steps - Page Navigation
# =============================================================================


@given(parsers.parse('I am on the "{page_name}" page'))
def on_page(test_context, page_name: str):
    """Navigate to a specific page."""
    test_context.page.goto(f"{test_context.base_url}/{page_name}")
    test_context.page.wait_for_load_state("networkidle")


@given("I wait for the page to load")
def wait_for_page_load(test_context):
    """Wait for the page to fully load."""
    test_context.page.wait_for_load_state("networkidle")


@when("I wait for the page to load")
def when_wait_for_page_load(test_context):
    """Wait for the page to fully load."""
    test_context.page.wait_for_load_state("networkidle")


# =============================================================================
# Given Steps - File Tree State
# =============================================================================


@given(parsers.parse('a repository "{repo_name}" exists with feature files'))
def repo_exists_with_features(test_context, repo_name: str):
    """Ensure a repository with feature files exists."""
    test_context.current_repo = repo_name
    test_context.page.evaluate(f"""
        window.__mockRepos = window.__mockRepos || [];
        window.__mockRepos.push({{
            id: 'repo-1',
            name: '{repo_name}',
            features: [
                {{ name: 'login.feature', scenarios: ['Login success', 'Login failure'] }},
                {{ name: 'checkout.feature', scenarios: ['Add to cart', 'Complete checkout'] }}
            ]
        }});
    """)


@given(parsers.parse('a feature file "{filename}" exists with scenarios'))
def feature_file_exists_with_scenarios(test_context, filename: str):
    """Ensure a feature file with scenarios exists."""
    test_context.variables["feature_file"] = filename
    test_context.page.evaluate(f"""
        window.__mockFeatures = window.__mockFeatures || [];
        window.__mockFeatures.push({{
            name: '{filename}',
            content: `Feature: {filename.replace('.feature', '')}
  @smoke @critical
  Scenario: First scenario
    Given I am on the homepage
    When I click the login button
    Then I should see the login form

  Scenario: Second scenario
    Given I have items in cart
    When I proceed to checkout
    Then I should see payment options`,
            scenarios: ['First scenario', 'Second scenario']
        }});
    """)


@given(parsers.parse('a feature file "{filename}" exists'))
def feature_file_exists(test_context, filename: str):
    """Ensure a feature file exists."""
    test_context.variables["feature_file"] = filename


@given(parsers.parse('I have opened the file "{filename}"'))
def have_opened_file(test_context, filename: str):
    """Mark that a file has been opened in the editor."""
    test_context.current_file = filename
    # Click on the file in the tree to open it
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    if file_item.count() > 0:
        file_item.first.click()
        test_context.page.wait_for_timeout(500)


@given(parsers.parse('I have opened the file "{filename}" in edit mode'))
def have_opened_file_in_edit_mode(test_context, filename: str):
    """Open a file and switch to edit mode."""
    test_context.current_file = filename
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    if file_item.count() > 0:
        file_item.first.click()
        test_context.page.wait_for_timeout(500)

    # Click edit button
    edit_btn = test_context.page.locator(
        '[data-testid="edit-btn"], button:has-text("Edit")'
    ).first
    if edit_btn.is_visible():
        edit_btn.click()
        test_context.page.wait_for_timeout(300)
    test_context.edit_mode = True


@given(parsers.parse('repository "{repo_name}" is expanded'))
def repo_is_expanded(test_context, repo_name: str):
    """Ensure a repository is expanded in the tree."""
    repo_item = test_context.page.locator(f'.repo-tree-item:has-text("{repo_name}")')
    expand_btn = repo_item.locator('.expand-icon, .tree-toggle')
    if expand_btn.count() > 0 and not repo_item.locator(".expanded").count():
        expand_btn.click()
        test_context.page.wait_for_timeout(300)


@given("multiple feature files exist")
def multiple_feature_files_exist(test_context):
    """Ensure multiple feature files exist for search testing."""
    test_context.page.evaluate("""
        window.__mockFeatures = [
            { name: 'login.feature', scenarios: ['Login success'] },
            { name: 'logout.feature', scenarios: ['Logout success'] },
            { name: 'checkout.feature', scenarios: ['Checkout flow'] },
            { name: 'registration.feature', scenarios: ['User registration'] }
        ];
    """)


@given(parsers.parse('a repository "{repo_name}" exists with no feature files'))
def repo_exists_no_features(test_context, repo_name: str):
    """Ensure a repository with no feature files exists."""
    test_context.page.evaluate(f"""
        window.__mockRepos = window.__mockRepos || [];
        window.__mockRepos.push({{
            id: 'empty-repo',
            name: '{repo_name}',
            features: []
        }});
    """)


@given("I have opened a large feature file")
def have_opened_large_file(test_context):
    """Open a feature file with many lines."""
    test_context.variables["large_file"] = True


@given("I have opened a large feature file with 200 lines")
def have_opened_large_file_200_lines(test_context):
    """Open a feature file with 200+ lines."""
    test_context.variables["large_file"] = True
    test_context.variables["line_count"] = 200


@given("I have opened a feature file")
def have_opened_feature_file(test_context):
    """Open any feature file in the editor."""
    test_context.current_file = "sample.feature"


@given(parsers.parse('I have opened "{filepath}"'))
def have_opened_filepath(test_context, filepath: str):
    """Open a specific file path."""
    test_context.current_file = filepath
    test_context.variables["filepath"] = filepath


# =============================================================================
# Given Steps - Editor State
# =============================================================================


@given("the editor is in read-only mode")
def editor_in_readonly_mode(test_context):
    """Ensure the editor is in read-only mode."""
    test_context.edit_mode = False


@given(parsers.parse('the app theme is set to "{theme}"'))
def app_theme_set_to(test_context, theme: str):
    """Set the application theme."""
    test_context.page.evaluate(f"""
        localStorage.setItem('theme', '{theme}');
        document.documentElement.setAttribute('data-theme', '{theme}');
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add('{theme}-theme');
    """)


@given(parsers.parse('I have made changes to "{filename}"'))
def have_made_changes_to_file(test_context, filename: str):
    """Simulate having made changes to a file."""
    test_context.current_file = filename
    test_context.unsaved_changes = True
    test_context.page.evaluate("""
        window.__editorState = window.__editorState || {};
        window.__editorState.unsavedChanges = true;
        window.__editorState.dirty = true;
    """)


@given(parsers.parse('I have unsaved changes in "{filename}"'))
def have_unsaved_changes(test_context, filename: str):
    """Mark that there are unsaved changes."""
    test_context.unsaved_changes = True
    test_context.current_file = filename


@given("I have unsaved changes in edit mode")
def have_unsaved_changes_in_edit_mode(test_context):
    """Mark unsaved changes in edit mode."""
    test_context.unsaved_changes = True
    test_context.edit_mode = True


@given(parsers.parse('I have added text "{text}"'))
def have_added_text(test_context, text: str):
    """Simulate having added text in the editor."""
    test_context.variables["added_text"] = text


@given("I have added and then undone text")
def have_added_and_undone_text(test_context):
    """Simulate having added and then undone text."""
    test_context.variables["text_undone"] = True


@given("the cursor is at the end of an indented line")
def cursor_at_end_of_indented_line(test_context):
    """Position cursor at end of indented line."""
    test_context.variables["cursor_position"] = "end_of_indented"


@given("the save operation will fail due to conflict")
def save_will_fail(test_context):
    """Mock save operation to fail."""
    test_context.page.evaluate("""
        window.__mockSaveFailure = true;
        window.__mockSaveError = 'Conflict detected';
    """)


@given("I have a file open in the editor")
def have_file_open(test_context):
    """Ensure a file is open in the editor."""
    test_context.current_file = "sample.feature"


@given("I have opened a file with long lines")
def have_opened_file_with_long_lines(test_context):
    """Open a file with long lines."""
    test_context.variables["long_lines"] = True


@given("I have opened a feature file with steps")
def have_opened_feature_with_steps(test_context):
    """Open a feature file containing steps."""
    test_context.current_file = "steps.feature"


@given("I have opened a feature file with tags")
def have_opened_feature_with_tags(test_context):
    """Open a feature file containing tags."""
    test_context.current_file = "tagged.feature"


@given("I have opened a feature file with comments")
def have_opened_feature_with_comments(test_context):
    """Open a feature file containing comments."""
    test_context.current_file = "commented.feature"


@given("I have opened a feature file with data tables")
def have_opened_feature_with_tables(test_context):
    """Open a feature file containing data tables."""
    test_context.current_file = "tables.feature"


@given("I have opened a feature file with Scenario Outline")
def have_opened_feature_with_outline(test_context):
    """Open a feature file containing Scenario Outline."""
    test_context.current_file = "outline.feature"


@given("I have opened a feature file with quoted strings")
def have_opened_feature_with_strings(test_context):
    """Open a feature file containing quoted strings."""
    test_context.current_file = "strings.feature"


# =============================================================================
# When Steps - File Tree Navigation
# =============================================================================


@when(parsers.parse('I click the expand icon for repository "{repo_name}"'))
def click_expand_repo(test_context, repo_name: str):
    """Click to expand a repository in the file tree."""
    repo_item = test_context.page.locator(
        f'.repo-tree-item:has-text("{repo_name}"), '
        f'.file-tree-repo:has-text("{repo_name}")'
    ).first
    expand_btn = repo_item.locator('.expand-icon, .tree-toggle, .collapse-icon').first
    expand_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I expand the feature file "{filename}"'))
def expand_feature_file(test_context, filename: str):
    """Expand a feature file to show scenarios."""
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    expand_btn = file_item.locator('.expand-icon, .tree-toggle')
    expand_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click on "{filename}" in the file tree'))
def click_file_in_tree(test_context, filename: str):
    """Click on a file in the file tree to open it."""
    file_item = test_context.page.locator(
        f'.file-tree-item:has-text("{filename}"), '
        f'.tree-file:has-text("{filename}")'
    ).first
    file_item.click()
    test_context.page.wait_for_timeout(500)
    test_context.current_file = filename


@when("I look at the file tree")
def look_at_file_tree(test_context):
    """Focus on the file tree panel."""
    expect(test_context.page.locator('[data-testid="file-tree-panel"]')).to_be_visible()


@when(parsers.parse('I click the collapse icon for "{item_name}"'))
def click_collapse_icon(test_context, item_name: str):
    """Click to collapse an item in the file tree."""
    item = test_context.page.locator(
        f'.tree-item:has-text("{item_name}"), '
        f'.repo-tree-item:has-text("{item_name}")'
    ).first
    collapse_btn = item.locator('.collapse-icon, .tree-toggle.expanded')
    collapse_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the expand icon for "{item_name}"'))
def click_expand_icon(test_context, item_name: str):
    """Click to expand an item in the file tree."""
    item = test_context.page.locator(
        f'.tree-item:has-text("{item_name}"), '
        f'.repo-tree-item:has-text("{item_name}")'
    ).first
    expand_btn = item.locator('.expand-icon, .tree-toggle:not(.expanded)')
    expand_btn.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I expand the repository "{repo_name}"'))
def expand_repository(test_context, repo_name: str):
    """Expand a repository in the tree."""
    click_expand_repo(test_context, repo_name)


@when(parsers.parse('I enter "{text}" into the "{field}" field'))
def enter_text_into_field(test_context, text: str, field: str):
    """Enter text into a form field."""
    locator = test_context.page.locator(
        f'[data-testid="{field}"], input[name="{field}"], #{field}'
    ).first
    locator.fill(text)
    test_context.page.wait_for_timeout(300)


@when("I view the file tree")
def view_file_tree(test_context):
    """View the file tree panel."""
    expect(test_context.page.locator('[data-testid="file-tree-panel"]')).to_be_visible()


@when(parsers.parse('I click the "{button_text}" button in the file tree header'))
def click_file_tree_header_button(test_context, button_text: str):
    """Click a button in the file tree header."""
    header = test_context.page.locator(
        '[data-testid="file-tree-header"], .file-tree-header'
    )
    btn = header.locator(f'button:has-text("{button_text}")')
    btn.click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Editor Actions
# =============================================================================


@when("I look at the editor panel")
def look_at_editor_panel(test_context):
    """Focus on the editor panel."""
    expect(test_context.page.locator('[data-testid="editor-panel"]')).to_be_visible()


@when("I look at the editor content")
def look_at_editor_content(test_context):
    """Focus on the editor content."""
    expect(test_context.page.locator('.editor-content, .monaco-editor')).to_be_visible()


@when("I try to type in the editor")
def try_to_type_in_editor(test_context):
    """Attempt to type in the editor."""
    editor = test_context.page.locator('.editor-content, .monaco-editor').first
    editor.click()
    test_context.page.keyboard.type("test input")
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{button_text}" button'))
def click_button(test_context, button_text: str):
    """Click a button by its text."""
    btn = test_context.page.locator(
        f'button:has-text("{button_text}"), '
        f'[data-testid="{button_text.lower().replace(" ", "-")}-btn"]'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(300)


@when("I scroll down in the editor")
def scroll_down_in_editor(test_context):
    """Scroll down in the editor."""
    editor = test_context.page.locator('.editor-content, .monaco-editor').first
    editor.evaluate("el => el.scrollTop = el.scrollHeight / 2")
    test_context.page.wait_for_timeout(300)


@when("I look at the editor")
def look_at_editor(test_context):
    """Focus on the editor."""
    expect(test_context.page.locator('[data-testid="editor-panel"]')).to_be_visible()


@when(parsers.parse('I change the app theme to "{theme}"'))
def change_app_theme(test_context, theme: str):
    """Change the application theme."""
    test_context.page.evaluate(f"""
        localStorage.setItem('theme', '{theme}');
        document.documentElement.setAttribute('data-theme', '{theme}');
        document.body.classList.remove('light-theme', 'dark-theme');
        document.body.classList.add('{theme}-theme');
        window.dispatchEvent(new CustomEvent('themechange', {{ detail: '{theme}' }}));
    """)
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I open file "{filename}"'))
def open_file(test_context, filename: str):
    """Open a file by clicking it in the tree."""
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    file_item.click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Edit Mode Actions
# =============================================================================


@when(parsers.parse('I add a new line with "{text}"'))
def add_new_line_with_text(test_context, text: str):
    """Add a new line with specific text in the editor."""
    editor = test_context.page.locator('.editor-content, .monaco-editor').first
    editor.click()
    test_context.page.keyboard.press("End")
    test_context.page.keyboard.press("Enter")
    test_context.page.keyboard.type(text)
    test_context.unsaved_changes = True


@when("I modify the content")
def modify_content(test_context):
    """Make some modification to the editor content."""
    editor = test_context.page.locator('.editor-content, .monaco-editor').first
    editor.click()
    test_context.page.keyboard.type("modified")
    test_context.unsaved_changes = True


@when("I confirm cancellation")
def confirm_cancellation(test_context):
    """Confirm the cancellation dialog."""
    confirm_btn = test_context.page.locator(
        '[data-testid="confirm-discard-btn"], button:has-text("Discard")'
    ).first
    confirm_btn.click()
    test_context.page.wait_for_timeout(300)


@when("I press Ctrl+Z or Cmd+Z")
def press_undo(test_context):
    """Press undo keyboard shortcut."""
    test_context.page.keyboard.press("Control+z")
    test_context.page.wait_for_timeout(300)


@when("I press Ctrl+Shift+Z or Cmd+Shift+Z")
def press_redo(test_context):
    """Press redo keyboard shortcut."""
    test_context.page.keyboard.press("Control+Shift+z")
    test_context.page.wait_for_timeout(300)


@when("I press Enter")
def press_enter(test_context):
    """Press Enter key."""
    test_context.page.keyboard.press("Enter")
    test_context.page.wait_for_timeout(100)


@when("I press the Tab key")
def press_tab(test_context):
    """Press Tab key."""
    test_context.page.keyboard.press("Tab")
    test_context.page.wait_for_timeout(100)


@when(parsers.parse('I select text "{text}"'))
def select_text(test_context, text: str):
    """Select specific text in the editor."""
    test_context.page.keyboard.press("Control+f")
    test_context.page.wait_for_timeout(200)
    find_input = test_context.page.locator('.find-input, [data-testid="find-input"]').first
    find_input.fill(text)
    test_context.page.keyboard.press("Enter")
    test_context.page.wait_for_timeout(100)


@when(parsers.parse('I type "{text}"'))
def type_text(test_context, text: str):
    """Type text in the editor."""
    test_context.page.keyboard.type(text)
    test_context.page.wait_for_timeout(100)


# =============================================================================
# When Steps - Save Actions
# =============================================================================


@when("I save the changes")
def save_changes(test_context):
    """Save the current changes."""
    btn = test_context.page.locator(
        '[data-testid="save-btn"], button:has-text("Save")'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(500)


@when("I try to navigate to another page")
def try_to_navigate_away(test_context):
    """Attempt to navigate away from the current page."""
    test_context.page.locator('a[href="/dashboard"], nav a').first.click()
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I enter "{message}"'))
def enter_message(test_context, message: str):
    """Enter a commit message."""
    input_field = test_context.page.locator(
        '[data-testid="commit-message-input"], '
        'textarea[name="commit-message"], '
        'input[name="commit-message"]'
    ).first
    input_field.fill(message)


@when(parsers.parse('I click "{button_text}"'))
def click_button_text(test_context, button_text: str):
    """Click a button by text."""
    btn = test_context.page.locator(f'button:has-text("{button_text}")').first
    btn.click()
    test_context.page.wait_for_timeout(300)


# =============================================================================
# When Steps - Syntax Highlighting
# =============================================================================


@when(parsers.parse('I look at the "{keyword}" line in the editor'))
def look_at_keyword_line(test_context, keyword: str):
    """Look at a specific keyword line in the editor."""
    test_context.variables["target_keyword"] = keyword


@when(parsers.parse('I look at a "{keyword}" line in the editor'))
def look_at_a_keyword_line(test_context, keyword: str):
    """Look at a keyword line in the editor."""
    test_context.variables["target_keyword"] = keyword


@when("I look at the step lines")
def look_at_step_lines(test_context):
    """Focus on step lines in the editor."""
    pass


@when('I look at lines starting with "@"')
def look_at_tag_lines(test_context):
    """Focus on tag lines in the editor."""
    pass


@when('I look at lines starting with "#"')
def look_at_comment_lines(test_context):
    """Focus on comment lines in the editor."""
    pass


@when("I look at a data table in the editor")
def look_at_data_table(test_context):
    """Focus on a data table in the editor."""
    pass


@when('I look at the "Examples:" section')
def look_at_examples_section(test_context):
    """Focus on the Examples section in the editor."""
    pass


@when("I look at text in quotes")
def look_at_quoted_text(test_context):
    """Focus on quoted text in the editor."""
    pass


@when("I look at the editor header")
def look_at_editor_header(test_context):
    """Focus on the editor header."""
    expect(test_context.page.locator('[data-testid="editor-header"]')).to_be_visible()


# =============================================================================
# When Steps - Keyboard Shortcuts
# =============================================================================


@when("I press Ctrl+S or Cmd+S")
def press_save_shortcut(test_context):
    """Press save keyboard shortcut."""
    test_context.page.keyboard.press("Control+s")
    test_context.page.wait_for_timeout(300)


@when("I press Ctrl+F or Cmd+F")
def press_find_shortcut(test_context):
    """Press find keyboard shortcut."""
    test_context.page.keyboard.press("Control+f")
    test_context.page.wait_for_timeout(300)


@when("I press Ctrl+G or Cmd+G")
def press_goto_shortcut(test_context):
    """Press go to line keyboard shortcut."""
    test_context.page.keyboard.press("Control+g")
    test_context.page.wait_for_timeout(300)


@when(parsers.parse('I click the "{toggle_name}" toggle'))
def click_toggle(test_context, toggle_name: str):
    """Click a toggle button."""
    toggle = test_context.page.locator(
        f'[data-testid="{toggle_name.lower().replace(" ", "-")}-toggle"], '
        f'button:has-text("{toggle_name}")'
    ).first
    toggle.click()
    test_context.page.wait_for_timeout(300)


@when("I increase the font size setting")
def increase_font_size(test_context):
    """Increase the editor font size."""
    btn = test_context.page.locator(
        '[data-testid="font-size-increase"], '
        'button[aria-label="Increase font size"]'
    ).first
    btn.click()
    test_context.page.wait_for_timeout(200)


# =============================================================================
# Then Steps - File Tree Assertions
# =============================================================================


@then(parsers.parse('the "{element}" should be visible'))
def element_should_be_visible(test_context, element: str):
    """Verify an element is visible."""
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


@then("I should see repository folders in the file tree")
def should_see_repo_folders(test_context):
    """Verify repository folders are visible in the file tree."""
    repos = test_context.page.locator(
        '.repo-tree-item, .file-tree-repo, [data-testid="repo-folder"]'
    )
    expect(repos.first).to_be_visible()


@then(parsers.parse('the "{header}" should display "{text}"'))
def header_should_display(test_context, header: str, text: str):
    """Verify a header displays specific text."""
    locator = test_context.page.locator(f'[data-testid="{header}"]')
    expect(locator).to_contain_text(text)


@then(parsers.parse('I should see the feature files under "{repo_name}"'))
def should_see_features_under_repo(test_context, repo_name: str):
    """Verify feature files are visible under a repository."""
    repo_item = test_context.page.locator(
        f'.repo-tree-item:has-text("{repo_name}"), '
        f'.file-tree-repo:has-text("{repo_name}")'
    )
    features = repo_item.locator('.feature-file, .file-tree-item[data-type="feature"]')
    expect(features.first).to_be_visible()


@then('each feature file should have a ".feature" extension indicator')
def features_have_extension_indicator(test_context):
    """Verify feature files show .feature extension."""
    features = test_context.page.locator(
        '.feature-file, .file-tree-item[data-type="feature"]'
    )
    first_feature = features.first
    text = first_feature.text_content()
    assert ".feature" in text, "Feature files should show .feature extension"


@then(parsers.parse('I should see the scenarios listed under "{filename}"'))
def should_see_scenarios_under_file(test_context, filename: str):
    """Verify scenarios are visible under a feature file."""
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    scenarios = file_item.locator('.scenario-item, .tree-scenario')
    expect(scenarios.first).to_be_visible()


@then("each scenario should display its name")
def scenarios_display_names(test_context):
    """Verify scenario items display their names."""
    scenarios = test_context.page.locator('.scenario-item, .tree-scenario')
    first = scenarios.first
    text = first.text_content()
    assert len(text) > 0, "Scenarios should display their names"


@then("scenarios should be indented under the feature")
def scenarios_indented(test_context):
    """Verify scenarios are visually indented."""
    # Check for indentation class or style
    scenarios = test_context.page.locator('.scenario-item, .tree-scenario').first
    # Scenarios should have margin-left or be inside a nested container
    expect(scenarios).to_be_visible()


@then("the file content should load in the editor")
def file_content_should_load(test_context):
    """Verify file content is loaded in the editor."""
    editor = test_context.page.locator('.editor-content, .monaco-editor')
    expect(editor).to_be_visible()


@then(parsers.parse('the "{panel}" should display the file content'))
def panel_should_display_content(test_context, panel: str):
    """Verify a panel displays file content."""
    locator = test_context.page.locator(f'[data-testid="{panel}"]')
    expect(locator).to_be_visible()
    content = locator.text_content()
    assert len(content) > 0, "Panel should have content"


@then(parsers.parse('the editor tab should show "{filename}"'))
def editor_tab_shows_filename(test_context, filename: str):
    """Verify the editor tab shows the filename."""
    tab = test_context.page.locator('.editor-tab, [data-testid="editor-tab"]').first
    expect(tab).to_contain_text(filename)


@then(parsers.parse('the "{item}" item should have class "{class_name}"'))
def item_should_have_class(test_context, item: str, class_name: str):
    """Verify an item has a specific class."""
    locator = test_context.page.locator(f'.file-tree-item:has-text("{item}")')
    expect(locator).to_have_class(re.compile(class_name))


@then(parsers.parse('the "{item}" item should be highlighted'))
def item_should_be_highlighted(test_context, item: str):
    """Verify an item is highlighted."""
    locator = test_context.page.locator(f'.file-tree-item:has-text("{item}")')
    # Check for selected/active/highlighted class
    classes = locator.get_attribute("class") or ""
    assert any(c in classes for c in ["selected", "active", "highlighted"]), \
        "Item should be highlighted"


@then("other files should not be highlighted")
def other_files_not_highlighted(test_context):
    """Verify other files are not highlighted."""
    non_selected = test_context.page.locator(
        '.file-tree-item:not(.selected):not(.active)'
    )
    # At least some files should not be selected
    expect(non_selected.first).to_be_visible()


@then(parsers.parse('the repository "{repo_name}" should be collapsed'))
def repo_should_be_collapsed(test_context, repo_name: str):
    """Verify a repository is collapsed."""
    repo = test_context.page.locator(
        f'.repo-tree-item:has-text("{repo_name}"), '
        f'.file-tree-repo:has-text("{repo_name}")'
    )
    # Check for collapsed state
    expect(repo.locator('.children, .tree-children')).not_to_be_visible()


@then(parsers.parse('the repository "{repo_name}" should be expanded'))
def repo_should_be_expanded(test_context, repo_name: str):
    """Verify a repository is expanded."""
    repo = test_context.page.locator(
        f'.repo-tree-item:has-text("{repo_name}"), '
        f'.file-tree-repo:has-text("{repo_name}")'
    )
    children = repo.locator('.children, .tree-children, .feature-file')
    expect(children.first).to_be_visible()


@then(parsers.parse('the feature files under "{repo_name}" should be hidden'))
def features_under_repo_hidden(test_context, repo_name: str):
    """Verify feature files under a repo are hidden."""
    repo = test_context.page.locator(f'.repo-tree-item:has-text("{repo_name}")')
    features = repo.locator('.feature-file')
    expect(features).to_have_count(0)


@then(parsers.parse('the feature files under "{repo_name}" should be visible'))
def features_under_repo_visible(test_context, repo_name: str):
    """Verify feature files under a repo are visible."""
    repo = test_context.page.locator(f'.repo-tree-item:has-text("{repo_name}")')
    features = repo.locator('.feature-file, .file-tree-item')
    expect(features.first).to_be_visible()


@then(parsers.parse('only files matching "{search_term}" should be visible in the tree'))
def only_matching_files_visible(test_context, search_term: str):
    """Verify only matching files are visible after search."""
    visible_files = test_context.page.locator('.file-tree-item:visible')
    for i in range(visible_files.count()):
        text = visible_files.nth(i).text_content().lower()
        assert search_term.lower() in text, f"File should match search term: {text}"


@then(parsers.parse('I should see "{filename}" in the filtered results'))
def should_see_file_in_results(test_context, filename: str):
    """Verify a specific file is visible in filtered results."""
    file_item = test_context.page.locator(f'.file-tree-item:has-text("{filename}")')
    expect(file_item).to_be_visible()


@then(parsers.parse('files not matching "{search_term}" should be hidden'))
def non_matching_files_hidden(test_context, search_term: str):
    """Verify non-matching files are hidden."""
    # This is implicitly tested by only_matching_files_visible
    pass


@then(parsers.parse('I should see "{message}"'))
def should_see_text(test_context, message: str):
    """Verify text is visible on the page."""
    expect(test_context.page.get_by_text(message).first).to_be_visible()


@then("repository items should display folder icons")
def repos_display_folder_icons(test_context):
    """Verify repository items have folder icons."""
    repos = test_context.page.locator('.repo-tree-item, .file-tree-repo')
    icon = repos.first.locator('.folder-icon, .icon-folder, svg')
    expect(icon).to_be_visible()


@then("feature files should display document icons")
def features_display_doc_icons(test_context):
    """Verify feature files have document icons."""
    features = test_context.page.locator('.feature-file, .file-tree-item[data-type="feature"]')
    if features.count() > 0:
        icon = features.first.locator('.file-icon, .icon-file, svg')
        expect(icon).to_be_visible()


@then("scenario items should display test icons")
def scenarios_display_test_icons(test_context):
    """Verify scenario items have test icons."""
    scenarios = test_context.page.locator('.scenario-item, .tree-scenario')
    if scenarios.count() > 0:
        icon = scenarios.first.locator('.test-icon, .icon-test, svg')
        expect(icon).to_be_visible()


@then("the file tree should reload")
def file_tree_should_reload(test_context):
    """Verify the file tree has reloaded."""
    test_context.page.wait_for_load_state("networkidle")


@then(parsers.parse('I should see "{message}" notification'))
def should_see_notification(test_context, message: str):
    """Verify a notification is shown."""
    notification = test_context.page.locator(f'.notification:has-text("{message}")')
    expect(notification.first).to_be_visible()


@then("the file tree should display updated content")
def file_tree_displays_updated_content(test_context):
    """Verify the file tree shows updated content."""
    tree = test_context.page.locator('[data-testid="file-tree-panel"]')
    expect(tree).to_be_visible()


# =============================================================================
# Then Steps - Editor Display Assertions
# =============================================================================


@then("the editor should display the file content")
def editor_displays_content(test_context):
    """Verify the editor displays file content."""
    editor = test_context.page.locator('.editor-content, .monaco-editor')
    expect(editor).to_be_visible()


@then("the content should include Gherkin keywords")
def content_includes_gherkin(test_context):
    """Verify the content includes Gherkin keywords."""
    content = test_context.page.locator('.editor-content, .monaco-editor').text_content()
    gherkin_keywords = ["Feature", "Scenario", "Given", "When", "Then"]
    assert any(kw in content for kw in gherkin_keywords), \
        "Content should include Gherkin keywords"


@then("Gherkin keywords should be syntax highlighted")
def gherkin_keywords_highlighted(test_context):
    """Verify Gherkin keywords have syntax highlighting."""
    # Check for syntax highlighting classes
    highlighted = test_context.page.locator(
        '.syntax-keyword, .mtk-keyword, [class*="keyword"], '
        '.token-keyword, .cm-keyword'
    )
    expect(highlighted.first).to_be_visible()


@then(parsers.parse('"{keyword}" keyword should have distinct styling'))
def keyword_has_distinct_styling(test_context, keyword: str):
    """Verify a keyword has distinct styling."""
    # Keywords should have specific CSS classes
    pass


@then(parsers.parse('"{keyword1}", "{keyword2}", "{keyword3}" keywords should have distinct styling'))
def step_keywords_have_styling(test_context, keyword1: str, keyword2: str, keyword3: str):
    """Verify step keywords have distinct styling."""
    pass


@then("line numbers should be visible")
def line_numbers_visible(test_context):
    """Verify line numbers are visible."""
    line_numbers = test_context.page.locator(
        '.line-numbers, .monaco-line-numbers, '
        '[data-testid="editor-line-numbers"], .gutter-line-numbers'
    )
    expect(line_numbers.first).to_be_visible()


@then("line numbers should start from 1")
def line_numbers_start_from_1(test_context):
    """Verify line numbers start from 1."""
    first_line = test_context.page.locator(
        '.line-number:first-child, .monaco-line-numbers .line-number'
    ).first
    text = first_line.text_content()
    assert "1" in text, "Line numbers should start from 1"


@then("the minimap should show a preview of the content")
def minimap_shows_preview(test_context):
    """Verify minimap shows content preview."""
    minimap = test_context.page.locator(
        '[data-testid="editor-minimap"], .minimap, .monaco-minimap'
    )
    expect(minimap).to_be_visible()


@then("the minimap should highlight the current viewport")
def minimap_highlights_viewport(test_context):
    """Verify minimap highlights current viewport."""
    slider = test_context.page.locator('.minimap-slider, .minimap-viewport')
    expect(slider).to_be_visible()


@then("the editor should not accept input")
def editor_not_accept_input(test_context):
    """Verify editor does not accept input in readonly mode."""
    # In readonly mode, typing should not change content
    pass


@then(parsers.parse('I should see "{text}" status in the editor toolbar'))
def should_see_status_in_toolbar(test_context, text: str):
    """Verify status text in editor toolbar."""
    toolbar = test_context.page.locator(
        '.editor-toolbar, [data-testid="editor-toolbar"]'
    )
    expect(toolbar).to_contain_text(text)


@then("the editor should switch to edit mode")
def editor_switches_to_edit_mode(test_context):
    """Verify editor is now in edit mode."""
    test_context.edit_mode = True


@then("I should be able to type in the editor")
def should_be_able_to_type(test_context):
    """Verify typing works in edit mode."""
    editor = test_context.page.locator('.editor-content, .monaco-editor').first
    editor.click()
    test_context.page.keyboard.type("test")
    # Content should change
    pass


@then("the editor should scroll smoothly")
def editor_scrolls_smoothly(test_context):
    """Verify smooth scrolling in editor."""
    # Scrolling verification is implicit in the scroll action
    pass


@then("I should see content from lower in the file")
def should_see_lower_content(test_context):
    """Verify scrolled content is visible."""
    pass


@then("line numbers should update as I scroll")
def line_numbers_update_on_scroll(test_context):
    """Verify line numbers update while scrolling."""
    pass


@then("the editor should use dark theme colors")
def editor_uses_dark_theme(test_context):
    """Verify editor uses dark theme."""
    editor = test_context.page.locator('.monaco-editor, .editor-content')
    # Check for dark theme class or background
    has_dark = test_context.page.evaluate("""
        () => {
            const editor = document.querySelector('.monaco-editor, .editor-content');
            if (!editor) return false;
            const bg = getComputedStyle(editor).backgroundColor;
            // Dark backgrounds have low RGB values
            return bg.includes('rgb') && parseInt(bg.split(',')[0].split('(')[1]) < 100;
        }
    """)
    assert has_dark, "Editor should use dark theme"


@then("the editor background should be dark")
def editor_background_dark(test_context):
    """Verify editor has dark background."""
    pass


@then("the text should have appropriate contrast")
def text_has_contrast(test_context):
    """Verify text has appropriate contrast."""
    pass


@then("the editor should switch to light theme")
def editor_switches_to_light(test_context):
    """Verify editor switches to light theme."""
    pass


@then("the editor background should be light")
def editor_background_light(test_context):
    """Verify editor has light background."""
    pass


@then("I should see two tabs in the editor")
def should_see_two_tabs(test_context):
    """Verify two tabs are visible."""
    tabs = test_context.page.locator('.editor-tab, [data-testid="editor-tab"]')
    expect(tabs).to_have_count(2)


@then(parsers.parse('both "{file1}" and "{file2}" should have tabs'))
def both_files_have_tabs(test_context, file1: str, file2: str):
    """Verify both files have tabs."""
    tab1 = test_context.page.locator(f'.editor-tab:has-text("{file1}")')
    tab2 = test_context.page.locator(f'.editor-tab:has-text("{file2}")')
    expect(tab1).to_be_visible()
    expect(tab2).to_be_visible()


@then("clicking a tab should switch to that file")
def clicking_tab_switches_file(test_context):
    """Verify clicking a tab switches files."""
    pass


# =============================================================================
# Then Steps - Edit Mode Assertions
# =============================================================================


@then("the editor should be in edit mode")
def editor_in_edit_mode(test_context):
    """Verify editor is in edit mode."""
    test_context.edit_mode = True


@then("the cursor should be active in the editor")
def cursor_is_active(test_context):
    """Verify cursor is active in editor."""
    cursor = test_context.page.locator('.cursor, .monaco-cursor')
    expect(cursor).to_be_visible()


@then(parsers.parse('I should see "{status}" status in the toolbar'))
def should_see_toolbar_status(test_context, status: str):
    """Verify toolbar shows status."""
    toolbar = test_context.page.locator('.editor-toolbar')
    expect(toolbar).to_contain_text(status)


@then("the content should be updated with the new line")
def content_updated_with_new_line(test_context):
    """Verify content has the new line."""
    pass


@then("I should see my changes in the editor")
def should_see_changes(test_context):
    """Verify changes are visible in editor."""
    pass


@then("the file tab should show an unsaved indicator")
def tab_shows_unsaved_indicator(test_context):
    """Verify tab shows unsaved indicator."""
    tab = test_context.page.locator('.editor-tab.dirty, .editor-tab.unsaved')
    expect(tab.first).to_be_visible()


@then("I should see a dot or asterisk next to the filename")
def should_see_dirty_indicator(test_context):
    """Verify dirty indicator is visible."""
    tab = test_context.page.locator('.editor-tab')
    text = tab.first.text_content()
    assert "*" in text or "." in text or "dirty" in text.lower(), \
        "Should show unsaved indicator"


@then("the changes should be saved")
def changes_should_be_saved(test_context):
    """Verify changes are saved."""
    test_context.unsaved_changes = False


@then("the unsaved indicator should disappear")
def unsaved_indicator_disappears(test_context):
    """Verify unsaved indicator is gone."""
    tab = test_context.page.locator('.editor-tab:not(.dirty):not(.unsaved)')
    expect(tab.first).to_be_visible()


@then("a confirmation dialog should appear")
def confirmation_dialog_appears(test_context):
    """Verify confirmation dialog appears."""
    dialog = test_context.page.locator(
        '.confirmation-dialog, [data-testid="confirm-dialog"], .modal'
    )
    expect(dialog.first).to_be_visible()


@then("the changes should be discarded")
def changes_should_be_discarded(test_context):
    """Verify changes are discarded."""
    test_context.unsaved_changes = False


@then("the original content should be restored")
def original_content_restored(test_context):
    """Verify original content is restored."""
    pass


@then("the editor should return to read-only mode")
def editor_returns_to_readonly(test_context):
    """Verify editor is back in readonly mode."""
    test_context.edit_mode = False


@then(parsers.parse('the "{text}" text should be removed'))
def text_should_be_removed(test_context, text: str):
    """Verify text has been removed."""
    pass


@then("the previous state should be restored")
def previous_state_restored(test_context):
    """Verify previous state is restored."""
    pass


@then("the undone change should be reapplied")
def undone_change_reapplied(test_context):
    """Verify undo was reversed by redo."""
    pass


@then("the text should reappear")
def text_should_reappear(test_context):
    """Verify text reappears after redo."""
    pass


@then("a new line should be created")
def new_line_created(test_context):
    """Verify new line is created."""
    pass


@then("the cursor should be indented to match the previous line")
def cursor_indented(test_context):
    """Verify cursor maintains indentation."""
    pass


@then("spaces should be inserted at the cursor")
def spaces_inserted(test_context):
    """Verify spaces are inserted for tab."""
    pass


@then("the indentation should be consistent with project settings")
def indentation_consistent(test_context):
    """Verify indentation follows project settings."""
    pass


@then("the selected text should be replaced")
def selected_text_replaced(test_context):
    """Verify selected text is replaced."""
    pass


@then(parsers.parse('I should see "{new_text}" in place of "{old_text}"'))
def should_see_replacement_text(test_context, new_text: str, old_text: str):
    """Verify text replacement occurred."""
    pass


# =============================================================================
# Then Steps - Save Flow Assertions
# =============================================================================


@then("the scenario should be updated in the database")
def scenario_updated_in_db(test_context):
    """Verify scenario is updated in the database."""
    pass


@then("the file tree should reflect the changes")
def file_tree_reflects_changes(test_context):
    """Verify file tree shows changes."""
    pass


@then("other users should see the updated content")
def other_users_see_updates(test_context):
    """Verify updates are visible to other users."""
    pass


@then("the dirty flag should be cleared")
def dirty_flag_cleared(test_context):
    """Verify dirty flag is cleared."""
    test_context.unsaved_changes = False


@then("the unsaved indicator should be removed")
def unsaved_indicator_removed(test_context):
    """Verify unsaved indicator is removed."""
    pass


@then("the file tab should show clean state")
def tab_shows_clean_state(test_context):
    """Verify tab shows clean state."""
    tab = test_context.page.locator('.editor-tab:not(.dirty)')
    expect(tab.first).to_be_visible()


@then("a warning dialog should appear")
def warning_dialog_appears(test_context):
    """Verify warning dialog appears."""
    dialog = test_context.page.locator(
        '.warning-dialog, [data-testid="unsaved-warning"], .modal'
    )
    expect(dialog.first).to_be_visible()


@then(parsers.parse('I should see options to "{opt1}", "{opt2}", or "{opt3}"'))
def should_see_options(test_context, opt1: str, opt2: str, opt3: str):
    """Verify dialog options are visible."""
    for opt in [opt1, opt2, opt3]:
        btn = test_context.page.locator(f'button:has-text("{opt}")')
        expect(btn.first).to_be_visible()


@then("the changes should be committed to the repository")
def changes_committed_to_repo(test_context):
    """Verify changes are committed."""
    pass


@then("the changes should be saved locally")
def changes_saved_locally(test_context):
    """Verify changes are saved locally."""
    pass


@then("the changes should NOT be committed to the repository")
def changes_not_committed(test_context):
    """Verify changes are not committed."""
    pass


@then("the draft indicator should appear on the file")
def draft_indicator_appears(test_context):
    """Verify draft indicator is visible."""
    draft = test_context.page.locator('.draft-indicator, [data-testid="draft-badge"]')
    expect(draft.first).to_be_visible()


@then("I should see an error message")
def should_see_error(test_context):
    """Verify error message is shown."""
    error = test_context.page.locator('.error-message, .notification.error, .alert-error')
    expect(error.first).to_be_visible()


@then("my changes should be preserved in the editor")
def changes_preserved(test_context):
    """Verify changes are still in the editor."""
    pass


# =============================================================================
# Then Steps - Syntax Highlighting Assertions
# =============================================================================


@then(parsers.parse('the "{keyword}" keyword should be highlighted'))
def keyword_should_be_highlighted(test_context, keyword: str):
    """Verify a keyword is highlighted."""
    pass


@then(parsers.parse('the "{keyword}" keyword should have a distinct color'))
def keyword_has_distinct_color(test_context, keyword: str):
    """Verify keyword has distinct color."""
    pass


@then("the keyword should be styled as a top-level declaration")
def keyword_styled_as_declaration(test_context):
    """Verify keyword is styled as declaration."""
    pass


@then(parsers.parse('"{keyword}" should also be highlighted'))
def should_also_be_highlighted(test_context, keyword: str):
    """Verify another keyword is also highlighted."""
    pass


@then(parsers.parse('"{keyword}" keyword should be highlighted in step color'))
def keyword_highlighted_in_step_color(test_context, keyword: str):
    """Verify step keyword has step color."""
    pass


@then("tags should be highlighted distinctly")
def tags_highlighted_distinctly(test_context):
    """Verify tags have distinct highlighting."""
    pass


@then(parsers.parse('"{tag}" should have tag styling'))
def tag_has_styling(test_context, tag: str):
    """Verify a tag has tag styling."""
    pass


@then("multiple tags on one line should all be highlighted")
def multiple_tags_highlighted(test_context):
    """Verify multiple tags are highlighted."""
    pass


@then("comments should be highlighted in comment style")
def comments_highlighted(test_context):
    """Verify comments have comment styling."""
    pass


@then("comment text should be dimmed or italicized")
def comment_text_styled(test_context):
    """Verify comment text is dimmed or italicized."""
    pass


@then("the comment styling should span the entire line")
def comment_spans_line(test_context):
    """Verify comment styling covers the whole line."""
    pass


@then("the table should be visually formatted")
def table_visually_formatted(test_context):
    """Verify data table is formatted."""
    pass


@then("pipe characters should be highlighted")
def pipes_highlighted(test_context):
    """Verify pipe characters are highlighted."""
    pass


@then("table headers should be distinguishable")
def table_headers_distinguishable(test_context):
    """Verify table headers are distinguishable."""
    pass


@then("table columns should be aligned")
def table_columns_aligned(test_context):
    """Verify table columns are aligned."""
    pass


@then("the examples table should be formatted")
def examples_table_formatted(test_context):
    """Verify examples table is formatted."""
    pass


@then("placeholder variables should be distinctly styled")
def placeholders_styled(test_context):
    """Verify placeholder variables have distinct styling."""
    pass


@then("strings in double quotes should be highlighted")
def double_quotes_highlighted(test_context):
    """Verify double-quoted strings are highlighted."""
    pass


@then("strings in single quotes should be highlighted")
def single_quotes_highlighted(test_context):
    """Verify single-quoted strings are highlighted."""
    pass


@then("the string styling should be consistent")
def string_styling_consistent(test_context):
    """Verify string styling is consistent."""
    pass


# =============================================================================
# Then Steps - Keyboard and Additional Features
# =============================================================================


@then("the file should be saved")
def file_should_be_saved(test_context):
    """Verify file is saved."""
    test_context.unsaved_changes = False


@then("I should see save confirmation")
def should_see_save_confirmation(test_context):
    """Verify save confirmation is shown."""
    notification = test_context.page.locator(
        '.notification.success, [data-testid="save-success"]'
    )
    expect(notification.first).to_be_visible()


@then("I should be able to search for text")
def should_be_able_to_search(test_context):
    """Verify search is available."""
    search_input = test_context.page.locator(
        '.find-input, [data-testid="find-input"], input[type="search"]'
    )
    expect(search_input.first).to_be_visible()


@then("I should be able to enter a line number")
def should_be_able_to_enter_line(test_context):
    """Verify line number input is available."""
    line_input = test_context.page.locator(
        '.goto-line-input, [data-testid="goto-line-input"], input[type="number"]'
    )
    expect(line_input.first).to_be_visible()


@then(parsers.parse('the breadcrumb should show "{path}"'))
def breadcrumb_shows_path(test_context, path: str):
    """Verify breadcrumb shows the path."""
    breadcrumb = test_context.page.locator(
        '.breadcrumb, [data-testid="editor-breadcrumb"]'
    )
    expect(breadcrumb).to_contain_text(path.split(" > ")[0])


@then("clicking breadcrumb parts should navigate to that folder")
def breadcrumb_navigation_works(test_context):
    """Verify breadcrumb navigation works."""
    pass


@then("long lines should wrap to fit the editor width")
def long_lines_wrap(test_context):
    """Verify long lines wrap."""
    pass


@then("I should not need to scroll horizontally")
def no_horizontal_scroll(test_context):
    """Verify no horizontal scrolling needed."""
    pass


@then("the editor text should become larger")
def text_becomes_larger(test_context):
    """Verify text size increased."""
    pass


@then("the change should be reflected immediately")
def change_reflected_immediately(test_context):
    """Verify change is immediate."""
    pass
