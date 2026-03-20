@phase6 @frontend @ui @editor
Feature: Scenario Editor - File Tree, Code Editor, and Gherkin Editing
  As a Sliples user
  I want to browse scenarios in a file tree and edit them in a Monaco-style editor
  So that I can view and modify Gherkin test scenarios efficiently

  # =============================================================================
  # File Tree - Repository and File Navigation
  # =============================================================================

  @filetree @display @critical
  Scenario: View file tree with repositories
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    When I wait for the page to load
    Then the "file-tree-panel" should be visible
    And I should see repository folders in the file tree
    And the "file-tree-header" should display "Scenarios"

  @filetree @expand @critical
  Scenario: Expand repository to see feature files
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And a repository "test-scenarios" exists with feature files
    When I click the expand icon for repository "test-scenarios"
    Then I should see the feature files under "test-scenarios"
    And each feature file should have a ".feature" extension indicator

  @filetree @expand
  Scenario: Expand feature file to see scenarios
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And a feature file "login.feature" exists with scenarios
    When I expand the feature file "login.feature"
    Then I should see the scenarios listed under "login.feature"
    And each scenario should display its name
    And scenarios should be indented under the feature

  @filetree @select @critical
  Scenario: Click file to load in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And a feature file "checkout.feature" exists
    When I click on "checkout.feature" in the file tree
    Then the file content should load in the editor
    And the "editor-panel" should display the file content
    And the editor tab should show "checkout.feature"

  @filetree @highlight
  Scenario: Current file highlighted in tree
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I look at the file tree
    Then the "login.feature" item should have class "selected"
    And the "login.feature" item should be highlighted
    And other files should not be highlighted

  @filetree @collapse
  Scenario: Collapse and expand folders in tree
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And repository "main-repo" is expanded
    When I click the collapse icon for "main-repo"
    Then the repository "main-repo" should be collapsed
    And the feature files under "main-repo" should be hidden
    When I click the expand icon for "main-repo"
    Then the repository "main-repo" should be expanded
    And the feature files under "main-repo" should be visible

  @filetree @search @critical
  Scenario: Search files in tree
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And multiple feature files exist
    When I enter "login" into the "file-tree-search" field
    Then only files matching "login" should be visible in the tree
    And I should see "login.feature" in the filtered results
    And files not matching "login" should be hidden

  @filetree @empty
  Scenario: Empty state for repo with no scenarios
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And a repository "empty-repo" exists with no feature files
    When I expand the repository "empty-repo"
    Then I should see "No scenarios in this repository"
    And the "empty-repo-message" should be visible

  @filetree @icons
  Scenario: File tree shows appropriate icons
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    When I view the file tree
    Then repository items should display folder icons
    And feature files should display document icons
    And scenario items should display test icons

  @filetree @refresh
  Scenario: Refresh file tree updates content
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    When I click the "Refresh" button in the file tree header
    Then the file tree should reload
    And I should see "File tree refreshed" notification
    And the file tree should display updated content

  # =============================================================================
  # Editor View - Display and Features
  # =============================================================================

  @editor @display @critical
  Scenario: View scenario content in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I look at the editor panel
    Then the "editor-panel" should be visible
    And the editor should display the file content
    And the content should include Gherkin keywords

  @editor @syntax @critical
  Scenario: See Gherkin syntax highlighting
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I look at the editor content
    Then Gherkin keywords should be syntax highlighted
    And "Feature" keyword should have distinct styling
    And "Scenario" keyword should have distinct styling
    And "Given", "When", "Then" keywords should have distinct styling

  @editor @linenumbers @critical
  Scenario: See line numbers in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I look at the editor panel
    Then line numbers should be visible
    And line numbers should start from 1
    And the "editor-line-numbers" should be visible

  @editor @minimap
  Scenario: See minimap in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a large feature file
    When I look at the editor panel
    Then the "editor-minimap" should be visible
    And the minimap should show a preview of the content
    And the minimap should highlight the current viewport

  @editor @readonly @critical
  Scenario: Read-only mode by default
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I try to type in the editor
    Then the editor should not accept input
    And the "readonly-indicator" should be visible
    And I should see "Read-only" status in the editor toolbar

  @editor @toggle
  Scenario: Toggle to edit mode
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    And the editor is in read-only mode
    When I click the "Edit" button
    Then the editor should switch to edit mode
    And the "edit-mode-indicator" should be visible
    And I should be able to type in the editor

  @editor @scroll
  Scenario: Scroll through large files
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a large feature file with 200 lines
    When I scroll down in the editor
    Then the editor should scroll smoothly
    And I should see content from lower in the file
    And line numbers should update as I scroll

  @editor @theme @critical
  Scenario: Editor theme matches app theme
    Given I am logged in as "editor.user@example.com"
    And the app theme is set to "dark"
    And I am on the "scenarios" page
    And I have opened a feature file
    When I look at the editor
    Then the editor should use dark theme colors
    And the editor background should be dark
    And the text should have appropriate contrast

  @editor @theme
  Scenario: Editor theme updates when app theme changes
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file
    And the app theme is set to "dark"
    When I change the app theme to "light"
    Then the editor should switch to light theme
    And the editor background should be light

  @editor @tabs
  Scenario: Multiple files open in tabs
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    When I open file "login.feature"
    And I open file "checkout.feature"
    Then I should see two tabs in the editor
    And both "login.feature" and "checkout.feature" should have tabs
    And clicking a tab should switch to that file

  # =============================================================================
  # Edit Mode - Making Changes
  # =============================================================================

  @editmode @enable @critical
  Scenario: Enable edit mode for a file
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature"
    When I click the "Edit" button
    Then the editor should be in edit mode
    And the cursor should be active in the editor
    And I should see "Editing" status in the toolbar

  @editmode @changes @critical
  Scenario: Make changes to content
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    When I add a new line with "And I click the submit button"
    Then the content should be updated with the new line
    And I should see my changes in the editor

  @editmode @dirty @critical
  Scenario: See unsaved indicator after changes
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    When I modify the content
    Then the file tab should show an unsaved indicator
    And the "unsaved-indicator" should be visible
    And I should see a dot or asterisk next to the filename

  @editmode @save @critical
  Scenario: Save changes to file
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    When I click the "Save" button
    Then the changes should be saved
    And I should see "Changes saved successfully"
    And the unsaved indicator should disappear

  @editmode @cancel
  Scenario: Cancel edit discards changes
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    When I click the "Cancel" button
    Then a confirmation dialog should appear
    When I confirm cancellation
    Then the changes should be discarded
    And the original content should be restored
    And the editor should return to read-only mode

  @editmode @undo @critical
  Scenario: Undo changes in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    And I have added text "new step"
    When I press Ctrl+Z or Cmd+Z
    Then the "new step" text should be removed
    And the previous state should be restored

  @editmode @redo
  Scenario: Redo changes in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    And I have added and then undone text
    When I press Ctrl+Shift+Z or Cmd+Shift+Z
    Then the undone change should be reapplied
    And the text should reappear

  @editmode @autoindent
  Scenario: Auto-indent on new lines
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    And the cursor is at the end of an indented line
    When I press Enter
    Then a new line should be created
    And the cursor should be indented to match the previous line

  @editmode @tab
  Scenario: Tab inserts spaces
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    When I press the Tab key
    Then spaces should be inserted at the cursor
    And the indentation should be consistent with project settings

  @editmode @selection
  Scenario: Select and replace text
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened the file "login.feature" in edit mode
    When I select text "old text"
    And I type "new text"
    Then the selected text should be replaced
    And I should see "new text" in place of "old text"

  # =============================================================================
  # Save Flow - Persistence and Commits
  # =============================================================================

  @save @update @critical
  Scenario: Save updates scenario in system
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    When I click the "Save" button
    Then the scenario should be updated in the database
    And the file tree should reflect the changes
    And other users should see the updated content

  @save @clear
  Scenario: Save clears dirty flag
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have unsaved changes in "login.feature"
    When I save the changes
    Then the dirty flag should be cleared
    And the unsaved indicator should be removed
    And the file tab should show clean state

  @save @warning @critical
  Scenario: Unsaved changes warning on navigate
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have unsaved changes in "login.feature"
    When I try to navigate to another page
    Then a warning dialog should appear
    And I should see "You have unsaved changes"
    And I should see options to "Save", "Discard", or "Cancel"

  @save @commit @critical
  Scenario: Commit message prompt on save
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    When I click the "Save & Commit" button
    Then the "commit-message-modal" should be visible
    And I should see "Enter commit message"
    When I enter "Updated login scenario steps"
    And I click "Commit"
    Then the changes should be committed to the repository
    And I should see "Changes committed successfully"

  @save @draft
  Scenario: Save to draft without commit
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    When I click the "Save Draft" button
    Then the changes should be saved locally
    And I should see "Draft saved"
    And the changes should NOT be committed to the repository
    And the draft indicator should appear on the file

  @save @error
  Scenario: Error handling on save failure
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have made changes to "login.feature"
    And the save operation will fail due to conflict
    When I click the "Save" button
    Then I should see an error message
    And I should see "Save failed: Conflict detected"
    And the "save-error-details" should be visible
    And my changes should be preserved in the editor

  # =============================================================================
  # Gherkin Syntax - Highlighting and Formatting
  # =============================================================================

  @syntax @feature @critical
  Scenario: Feature keyword highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file
    When I look at the "Feature:" line in the editor
    Then the "Feature" keyword should be highlighted
    And the "Feature" keyword should have a distinct color
    And the keyword should be styled as a top-level declaration

  @syntax @scenario @critical
  Scenario: Scenario keyword highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file
    When I look at a "Scenario:" line in the editor
    Then the "Scenario" keyword should be highlighted
    And the "Scenario" keyword should have distinct styling
    And "Scenario Outline" should also be highlighted

  @syntax @steps @critical
  Scenario: Given/When/Then keywords highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with steps
    When I look at the step lines
    Then "Given" keyword should be highlighted in step color
    And "When" keyword should be highlighted in step color
    And "Then" keyword should be highlighted in step color
    And "And" keyword should be highlighted in step color
    And "But" keyword should be highlighted in step color

  @syntax @tags @critical
  Scenario: Tags highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with tags
    When I look at lines starting with "@"
    Then tags should be highlighted distinctly
    And "@smoke" should have tag styling
    And "@critical" should have tag styling
    And multiple tags on one line should all be highlighted

  @syntax @comments
  Scenario: Comments highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with comments
    When I look at lines starting with "#"
    Then comments should be highlighted in comment style
    And comment text should be dimmed or italicized
    And the comment styling should span the entire line

  @syntax @datatable
  Scenario: Data tables formatted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with data tables
    When I look at a data table in the editor
    Then the table should be visually formatted
    And pipe characters should be highlighted
    And table headers should be distinguishable
    And table columns should be aligned

  @syntax @examples
  Scenario: Examples keyword highlighted in Scenario Outline
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with Scenario Outline
    When I look at the "Examples:" section
    Then the "Examples" keyword should be highlighted
    And the examples table should be formatted
    And placeholder variables should be distinctly styled

  @syntax @strings
  Scenario: String literals highlighted
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a feature file with quoted strings
    When I look at text in quotes
    Then strings in double quotes should be highlighted
    And strings in single quotes should be highlighted
    And the string styling should be consistent

  # =============================================================================
  # Keyboard Shortcuts
  # =============================================================================

  @keyboard @save
  Scenario: Ctrl+S saves the file
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have unsaved changes in edit mode
    When I press Ctrl+S or Cmd+S
    Then the file should be saved
    And I should see save confirmation

  @keyboard @find
  Scenario: Ctrl+F opens find dialog
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have a file open in the editor
    When I press Ctrl+F or Cmd+F
    Then the "find-dialog" should be visible
    And I should be able to search for text

  @keyboard @goto
  Scenario: Ctrl+G opens go to line dialog
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have a file open in the editor
    When I press Ctrl+G or Cmd+G
    Then the "goto-line-dialog" should be visible
    And I should be able to enter a line number

  # =============================================================================
  # Additional Editor Features
  # =============================================================================

  @editor @breadcrumb
  Scenario: Breadcrumb navigation shows file path
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened "test-repo/features/login.feature"
    When I look at the editor header
    Then the breadcrumb should show "test-repo > features > login.feature"
    And clicking breadcrumb parts should navigate to that folder

  @editor @wordwrap
  Scenario: Toggle word wrap in editor
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have opened a file with long lines
    When I click the "Word Wrap" toggle
    Then long lines should wrap to fit the editor width
    And I should not need to scroll horizontally

  @editor @fontsize
  Scenario: Adjust editor font size
    Given I am logged in as "editor.user@example.com"
    And I am on the "scenarios" page
    And I have a file open in the editor
    When I increase the font size setting
    Then the editor text should become larger
    And the change should be reflected immediately
