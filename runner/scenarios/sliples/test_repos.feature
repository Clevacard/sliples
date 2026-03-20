@phase2 @repos @api
Feature: Repository Management
  As a Sliples user
  I want to manage scenario repositories
  So that I can organize and sync test scenarios from Git repositories

  Background:
    Given I have a valid API key

  # =============================================================================
  # Success Cases
  # =============================================================================

  @repos @create @critical
  Scenario: Add a new repository
    When I add a repository with name "test-repo-qa" and URL "https://github.com/example/tests.git"
    Then the response status code should be 201
    And the repository should be created
    And the JSON field "id" should be a valid UUID
    And the JSON field "name" should equal "test-repo-qa"
    And the JSON field "git_url" should equal "https://github.com/example/tests.git"
    And it should appear in the repository list

  @repos @list
  Scenario: List all repositories
    Given at least one repository exists
    When I list all repositories
    Then the response status code should be 200
    And the response should be a JSON array
    And each item should have fields "id, name, git_url, branch"

  @repos @list @filter
  Scenario: List repositories returns multiple repos
    Given a repository with name "repo-alpha" exists
    And a repository with name "repo-beta" exists
    When I list all repositories
    Then the response status code should be 200
    And the response should be a JSON array
    And the response should have at least 2 items

  @repos @sync
  Scenario: Sync a repository
    Given a repository with name "sync-test-repo" exists
    When I sync the repository
    Then the response status code should be 200
    And the sync should be started
    And the response should contain "status"

  @repos @sync-all
  Scenario: Sync all repositories
    Given at least one repository exists
    When I send a POST request to "/api/v1/repos/sync-all"
    Then the response status code should be 200
    And the response should contain "status"
    And the JSON field "status" should equal "sync_started"

  @repos @delete
  Scenario: Delete a repository
    Given a repository with name "delete-test-repo" exists
    When I delete the repository
    Then the response status code should be 204
    And the repository should be deleted
    And it should not appear in the repository list

  @repos @details
  Scenario: Get repository details
    Given a repository with name "details-test-repo" exists
    When I store the response field "id" as "repo_id"
    And I send a GET request to "/api/v1/repos/{repo_id}"
    Then the response status code should be 200
    And the JSON field "name" should equal "details-test-repo"

  # =============================================================================
  # Error Cases
  # =============================================================================

  @repos @error @duplicate
  Scenario: Cannot create repository with duplicate name
    Given a repository with name "duplicate-repo" exists
    When I add a repository with name "duplicate-repo" and URL "https://github.com/other/repo.git"
    Then the response status code should be 400
    And the response body should contain "already exists"

  @repos @error @not-found
  Scenario: Sync non-existent repository returns 404
    When I send a POST request to "/api/v1/repos/00000000-0000-0000-0000-000000000000/sync"
    Then the response status code should be 404
    And the response body should contain "not found"

  @repos @error @not-found
  Scenario: Delete non-existent repository returns 404
    When I send a DELETE request to "/api/v1/repos/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the response body should contain "not found"

  @repos @error @auth
  Scenario: Unauthorized access to repositories is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/repos" without authentication
    Then the response status code should be 401

  @repos @error @auth
  Scenario: Invalid API key is rejected for repository operations
    Given I have an invalid API key "invalid-key-12345"
    When I send a GET request to "/api/v1/repos" with the API key header
    Then the response status code should be 401

  # =============================================================================
  # Data Validation
  # =============================================================================

  @repos @validation
  Scenario: Repository creation validates required fields
    When I send a POST request to "/api/v1/repos" with body:
      """
      {
        "name": ""
      }
      """
    Then the response status code should be 422

  @repos @validation
  Scenario: Repository stores branch and sync_path defaults
    When I send a POST request to "/api/v1/repos" with body:
      """
      {
        "name": "minimal-repo",
        "git_url": "https://github.com/example/minimal.git"
      }
      """
    Then the response status code should be 201
    And the JSON field "branch" should equal "main"
    And the JSON field "sync_path" should equal "scenarios"
