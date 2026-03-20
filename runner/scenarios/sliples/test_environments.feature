# Environment Management Tests
# ============================
# Tests for Phase 2 - Environment CRUD and Configuration
#
# These scenarios test environment management including:
# - Create, Read, Update, Delete operations
# - Validation rules (URL format, required fields)
# - Browser configuration management

@phase2 @environments @api
Feature: Environment Management
  As a test administrator
  I want to manage test environments
  So that I can run tests against different target systems

  Background:
    Given the API server is running at "http://localhost:8000"
    And I have a valid API key

  # =============================================================================
  # Create Environment
  # =============================================================================

  @environments @create @happy-path
  Scenario: Create a basic environment
    When I create an environment with:
      | field    | value                     |
      | name     | qa-environment            |
      | base_url | https://qa.example.com    |
    Then the response status code should be 201
    And the response JSON should include:
      | field    | value                     |
      | name     | qa-environment            |
      | base_url | https://qa.example.com    |
    And the JSON field "id" should be a valid UUID

  @environments @create @happy-path
  Scenario: Create environment with all optional fields
    When I create an environment with:
      | field           | value                      |
      | name            | full-config-env            |
      | base_url        | https://test.example.com   |
      | credentials_env | TEST_ENV_CREDENTIALS       |
      | retention_days  | 90                         |
    And I include variables:
      | key          | value   |
      | timeout      | 30      |
      | debug_mode   | true    |
      | api_version  | v2      |
    Then the response status code should be 201
    And the response should include the variables I specified
    And the retention_days should be 90

  @environments @create @happy-path
  Scenario: Create environment with browser configurations
    When I create an environment with:
      | field    | value                      |
      | name     | multi-browser-env          |
      | base_url | https://test.example.com   |
    And I include browser configurations:
      | browser  | version | channel |
      | chrome   | latest  | stable  |
      | firefox  | 120     | stable  |
    Then the response status code should be 201
    And the environment should have 2 browser configurations

  # =============================================================================
  # Create Environment - Validation Errors
  # =============================================================================

  @environments @create @validation
  Scenario: Cannot create environment without name
    When I try to create an environment without a name
    Then the response status code should be 422
    And the error should indicate "name" is required

  @environments @create @validation
  Scenario: Cannot create environment without base_url
    When I try to create an environment without a base_url
    Then the response status code should be 422
    And the error should indicate "base_url" is required

  @environments @create @validation
  Scenario: Cannot create environment with invalid URL
    When I create an environment with:
      | field    | value                |
      | name     | invalid-url-env      |
      | base_url | not-a-valid-url      |
    Then the response status code should be 422
    And the error should indicate invalid URL format

  @environments @create @validation
  Scenario: Cannot create environment with duplicate name
    Given an environment named "existing-env" already exists
    When I create an environment with:
      | field    | value                   |
      | name     | existing-env            |
      | base_url | https://new.example.com |
    Then the response status code should be 400
    And the error should indicate "name already exists"

  @environments @create @validation
  Scenario: Cannot create environment with empty name
    When I create an environment with:
      | field    | value                  |
      | name     |                        |
      | base_url | https://test.example.com|
    Then the response status code should be 422
    And the error should indicate name cannot be empty

  @environments @create @validation
  Scenario: Cannot create environment with name exceeding max length
    When I create an environment with name exceeding 100 characters
    Then the response status code should be 422
    And the error should indicate name is too long

  # =============================================================================
  # List Environments
  # =============================================================================

  @environments @list @happy-path
  Scenario: List all environments
    Given the following environments exist:
      | name        | base_url                    |
      | production  | https://prod.example.com    |
      | staging     | https://staging.example.com |
      | development | https://dev.example.com     |
    When I send a GET request to "/api/v1/environments"
    Then the response status code should be 200
    And the response should be a JSON array
    And the array should contain 3 environments
    And each environment should have "id", "name", "base_url" fields

  @environments @list @happy-path
  Scenario: List environments returns empty array when none exist
    Given no environments exist in the database
    When I send a GET request to "/api/v1/environments"
    Then the response status code should be 200
    And the response should be an empty JSON array

  @environments @list @security
  Scenario: Cannot list environments without authentication
    Given I have no API key configured
    When I send a GET request to "/api/v1/environments" without authentication
    Then the response status code should be 401

  # =============================================================================
  # Get Single Environment
  # =============================================================================

  @environments @get @happy-path
  Scenario: Get environment by ID
    Given an environment named "test-env" exists with ID stored
    When I send a GET request to "/api/v1/environments/{id}" using the stored ID
    Then the response status code should be 200
    And the response should include "name" equal to "test-env"

  @environments @get @validation
  Scenario: Get non-existent environment returns 404
    When I send a GET request to "/api/v1/environments/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the error should indicate "Environment not found"

  @environments @get @validation
  Scenario: Get environment with invalid UUID format
    When I send a GET request to "/api/v1/environments/not-a-uuid"
    Then the response status code should be 422
    And the error should indicate invalid UUID format

  # =============================================================================
  # Update Environment
  # =============================================================================

  @environments @update @happy-path
  Scenario: Update environment name
    Given an environment named "old-name" exists with ID stored
    When I send a PUT request to update the environment with:
      | field | value    |
      | name  | new-name |
    Then the response status code should be 200
    And the response should include "name" equal to "new-name"

  @environments @update @happy-path
  Scenario: Update environment base_url
    Given an environment named "url-test-env" exists with base_url "https://old.example.com"
    When I send a PUT request to update the environment with:
      | field    | value                   |
      | base_url | https://new.example.com |
    Then the response status code should be 200
    And the response should include "base_url" equal to "https://new.example.com"

  @environments @update @happy-path
  Scenario: Update environment variables
    Given an environment named "vars-test-env" exists with variables:
      | key     | value |
      | timeout | 30    |
    When I send a PUT request to update the environment with new variables:
      | key      | value |
      | timeout  | 60    |
      | retries  | 3     |
    Then the response status code should be 200
    And the environment should have variable "timeout" equal to "60"
    And the environment should have variable "retries" equal to "3"

  @environments @update @happy-path
  Scenario: Partial update only modifies specified fields
    Given an environment exists with:
      | field          | value                     |
      | name           | partial-update-env        |
      | base_url       | https://test.example.com  |
      | retention_days | 365                       |
    When I send a PUT request to update only:
      | field          | value |
      | retention_days | 30    |
    Then the response status code should be 200
    And the name should remain "partial-update-env"
    And the base_url should remain "https://test.example.com"
    And the retention_days should be 30

  @environments @update @validation
  Scenario: Cannot update environment with duplicate name
    Given an environment named "env-a" exists
    And an environment named "env-b" exists
    When I try to update "env-b" with name "env-a"
    Then the response status code should be 400
    And the error should indicate "name already exists"

  @environments @update @validation
  Scenario: Cannot update non-existent environment
    When I send a PUT request to "/api/v1/environments/00000000-0000-0000-0000-000000000000" with:
      | field | value    |
      | name  | new-name |
    Then the response status code should be 404
    And the error should indicate "Environment not found"

  @environments @update @validation
  Scenario: Cannot update environment with invalid URL
    Given an environment named "url-validation-env" exists
    When I send a PUT request to update the environment with:
      | field    | value           |
      | base_url | invalid-url     |
    Then the response status code should be 422
    And the error should indicate invalid URL format

  # =============================================================================
  # Delete Environment
  # =============================================================================

  @environments @delete @happy-path
  Scenario: Delete an environment
    Given an environment named "to-delete-env" exists with ID stored
    When I send a DELETE request to "/api/v1/environments/{id}" using the stored ID
    Then the response status code should be 204
    And the environment should no longer exist

  @environments @delete @happy-path
  Scenario: Delete environment also removes browser configs
    Given an environment named "env-with-configs" exists with browser configurations:
      | browser | version |
      | chrome  | latest  |
      | firefox | 120     |
    When I delete the environment "env-with-configs"
    Then the response status code should be 204
    And the associated browser configurations should be deleted

  @environments @delete @validation
  Scenario: Cannot delete non-existent environment
    When I send a DELETE request to "/api/v1/environments/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the error should indicate "Environment not found"

  @environments @delete @validation
  Scenario: Delete is idempotent - deleting twice does not cause error
    Given an environment named "delete-twice-env" exists with ID stored
    When I send a DELETE request to delete the environment
    Then the response status code should be 204
    When I send a DELETE request to delete the same environment again
    Then the response status code should be 404

  # =============================================================================
  # Browser Configuration Management
  # =============================================================================

  @environments @browsers @happy-path
  Scenario: Add browser configuration to existing environment
    Given an environment named "browser-config-env" exists without browser configs
    When I add a browser configuration:
      | browser | version | channel |
      | chrome  | latest  | stable  |
    Then the response status code should be 201
    And the environment should have 1 browser configuration

  @environments @browsers @happy-path
  Scenario: List browser configurations for environment
    Given an environment named "multi-browser-env" exists with browser configurations:
      | browser | version | channel |
      | chrome  | latest  | stable  |
      | firefox | 120     | stable  |
      | webkit  | latest  | stable  |
    When I request browser configurations for the environment
    Then the response status code should be 200
    And I should see 3 browser configurations

  @environments @browsers @happy-path
  Scenario: Update browser configuration
    Given an environment with a chrome browser config exists
    And the chrome config has version "119"
    When I update the browser configuration to version "120"
    Then the response status code should be 200
    And the browser version should be "120"

  @environments @browsers @happy-path
  Scenario: Remove browser configuration
    Given an environment with 2 browser configurations exists
    When I remove one browser configuration
    Then the response status code should be 204
    And the environment should have 1 browser configuration remaining

  @environments @browsers @validation
  Scenario: Cannot add browser config with invalid browser type
    Given an environment named "browser-validation-env" exists
    When I try to add a browser configuration with browser "invalid-browser"
    Then the response status code should be 422
    And the error should indicate invalid browser type

  @environments @browsers @validation
  Scenario: Cannot add duplicate browser configuration
    Given an environment with a chrome stable configuration exists
    When I try to add another chrome stable configuration
    Then the response status code should be 400
    And the error should indicate "browser configuration already exists"

  # =============================================================================
  # Environment Variables
  # =============================================================================

  @environments @variables @happy-path
  Scenario: Environment variables are persisted correctly
    When I create an environment with variables:
      | key             | value                |
      | API_TIMEOUT     | 30000                |
      | DEBUG           | true                 |
      | SERVICE_URL     | https://api.test.com |
    And I retrieve the environment
    Then all variables should be present with correct values

  @environments @variables @happy-path
  Scenario: Environment variables support various data types
    When I create an environment with variables:
      | key         | value          | type    |
      | string_var  | hello          | string  |
      | number_var  | 42             | number  |
      | bool_var    | true           | boolean |
      | nested_var  | {"key": "val"} | object  |
    Then the response status code should be 201
    And variables should preserve their types when retrieved

  @environments @variables @security
  Scenario: Sensitive variables are handled securely
    When I create an environment with:
      | field           | value         |
      | name            | secure-env    |
      | base_url        | https://x.com |
      | credentials_env | SECRET_CREDS  |
    Then the credentials_env reference should be stored
    But the actual credential value should not be in the response
