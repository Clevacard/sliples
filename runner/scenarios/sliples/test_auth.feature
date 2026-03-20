# Authentication and API Key Management Tests
# ============================================
# Tests for Phase 2 - Core API Authentication
#
# These scenarios test API key lifecycle management including:
# - Creating new API keys
# - Listing API keys (with masking)
# - Revoking API keys
# - Authentication with valid/invalid/revoked keys

@phase2 @auth @api
Feature: API Key Management
  As an API administrator
  I want to manage API keys securely
  So that I can control access to the Sliples platform

  Background:
    Given the API server is running at "http://localhost:8000"
    And I have admin access to the system

  # =============================================================================
  # API Key Creation
  # =============================================================================

  @auth @create @happy-path
  Scenario: Create a new API key with a name
    When I create a new API key named "ci-pipeline-key"
    Then the response status code should be 201
    And I should receive the full API key in the response
    And the key should start with "slp_"
    And the key should be at least 32 characters long
    And the response should include a warning to save the key

  @auth @create @happy-path
  Scenario: Create an API key with environment restrictions
    Given an environment "production" exists
    And an environment "staging" exists
    When I create a new API key named "staging-only-key" with environments:
      | environment |
      | staging     |
    Then the response status code should be 201
    And the API key should be restricted to the "staging" environment

  @auth @create @validation
  Scenario: Cannot create API key without a name
    When I try to create an API key without a name
    Then the response status code should be 400
    And the error message should indicate "name is required"

  @auth @create @validation
  Scenario: Cannot create API key with duplicate name
    Given an API key named "my-key" already exists
    When I create a new API key named "my-key"
    Then the response status code should be 400
    And the error message should indicate "name already exists"

  # =============================================================================
  # API Key Listing
  # =============================================================================

  @auth @list @happy-path
  Scenario: List all API keys shows masked keys
    Given the following API keys exist:
      | name          | created_at          |
      | ci-key        | 2024-01-01T10:00:00 |
      | dev-key       | 2024-01-15T10:00:00 |
      | production-key| 2024-02-01T10:00:00 |
    When I list all API keys
    Then the response status code should be 200
    And I should see 3 API keys in the list
    And each key should display only the first 8 characters
    And the full key value should NOT be visible

  @auth @list @happy-path
  Scenario: List API keys includes metadata
    Given an API key named "test-key" exists
    When I list all API keys
    Then each key entry should include:
      | field       |
      | id          |
      | name        |
      | key_prefix  |
      | created_at  |
      | last_used_at|
      | active      |

  @auth @list @security
  Scenario: Cannot list API keys without authentication
    Given I have no API key configured
    When I try to list all API keys without authentication
    Then the response status code should be 401
    And the response should contain "API key required"

  # =============================================================================
  # API Key Revocation
  # =============================================================================

  @auth @revoke @happy-path
  Scenario: Revoke an API key
    Given an API key named "temporary-key" exists
    And I have the ID of "temporary-key"
    When I revoke the API key by ID
    Then the response status code should be 200
    And the response should confirm the key has been revoked
    And the key should be marked as inactive

  @auth @revoke @happy-path
  Scenario: Revoked key appears as inactive in list
    Given an API key named "revoked-key" exists
    And the API key "revoked-key" has been revoked
    When I list all API keys
    Then the key "revoked-key" should show "active" as false

  @auth @revoke @validation
  Scenario: Cannot revoke non-existent API key
    When I try to revoke an API key with ID "00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the error message should indicate "API key not found"

  @auth @revoke @validation
  Scenario: Cannot revoke already revoked key
    Given an API key named "already-revoked" exists
    And the API key "already-revoked" has been revoked
    When I try to revoke the API key "already-revoked" again
    Then the response status code should be 400
    And the error message should indicate "key is already revoked"

  # =============================================================================
  # Authentication with API Keys
  # =============================================================================

  @auth @authentication @happy-path
  Scenario: Valid API key authenticates successfully
    Given I have created a valid API key
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 200
    And I should receive a valid JSON response

  @auth @authentication @security
  Scenario: Invalid API key is rejected
    Given I have an invalid API key "invalid-key-12345"
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 401
    And the response body should contain "Invalid API key"

  @auth @authentication @security
  Scenario: Revoked API key is rejected
    Given I have created an API key named "to-be-revoked"
    And I have saved the full key value
    And the API key "to-be-revoked" has been revoked
    When I try to authenticate using the revoked key
    Then the response status code should be 401
    And the response body should contain "Invalid API key"

  @auth @authentication @security
  Scenario: Missing API key is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/scenarios" without authentication
    Then the response status code should be 401
    And the response body should contain "API key required"

  @auth @authentication @security
  Scenario: API key with wrong format is rejected
    Given I have a malformed API key "not-a-valid-format"
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 401
    And the response body should contain "Invalid API key"

  # =============================================================================
  # Environment-Restricted Keys
  # =============================================================================

  @auth @environment-restriction @happy-path
  Scenario: Environment-restricted key works for allowed environment
    Given an environment "staging" exists
    And I have an API key restricted to "staging"
    When I access resources for the "staging" environment
    Then the response status code should be 200

  @auth @environment-restriction @security
  Scenario: Environment-restricted key denied for other environments
    Given an environment "staging" exists
    And an environment "production" exists
    And I have an API key restricted to "staging"
    When I try to access resources for the "production" environment
    Then the response status code should be 403
    And the error message should indicate "access denied for this environment"

  # =============================================================================
  # API Key Usage Tracking
  # =============================================================================

  @auth @tracking @happy-path
  Scenario: API key last_used_at is updated on use
    Given I have created a valid API key named "tracked-key"
    And I note the current time
    When I send a GET request to "/api/v1/health" with the API key header
    And I wait 1 second
    When I list all API keys
    Then the "tracked-key" should have "last_used_at" updated to approximately now

  # =============================================================================
  # Bootstrap Mode
  # =============================================================================

  @auth @bootstrap @happy-path
  Scenario: Bootstrap mode accepts any key when no keys exist
    Given no API keys exist in the database
    When I send a GET request to "/api/v1/health" with any API key
    Then the response status code should be 200
    And the system should operate in bootstrap mode

  @auth @bootstrap @transition
  Scenario: Bootstrap mode disabled after first key created
    Given no API keys exist in the database
    When I create the first API key named "admin-key"
    And I try to use a random key "random-123"
    Then the response status code should be 401
    And only the newly created key should work
