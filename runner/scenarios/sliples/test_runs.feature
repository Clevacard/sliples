@phase2 @runs @api
Feature: Test Run Management
  As a Sliples user
  I want to manage test runs
  So that I can trigger, monitor, and control test executions

  Background:
    Given I have a valid API key
    And at least one environment exists

  # =============================================================================
  # Triggering Test Runs
  # =============================================================================

  @runs @trigger @critical
  Scenario: Trigger a test run by tags
    When I trigger a test run with tags "phase1" on environment "test-environment"
    Then the response status code should be 202
    And the test run should be queued
    And the JSON field "id" should be a valid UUID
    And the JSON field "status" should equal "queued"

  @runs @trigger
  Scenario: Trigger a test run with multiple tags
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1", "health"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 202
    And the JSON field "status" should equal "queued"

  @runs @trigger @browser
  Scenario: Trigger a test run with specific browser
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["firefox"]
      }
      """
    Then the response status code should be 202
    And the JSON field "browser" should equal "firefox"

  @runs @trigger @parallel
  Scenario: Trigger a parallel test run
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "parallel": true
      }
      """
    Then the response status code should be 202
    And the JSON field "parallel" should equal "True"

  @runs @trigger @sequential
  Scenario: Trigger a sequential test run
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "parallel": false
      }
      """
    Then the response status code should be 202
    And the JSON field "parallel" should equal "False"

  # =============================================================================
  # Listing Test Runs
  # =============================================================================

  @runs @list @critical
  Scenario: List all test runs
    Given at least one test run exists
    When I list all test runs
    Then the response status code should be 200
    And the response should be a JSON array
    And each item should have fields "id, status, browser, created_at"

  @runs @list @pagination
  Scenario: List test runs with pagination
    When I send a GET request to "/api/v1/runs?limit=10&offset=0"
    Then the response status code should be 200
    And the response should be a JSON array

  @runs @list @filter @status
  Scenario: Filter test runs by status - queued
    Given at least one test run exists
    When I filter test runs by status "queued"
    Then the response status code should be 200
    And the response should be a JSON array

  @runs @list @filter @status
  Scenario: Filter test runs by status - running
    When I filter test runs by status "running"
    Then the response status code should be 200
    And the response should be a JSON array

  @runs @list @filter @status
  Scenario: Filter test runs by status - passed
    When I filter test runs by status "passed"
    Then the response status code should be 200
    And the response should be a JSON array

  @runs @list @filter @status
  Scenario: Filter test runs by status - failed
    When I filter test runs by status "failed"
    Then the response status code should be 200
    And the response should be a JSON array

  @runs @list @filter @environment
  Scenario: Filter test runs by environment
    Given at least one test run exists
    When I store the response field "environment_id" as "env_id"
    And I send a GET request to "/api/v1/runs?environment_id={env_id}"
    Then the response status code should be 200
    And the response should be a JSON array

  # =============================================================================
  # Test Run Details
  # =============================================================================

  @runs @details @critical
  Scenario: Get test run details
    Given at least one test run exists
    When I get the test run details
    Then the response status code should be 200
    And the JSON field "id" should be a valid UUID
    And the response should contain "status"
    And the response should contain "browser"
    And the response should contain "created_at"

  @runs @details
  Scenario: Test run details include environment reference
    Given at least one test run exists
    When I get the test run details
    Then the response status code should be 200
    And the response should contain "environment_id"

  @runs @details @results
  Scenario: Test run details include step-level results
    Given at least one test run exists
    When I get the test run details
    Then the response status code should be 200
    And the response should contain "results"
    And the response should include step-level results

  @runs @details @not-found
  Scenario: Get non-existent test run returns 404
    When I send a GET request to "/api/v1/runs/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the response body should contain "not found"

  # =============================================================================
  # Cancelling Test Runs
  # =============================================================================

  @runs @cancel @critical
  Scenario: Cancel a queued test run
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the response status code should be 202
    When I cancel the test run
    Then the response status code should be 204
    And the test run should be cancelled

  @runs @cancel @not-found
  Scenario: Cancel non-existent test run returns 404
    When I send a DELETE request to "/api/v1/runs/00000000-0000-0000-0000-000000000000"
    Then the response status code should be 404
    And the response body should contain "not found"

  @runs @cancel @already-finished
  Scenario: Cannot cancel an already finished test run
    Given a test run with status "passed" exists
    When I cancel the test run
    Then the response status code should be 400
    And the response body should contain "Can only cancel"

  # =============================================================================
  # Test Run Reports
  # =============================================================================

  @runs @report
  Scenario: Get test run report
    Given at least one test run exists
    When I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the response status code should be 200

  @runs @report @not-ready
  Scenario: Report not available for run without results
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the response status code should be 404
    And the response body should contain "not yet generated"

  # =============================================================================
  # Error Cases
  # =============================================================================

  @runs @error @auth
  Scenario: Unauthorized access to test runs is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/runs" without authentication
    Then the response status code should be 401

  @runs @error @auth
  Scenario: Invalid API key is rejected for test run operations
    Given I have an invalid API key "invalid-run-key"
    When I send a GET request to "/api/v1/runs" with the API key header
    Then the response status code should be 401

  @runs @error @invalid-env
  Scenario: Trigger run with non-existent environment fails
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "nonexistent-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 404
    And the response body should contain "not found"

  @runs @error @validation
  Scenario: Trigger run requires environment
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 422

  @runs @error @invalid-uuid
  Scenario: Invalid UUID format for run ID returns 422
    When I send a GET request to "/api/v1/runs/not-a-valid-uuid"
    Then the response status code should be 422

  # =============================================================================
  # Advanced Scenarios
  # =============================================================================

  @runs @retry
  Scenario: Retrieve run status after creation
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the response status code should be 200
    And the JSON field "id" should not be empty

  @runs @timestamps
  Scenario: Test run includes timestamps
    Given at least one test run exists
    When I get the test run details
    Then the response status code should be 200
    And the response should contain "created_at"

  @runs @triggered-by
  Scenario: Test run tracks who triggered it
    When I trigger a test run with tags "phase1" on environment "test-environment"
    Then the response status code should be 202
    And the response should contain "triggered_by"
