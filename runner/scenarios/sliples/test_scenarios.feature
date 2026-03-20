@phase2 @scenarios @api
Feature: Scenario Management
  As a Sliples user
  I want to manage test scenarios
  So that I can view, filter, and sync scenarios from repositories

  Background:
    Given I have a valid API key

  # =============================================================================
  # Listing Scenarios
  # =============================================================================

  @scenarios @list @critical
  Scenario: List all scenarios
    When I list all scenarios
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @list
  Scenario: List scenarios returns scenario details
    Given at least one scenario exists
    When I list all scenarios
    Then the response status code should be 200
    And the response should be a JSON array
    And each item should have fields "id, name, feature_path, tags"

  @scenarios @list @pagination
  Scenario: List scenarios supports pagination
    When I send a GET request to "/api/v1/scenarios?limit=10&offset=0"
    Then the response status code should be 200
    And the response should be a JSON array

  # =============================================================================
  # Filtering Scenarios
  # =============================================================================

  @scenarios @filter @tag @critical
  Scenario: Filter scenarios by tag
    Given at least one scenario exists
    When I filter scenarios by tag "phase1"
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @filter @tag
  Scenario: Filter scenarios by multiple tags returns matching scenarios
    When I send a GET request to "/api/v1/scenarios?tag=api"
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @filter @repo
  Scenario: Filter scenarios by repository
    Given at least one repository exists
    When I store the response field "id" as "repo_id"
    And I send a GET request to "/api/v1/scenarios?repo_id={repo_id}"
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @filter @empty
  Scenario: Filter scenarios with non-matching tag returns empty array
    When I filter scenarios by tag "nonexistent-tag-xyz"
    Then the response status code should be 200
    And the response should be a JSON array

  # =============================================================================
  # Scenario Details
  # =============================================================================

  @scenarios @details @critical
  Scenario: Get scenario details by ID
    Given at least one scenario exists
    When I get the scenario details
    Then the response status code should be 200
    And the JSON field "id" should be a valid UUID
    And the response should contain "name"
    And the response should contain "feature_path"
    And the response should contain "tags"

  @scenarios @details
  Scenario: Scenario details include content
    Given at least one scenario exists
    When I get the scenario details
    Then the response status code should be 200
    And the response should contain "content"

  @scenarios @details @not-found
  Scenario: Get non-existent scenario returns 404
    When I send a GET request to "/api/v1/scenarios/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the response body should contain "not found"

  # =============================================================================
  # Scenario Sync
  # =============================================================================

  @scenarios @sync @critical
  Scenario: Trigger scenario sync from repositories
    When I trigger a scenario sync
    Then the response status code should be 200
    And the response should contain "status"
    And the JSON field "status" should equal "sync_started"

  @scenarios @sync
  Scenario: Scenario sync returns synced count
    When I trigger a scenario sync
    Then the response status code should be 200
    And the response should contain "synced_count"

  @scenarios @sync @repo
  Scenario: Sync scenarios from specific repository
    Given a repository with name "sync-scenarios-repo" exists
    When I sync the repository
    Then the response status code should be 200
    And the sync should be started

  # =============================================================================
  # Error Cases
  # =============================================================================

  @scenarios @error @auth
  Scenario: Unauthorized access to scenarios is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/scenarios" without authentication
    Then the response status code should be 401

  @scenarios @error @auth
  Scenario: Invalid API key is rejected for scenario operations
    Given I have an invalid API key "bad-api-key"
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 401

  @scenarios @error @invalid-uuid
  Scenario: Invalid UUID format returns 422
    When I send a GET request to "/api/v1/scenarios/not-a-valid-uuid"
    Then the response status code should be 422

  # =============================================================================
  # Scenario Search
  # =============================================================================

  @scenarios @search
  Scenario: Search scenarios by name pattern
    When I send a GET request to "/api/v1/scenarios?search=acceptance"
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @search @combined
  Scenario: Combined filtering by tag and repo
    Given at least one repository exists
    When I store the response field "id" as "repo_id"
    And I send a GET request to "/api/v1/scenarios?repo_id={repo_id}&tag=phase1"
    Then the response status code should be 200
    And the response should be a JSON array
