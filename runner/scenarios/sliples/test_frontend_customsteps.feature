@phase6 @frontend @ui @customsteps
Feature: Custom Steps Editor - Create, Edit, Delete, and Manage Custom Step Definitions
  As a Sliples user
  I want to manage custom step definitions through the UI
  So that I can extend the testing vocabulary with reusable Python implementations

  # =============================================================================
  # Step List - Viewing and Searching Custom Steps
  # =============================================================================

  @steplist @display @critical
  Scenario: View list of custom steps
    Given I am logged in as "test.user@example.com"
    And custom steps exist in the system
    When I navigate to the custom steps page
    Then I should see "Custom Steps"
    And the "custom-steps-list" should be visible
    And I should see at least one custom step in the list

  @steplist @display @details
  Scenario: See step name, pattern, and description in list
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Login Step" exists
    And the step has pattern "I log in as {username}"
    And the step has description "Performs user login with given username"
    When I navigate to the custom steps page
    Then I should see "Login Step" in the custom steps list
    And I should see "I log in as {username}" in the custom steps list
    And I should see "Performs user login" in the custom steps list

  @steplist @empty
  Scenario: Empty state when no custom steps exist
    Given I am logged in as "test.user@example.com"
    And no custom steps exist in the system
    When I navigate to the custom steps page
    Then I should see "No custom steps yet"
    And I should see "Create your first custom step"
    And the "create-step-btn" should be visible

  @steplist @search @name
  Scenario: Search custom steps by name
    Given I am logged in as "test.user@example.com"
    And custom steps exist in the system
    And a custom step with name "Login Step" exists
    And a custom step with name "Logout Step" exists
    When I navigate to the custom steps page
    And I enter "Login" into the "step-search-input" field
    Then I should see "Login Step" in the custom steps list
    And I should not see "Logout Step" in the custom steps list

  @steplist @search @pattern
  Scenario: Search custom steps by pattern
    Given I am logged in as "test.user@example.com"
    And custom steps exist in the system
    And a custom step with pattern "I click the {button} button" exists
    And a custom step with pattern "I enter {text} into field" exists
    When I navigate to the custom steps page
    And I enter "click" into the "step-search-input" field
    Then I should see "I click the {button} button" in the custom steps list
    And I should not see "I enter {text} into field" in the custom steps list

  @steplist @filter @tag
  Scenario: Filter custom steps by tag/category
    Given I am logged in as "test.user@example.com"
    And a custom step with tag "authentication" exists
    And a custom step with tag "navigation" exists
    When I navigate to the custom steps page
    And I select "authentication" from the "step-tag-filter"
    Then I should only see steps with tag "authentication"
    And I should not see steps with tag "navigation"

  @steplist @filter @clear
  Scenario: Clear filter shows all custom steps
    Given I am logged in as "test.user@example.com"
    And custom steps exist in the system
    And I am on the custom steps page
    And I have filtered by tag "authentication"
    When I click the "Clear Filters" button
    Then I should see all custom steps in the list

  # =============================================================================
  # Create Step - Opening Editor and Entering Details
  # =============================================================================

  @createstep @editor @critical
  Scenario: Open create step editor
    Given I am logged in as "test.user@example.com"
    And I am on the custom steps page
    When I click the "Create Custom Step" button
    Then the "create-step-modal" should be visible
    And I should see "Create New Custom Step"
    And the "step-name-input" should be visible
    And the "step-pattern-input" should be visible
    And the "step-code-editor" should be visible

  @createstep @input @name
  Scenario: Enter step name in create editor
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter "My New Step" into the "step-name-input" field
    Then the "step-name-input" should have value "My New Step"

  @createstep @input @pattern
  Scenario: Enter step pattern with placeholder
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter "I click on the {element} button" into the "step-pattern-input" field
    Then the "step-pattern-input" should have value "I click on the {element} button"
    And the placeholder "{element}" should be highlighted in the pattern preview

  @createstep @input @code @critical
  Scenario: Write Python implementation in Monaco editor
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter the following code in the Monaco editor:
      """
      def step_impl(context, element):
          context.page.click(f'[data-testid="{element}"]')
      """
    Then the Monaco editor should contain "def step_impl"
    And the Monaco editor should contain "context.page.click"

  @createstep @preview
  Scenario: See pattern preview with placeholders
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered pattern "I log in as {username} with password {password}"
    When I wait for the preview to update
    Then the "pattern-preview" should be visible
    And the preview should show "{username}" as a parameter
    And the preview should show "{password}" as a parameter

  @createstep @description
  Scenario: Enter step description
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter "Authenticates user with credentials" into the "step-description-input" field
    Then the "step-description-input" should have value "Authenticates user with credentials"

  @createstep @tags
  Scenario: Add tags to custom step
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter "authentication" into the "step-tags-input" field
    And I press the "Enter" key
    Then I should see "authentication" tag badge in the tags list

  # =============================================================================
  # Create Step - Validation Errors
  # =============================================================================

  @createstep @validation @name @critical
  Scenario: Validation error for missing step name
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered a valid pattern "I do something"
    And I have entered valid Python code
    When I leave the "step-name-input" field empty
    And I click the "Create Step" button
    Then I should see "Step name is required"
    And the "create-step-modal" should still be visible

  @createstep @validation @pattern
  Scenario: Validation error for invalid pattern
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Test Step"
    When I enter "I click on {{invalid}" into the "step-pattern-input" field
    And I click the "Create Step" button
    Then I should see "Invalid pattern syntax"
    And the "step-pattern-input" should have error styling

  @createstep @validation @pattern @empty
  Scenario: Validation error for missing pattern
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Test Step"
    And I have entered valid Python code
    When I leave the "step-pattern-input" field empty
    And I click the "Create Step" button
    Then I should see "Step pattern is required"
    And the "create-step-modal" should still be visible

  @createstep @validation @code @syntax @critical
  Scenario: Validation error for syntax error in Python code
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Syntax Error Step"
    And I have entered pattern "I do something"
    When I enter the following code in the Monaco editor:
      """
      def step_impl(context):
          print("missing closing parenthesis"
      """
    And I click the "Create Step" button
    Then I should see "Python syntax error"
    And the Monaco editor should show error markers

  @createstep @validation @code @missing
  Scenario: Validation error for missing implementation code
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Empty Code Step"
    And I have entered pattern "I do something"
    When I clear the Monaco editor
    And I click the "Create Step" button
    Then I should see "Implementation code is required"
    And the "create-step-modal" should still be visible

  @createstep @validation @duplicate
  Scenario: Validation error for duplicate step pattern
    Given I am logged in as "test.user@example.com"
    And a custom step with pattern "I click the button" exists
    And the create step modal is open
    And I have entered step name "Duplicate Step"
    When I enter "I click the button" into the "step-pattern-input" field
    And I click the "Create Step" button
    Then I should see "A step with this pattern already exists"
    And the "create-step-modal" should still be visible

  # =============================================================================
  # Create Step - Successful Creation
  # =============================================================================

  @createstep @success @critical
  Scenario: Successfully create a custom step
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter "Click Element Step" into the "step-name-input" field
    And I enter "I click the {element} element" into the "step-pattern-input" field
    And I enter the following code in the Monaco editor:
      """
      def step_impl(context, element):
          context.page.click(f'[data-testid="{element}"]')
      """
    And I click the "Create Step" button
    Then I should see "Custom step created successfully"
    And the "create-step-modal" should not be visible
    And I should see "Click Element Step" in the custom steps list

  @createstep @cancel
  Scenario: Cancel create step discards changes
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Cancelled Step"
    And I have entered pattern "I do something cancelled"
    When I click the "Cancel" button
    Then the "create-step-modal" should not be visible
    And I should not see "Cancelled Step" in the custom steps list

  @createstep @cancel @confirm
  Scenario: Cancel with unsaved changes shows confirmation
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered step name "Unsaved Step"
    And I have entered pattern "I do something"
    And I have entered valid Python code
    When I click the modal close button
    Then the "discard-changes-modal" should be visible
    And I should see "Discard unsaved changes?"

  # =============================================================================
  # Edit Step - Opening and Modifying Steps
  # =============================================================================

  @editstep @open @critical
  Scenario: Open step for editing
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Editable Step" exists
    And I am on the custom steps page
    When I click the edit button for step "Editable Step"
    Then the "edit-step-modal" should be visible
    And I should see "Edit Custom Step"
    And the "step-name-input" should have value "Editable Step"

  @editstep @update @name
  Scenario: Update step name
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Old Step Name" exists
    And I am editing the step "Old Step Name"
    When I clear the "step-name-input" field
    And I enter "New Step Name" into the "step-name-input" field
    And I click the "Save Changes" button
    Then I should see "Custom step updated successfully"
    And I should see "New Step Name" in the custom steps list
    And I should not see "Old Step Name" in the custom steps list

  @editstep @update @pattern
  Scenario: Update step pattern
    Given I am logged in as "test.user@example.com"
    And a custom step with pattern "I click {button}" exists
    And I am editing the step with pattern "I click {button}"
    When I clear the "step-pattern-input" field
    And I enter "I press the {button} button" into the "step-pattern-input" field
    And I click the "Save Changes" button
    Then I should see "Custom step updated successfully"
    And I should see "I press the {button} button" in the custom steps list

  @editstep @update @code
  Scenario: Update step implementation code
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Code Update Step" exists
    And I am editing the step "Code Update Step"
    When I replace the code in the Monaco editor with:
      """
      def step_impl(context):
          context.page.wait_for_timeout(1000)
          print("Updated implementation")
      """
    And I click the "Save Changes" button
    Then I should see "Custom step updated successfully"

  @editstep @save @critical
  Scenario: Save changes successfully updates the step
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Save Test Step" exists
    And I am editing the step "Save Test Step"
    When I enter "Updated Description" into the "step-description-input" field
    And I click the "Save Changes" button
    Then I should see "Custom step updated successfully"
    And the "edit-step-modal" should not be visible

  @editstep @cancel
  Scenario: Cancel edit discards changes
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Cancel Edit Step" exists
    And I am editing the step "Cancel Edit Step"
    When I clear the "step-name-input" field
    And I enter "Should Not Save" into the "step-name-input" field
    And I click the "Cancel" button
    Then the "edit-step-modal" should not be visible
    And I should see "Cancel Edit Step" in the custom steps list
    And I should not see "Should Not Save" in the custom steps list

  @editstep @validation
  Scenario: Edit validation prevents invalid changes
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Valid Step" exists
    And I am editing the step "Valid Step"
    When I clear the "step-name-input" field
    And I click the "Save Changes" button
    Then I should see "Step name is required"
    And the "edit-step-modal" should still be visible

  # =============================================================================
  # Delete Step - Removing Custom Steps
  # =============================================================================

  @deletestep @confirm @critical
  Scenario: Delete step with confirmation dialog
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Delete Me Step" exists
    And I am on the custom steps page
    When I click the delete button for step "Delete Me Step"
    Then the "delete-step-modal" should be visible
    And I should see "Are you sure you want to delete this step?"
    And I should see "Delete Me Step"
    When I click the "Delete" button in the confirmation modal
    Then I should see "Custom step deleted successfully"
    And I should not see "Delete Me Step" in the custom steps list

  @deletestep @cancel
  Scenario: Cancel delete keeps the step
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Keep This Step" exists
    And I am on the custom steps page
    When I click the delete button for step "Keep This Step"
    Then the "delete-step-modal" should be visible
    When I click the "Cancel" button in the confirmation modal
    Then the "delete-step-modal" should not be visible
    And I should see "Keep This Step" in the custom steps list

  @deletestep @inuse
  Scenario: Cannot delete step that is in use
    Given I am logged in as "test.user@example.com"
    And a custom step with name "In Use Step" exists
    And the step "In Use Step" is used in 3 scenarios
    And I am on the custom steps page
    When I click the delete button for step "In Use Step"
    Then the "delete-step-modal" should be visible
    And I should see "This step is used in 3 scenarios"
    And the "confirm-delete-btn" should be disabled
    And I should see "Remove the step from all scenarios before deleting"

  @deletestep @removed
  Scenario: Deleted step is immediately removed from list
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Quick Delete" exists
    And I am on the custom steps page
    And I can see "Quick Delete" in the custom steps list
    When I delete the step "Quick Delete"
    Then the step "Quick Delete" should not be in the list
    And the custom steps count should decrease by 1

  # =============================================================================
  # Monaco Editor - Features and Functionality
  # =============================================================================

  @monaco @syntax @critical
  Scenario: Monaco editor shows Python syntax highlighting
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter the following code in the Monaco editor:
      """
      def step_impl(context):
          # This is a comment
          variable = "string value"
          context.page.click('.button')
      """
    Then the Monaco editor should highlight "def" as a keyword
    And the Monaco editor should highlight "# This is a comment" as a comment
    And the Monaco editor should highlight "string value" as a string

  @monaco @linenumbers
  Scenario: Monaco editor shows line numbers
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter multiple lines of code in the Monaco editor
    Then the Monaco editor should show line numbers
    And line number 1 should be visible
    And line number 5 should be visible

  @monaco @autoindent
  Scenario: Monaco editor auto-indents code
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I type "def step_impl(context):" in the Monaco editor
    And I press the "Enter" key
    Then the cursor should be indented by 4 spaces
    And I type "pass"
    Then the code should be properly indented

  @monaco @errors @critical
  Scenario: Monaco editor shows error markers for syntax errors
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I enter the following code in the Monaco editor:
      """
      def step_impl(context):
          if True
              print("missing colon")
      """
    Then the Monaco editor should show an error marker on line 2
    And the error tooltip should mention "expected ':'"

  @monaco @undoredo
  Scenario: Monaco editor supports undo/redo
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered code "def step_impl(context): pass" in the Monaco editor
    When I clear the Monaco editor
    And I press "Ctrl+Z" to undo
    Then the Monaco editor should contain "def step_impl(context): pass"
    When I press "Ctrl+Y" to redo
    Then the Monaco editor should be empty

  @monaco @findreplace
  Scenario: Monaco editor supports find and replace
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered code with multiple "context" occurrences
    When I press "Ctrl+F" to open find dialog
    Then the "monaco-find-dialog" should be visible
    When I enter "context" in the find field
    Then all occurrences of "context" should be highlighted
    When I click "Replace All" with "ctx"
    Then all occurrences should be replaced with "ctx"

  @monaco @autocomplete
  Scenario: Monaco editor shows Python autocomplete suggestions
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    When I type "def step_impl(context):" in the Monaco editor
    And I press "Enter" and type "context."
    And I trigger autocomplete with "Ctrl+Space"
    Then I should see autocomplete suggestions
    And I should see "page" in the suggestions

  @monaco @minimap
  Scenario: Monaco editor shows minimap for navigation
    Given I am logged in as "test.user@example.com"
    And the create step modal is open
    And I have entered more than 50 lines of code
    Then the "monaco-minimap" should be visible
    And I can click on the minimap to navigate

  # =============================================================================
  # Commit to Repository - Version Control Integration
  # =============================================================================

  @commit @offer
  Scenario: Offer to commit new step to repository
    Given I am logged in as "test.user@example.com"
    And I have just created a custom step
    Then I should see "Commit to repository?"
    And the "commit-step-btn" should be visible
    And the "skip-commit-btn" should be visible

  @commit @execute
  Scenario: Commit step to repository successfully
    Given I am logged in as "test.user@example.com"
    And I have just created a custom step named "Committed Step"
    When I click the "Commit to Repository" button
    Then I should see "Select repository"
    When I select repository "test-repo" from the dropdown
    And I enter "Add custom step: Committed Step" into the "commit-message-input" field
    And I click the "Commit" button
    Then I should see "Step committed successfully"

  @commit @skip
  Scenario: Skip committing step to repository
    Given I am logged in as "test.user@example.com"
    And I have just created a custom step
    When I click the "Skip" button
    Then the commit dialog should close
    And the step should remain as local only

  # =============================================================================
  # Step Usage and Documentation
  # =============================================================================

  @usage @display
  Scenario: View step usage in scenarios
    Given I am logged in as "test.user@example.com"
    And a custom step with name "Popular Step" exists
    And the step is used in 5 scenarios
    When I click on the step "Popular Step"
    Then the "step-details-panel" should be visible
    And I should see "Used in 5 scenarios"
    And I should see a list of scenarios using this step

  @usage @navigate
  Scenario: Navigate to scenario using the step
    Given I am logged in as "test.user@example.com"
    And a custom step is used in scenario "Login Test"
    And I am viewing the step details
    When I click on "Login Test" in the usage list
    Then I should be on the scenarios page
    And the URL should contain "/scenarios/"
