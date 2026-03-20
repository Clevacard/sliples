@phase5 @frontend @ui @environments
Feature: Environments Management UI
  As a Sliples user
  I want to manage test environments through the UI
  So that I can configure different target systems for running tests

  # =============================================================================
  # Environment List - Display
  # =============================================================================

  @environments @list @critical
  Scenario: View list of environments
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And at least one environment exists
    When I wait for the page to load
    Then the "environments-list" should be visible
    And I should see the environment name
    And I should see the environment URL

  @environments @list
  Scenario: See environment name, URL, and variable count
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with 5 variables exists
    When I wait for the page to load
    Then I should see the environment name
    And I should see the environment base URL
    And I should see "5 variables" for the environment

  @environments @list @empty
  Scenario: Empty state when no environments exist
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And no environments exist
    When I wait for the page to load
    Then I should see "No environments configured"
    And I should see "Create Environment"
    And the "create-environment-btn" should be visible

  @environments @list @navigation
  Scenario: Navigate to environment details
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "staging-env" exists
    When I click on the environment "staging-env"
    Then I should be on the environment details page
    And the URL should contain "/environments/"
    And I should see "staging-env"

  @environments @list @sort
  Scenario: Sort environments by name ascending
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And multiple environments exist
    When I click the sort button for "name"
    Then the environments should be sorted by name ascending

  @environments @list @sort
  Scenario: Sort environments by name descending
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And multiple environments exist
    When I click the sort button for "name" twice
    Then the environments should be sorted by name descending

  @environments @list @search
  Scenario: Search environments by name
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And environments "production", "staging", "development" exist
    When I enter "stag" into the search field
    Then I should see "staging" in the environments list
    And I should not see "production" in the environments list
    And I should not see "development" in the environments list

  @environments @list @filter
  Scenario: Filter environments clears with empty search
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And environments "production", "staging" exist
    And I have filtered by "prod"
    When I clear the search field
    Then I should see "production" in the environments list
    And I should see "staging" in the environments list

  # =============================================================================
  # Create Environment - Modal
  # =============================================================================

  @environments @create @critical
  Scenario: Open create environment modal
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    When I click the "Create Environment" button
    Then the "create-environment-modal" should be visible
    And I should see "Create New Environment"
    And the "environment-name-input" should be visible
    And the "environment-url-input" should be visible

  @environments @create @critical
  Scenario: Enter environment name and URL
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with name "qa-environment"
    And I fill the environment form with url "https://qa.example.com"
    Then the "environment-name-input" should have value "qa-environment"
    And the "environment-url-input" should have value "https://qa.example.com"

  @environments @create @variables
  Scenario: Add environment variables
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I click the "Add Variable" button
    Then the "variable-row" should be visible
    And I should see a variable key input
    And I should see a variable value input

  @environments @create @variables
  Scenario: Add multiple variables
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I click the "Add Variable" button
    And I fill variable 1 with key "API_KEY" and value "secret123"
    And I click the "Add Variable" button
    And I fill variable 2 with key "TIMEOUT" and value "30"
    Then I should see 2 variable rows
    And variable 1 should have key "API_KEY"
    And variable 2 should have key "TIMEOUT"

  @environments @create @variables
  Scenario: Remove a variable
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    And I have added 2 variables
    When I click the remove button for variable 1
    Then I should see 1 variable row
    And variable 1 should have key "TIMEOUT"

  @environments @create @validation
  Scenario: Validation error for missing name
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with url "https://test.example.com"
    And I click the "Save" button
    Then I should see "Name is required"
    And the "create-environment-modal" should be visible

  @environments @create @validation
  Scenario: Validation error for invalid URL
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with name "invalid-url-env"
    And I fill the environment form with url "not-a-valid-url"
    And I click the "Save" button
    Then I should see "Invalid URL format"
    And the "create-environment-modal" should be visible

  @environments @create @validation
  Scenario: Validation error for missing URL
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with name "no-url-env"
    And I click the "Save" button
    Then I should see "Base URL is required"
    And the "create-environment-modal" should be visible

  @environments @create @success @critical
  Scenario: Successfully create environment
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with name "new-test-env"
    And I fill the environment form with url "https://test.example.com"
    And I click the "Save" button
    Then I should see "Environment created successfully"
    And the "create-environment-modal" should not be visible
    And I should see "new-test-env" in the environments list

  @environments @create
  Scenario: Cancel create environment discards changes
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And the create environment modal is open
    When I fill the environment form with name "cancelled-env"
    And I click the "Cancel" button
    Then the "create-environment-modal" should not be visible
    And I should not see "cancelled-env" in the environments list

  # =============================================================================
  # Edit Environment
  # =============================================================================

  @environments @edit @critical
  Scenario: Open edit form for environment
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "edit-me-env" exists
    When I click the edit button for environment "edit-me-env"
    Then the "edit-environment-modal" should be visible
    And the "environment-name-input" should have value "edit-me-env"

  @environments @edit
  Scenario: Update environment name
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "old-name-env" exists
    When I click the edit button for environment "old-name-env"
    And I clear the "environment-name-input" field
    And I enter "new-name-env" into the "environment-name-input" field
    And I click the "Save" button
    Then I should see "Environment updated successfully"
    And I should see "new-name-env" in the environments list
    And I should not see "old-name-env" in the environments list

  @environments @edit
  Scenario: Update base URL
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "url-change-env" and url "https://old.example.com" exists
    When I click the edit button for environment "url-change-env"
    And I clear the "environment-url-input" field
    And I enter "https://new.example.com" into the "environment-url-input" field
    And I click the "Save" button
    Then I should see "Environment updated successfully"
    And the environment "url-change-env" should have url "https://new.example.com"

  @environments @edit @variables
  Scenario: Add new variable to existing environment
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "add-var-env" and 1 variable exists
    When I click the edit button for environment "add-var-env"
    And I click the "Add Variable" button
    And I fill the new variable with key "NEW_VAR" and value "new_value"
    And I click the "Save" button
    Then I should see "Environment updated successfully"
    And the environment should have 2 variables

  @environments @edit @variables
  Scenario: Remove variable from existing environment
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "remove-var-env" and 2 variables exists
    When I click the edit button for environment "remove-var-env"
    And I click the remove button for the first variable
    And I click the "Save" button
    Then I should see "Environment updated successfully"
    And the environment should have 1 variable

  @environments @edit
  Scenario: Cancel edit discards changes
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "keep-original-env" exists
    When I click the edit button for environment "keep-original-env"
    And I clear the "environment-name-input" field
    And I enter "changed-name" into the "environment-name-input" field
    And I click the "Cancel" button
    Then the "edit-environment-modal" should not be visible
    And I should see "keep-original-env" in the environments list
    And I should not see "changed-name" in the environments list

  # =============================================================================
  # Delete Environment
  # =============================================================================

  @environments @delete @critical
  Scenario: Delete environment with confirmation
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "delete-me-env" exists
    When I click the delete button for environment "delete-me-env"
    Then the "confirm-delete-modal" should be visible
    And I should see "Are you sure you want to delete"
    When I click the "Delete" button
    Then I should see "Environment deleted successfully"
    And I should not see "delete-me-env" in the environments list

  @environments @delete
  Scenario: Cancel delete confirmation
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "keep-me-env" exists
    When I click the delete button for environment "keep-me-env"
    Then the "confirm-delete-modal" should be visible
    When I click the "Cancel" button
    Then the "confirm-delete-modal" should not be visible
    And I should see "keep-me-env" in the environments list

  @environments @delete @validation
  Scenario: Cannot delete environment in use by scheduled run
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "in-use-env" exists
    And the environment "in-use-env" is used by a scheduled run
    When I click the delete button for environment "in-use-env"
    And I click the "Delete" button
    Then I should see "Cannot delete environment"
    And I should see "This environment is in use"
    And I should see "in-use-env" in the environments list

  @environments @delete
  Scenario: Deleted environment is removed from list immediately
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "quick-delete-env" exists
    When I click the delete button for environment "quick-delete-env"
    And I click the "Delete" button
    Then the environment "quick-delete-env" should be removed from the list
    And the environments count should decrease by 1

  # =============================================================================
  # Variables Editor
  # =============================================================================

  @environments @variables @display @critical
  Scenario: View environment variables
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "vars-env" and variables exists:
      | key        | value           |
      | API_KEY    | secret-key-123  |
      | BASE_URL   | https://api.com |
      | DEBUG      | true            |
    When I click on the environment "vars-env"
    Then the "variables-section" should be visible
    And I should see variable "API_KEY"
    And I should see variable "BASE_URL"
    And I should see variable "DEBUG"

  @environments @variables @security @critical
  Scenario: Mask sensitive values by default
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "secure-vars-env" and sensitive variables exists:
      | key        | value           | sensitive |
      | API_KEY    | secret-key-123  | true      |
      | PUBLIC_URL | https://api.com | false     |
    When I click on the environment "secure-vars-env"
    Then the value for "API_KEY" should be masked
    And I should see "********" for variable "API_KEY"
    And the value for "PUBLIC_URL" should be visible

  @environments @variables @security
  Scenario: Toggle to show sensitive values
    Given I am logged in as "test.user@example.com"
    And I am on the environment details page for "secure-vars-env"
    And the variable "API_KEY" is masked
    When I click the show value button for "API_KEY"
    Then the value for "API_KEY" should be visible
    And I should see "secret-key-123" for variable "API_KEY"
    And the "hide-value-btn" should be visible for "API_KEY"

  @environments @variables @copy
  Scenario: Copy variable value to clipboard
    Given I am logged in as "test.user@example.com"
    And I am on the environment details page for "copy-vars-env"
    And the environment has variable "COPY_ME" with value "copy-this-value"
    When I click the copy button for variable "COPY_ME"
    Then I should see "Copied to clipboard"
    And the clipboard should contain "copy-this-value"

  @environments @variables @edit
  Scenario: Edit variable value inline
    Given I am logged in as "test.user@example.com"
    And I am on the environment details page for "edit-vars-env"
    And the environment has variable "EDIT_ME" with value "old-value"
    When I click the edit button for variable "EDIT_ME"
    And I clear the variable value input
    And I enter "new-value" into the variable value input
    And I click the "Save" button for the variable
    Then I should see "Variable updated"
    And the variable "EDIT_ME" should have value "new-value"

  @environments @variables @persistence
  Scenario: Variables persist after save
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    And an environment with name "persist-vars-env" exists
    When I click the edit button for environment "persist-vars-env"
    And I click the "Add Variable" button
    And I fill the new variable with key "PERSIST_KEY" and value "persist_value"
    And I click the "Save" button
    And I refresh the page
    And I click on the environment "persist-vars-env"
    Then I should see variable "PERSIST_KEY"
    And the variable "PERSIST_KEY" should have value "persist_value"

  # =============================================================================
  # Navigation
  # =============================================================================

  @environments @navigation
  Scenario: Navigate to environments page from sidebar
    Given I am logged in as "test.user@example.com"
    And I am on the "dashboard" page
    When I click the link "Environments"
    Then I should be on the "environments" page
    And the "environments-nav-link" should have class "active"

  @environments @navigation
  Scenario: Environments page shows in breadcrumb
    Given I am logged in as "test.user@example.com"
    And I am on the "environments" page
    Then the "breadcrumb" should be visible
    And I should see "Environments" in the breadcrumb
