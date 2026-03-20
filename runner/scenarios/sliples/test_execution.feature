@phase3 @execution @api
Feature: Test Execution and Screenshots
  As a Sliples user
  I want to trigger test executions and capture screenshots
  So that I can verify my test scenarios run correctly and failures are documented

  Background:
    Given I have a valid API key
    And at least one environment exists

  # =============================================================================
  # Test Execution Flow
  # =============================================================================

  @execution @trigger @critical
  Scenario: Trigger a test run starts execution
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    Then the response status code should be 202
    And the test run should be queued
    And the JSON field "id" should be a valid UUID
    And the JSON field "status" should equal "queued"

  @execution @status @transition
  Scenario: Test run status transitions from queued to running
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to start
    Then the run status should be "running" or "passed" or "failed"

  @execution @status @complete
  Scenario: Test run completes with final status
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    Then the run status should be "passed" or "failed" or "error"
    And the run should have a finished timestamp

  @execution @polling
  Scenario: Poll test run status endpoint
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}/status"
    Then the response status code should be 200
    And the response should contain "status"
    And the response should contain "total_scenarios"
    And the response should contain "completed_steps"

  # =============================================================================
  # Multi-Browser Execution
  # =============================================================================

  @execution @browser @chrome
  Scenario: Trigger test run with Chrome browser
    Given a simple test scenario exists
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 202
    And the JSON field "browser" should equal "chrome"

  @execution @browser @firefox
  Scenario: Trigger test run with Firefox browser
    Given a simple test scenario exists
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

  @execution @browser @multi
  Scenario: Trigger test run with multiple browsers
    Given a simple test scenario exists
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["chrome", "firefox"]
      }
      """
    Then the response status code should be 202
    And a test run should be created for each browser

  # =============================================================================
  # Parallel Execution
  # =============================================================================

  @execution @parallel
  Scenario: Trigger parallel test execution
    Given multiple test scenarios exist
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

  @execution @sequential
  Scenario: Trigger sequential test execution
    Given multiple test scenarios exist
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
  # Screenshot Capture
  # =============================================================================

  @execution @screenshots @critical
  Scenario: Test results include screenshot URLs
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the response status code should be 200
    And the response should contain "results"
    And the results should include screenshot URLs if available

  @execution @screenshots @failure
  Scenario: Screenshots are captured on test failure
    Given a scenario that will fail exists
    When I trigger a test run for the failing scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the run status should be "failed"
    And failed steps should have screenshot URLs

  @execution @screenshots @url
  Scenario: Screenshot URLs are accessible
    Given a completed test run with screenshots exists
    When I get the first screenshot URL from results
    And I fetch the screenshot URL
    Then the screenshot response status should be 200
    And the screenshot content type should be an image

  @execution @screenshots @s3
  Scenario: Screenshots are stored in S3
    Given a completed test run with screenshots exists
    When I get the first screenshot URL from results
    Then the screenshot URL should contain the S3 bucket path

  # =============================================================================
  # Step-Level Results
  # =============================================================================

  @execution @results @steps
  Scenario: Test run includes step-level results
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the response status code should be 200
    And the results array should not be empty
    And each result should have step_name and status

  @execution @results @duration
  Scenario: Step results include duration
    Given a completed test run exists
    When I get the test run details
    Then each step result should have a duration_ms field
    And duration values should be non-negative integers

  @execution @results @error-message
  Scenario: Failed steps include error messages
    Given a scenario that will fail exists
    When I trigger a test run for the failing scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then failed steps should have error messages

  # =============================================================================
  # Retry Functionality
  # =============================================================================

  @execution @retry
  Scenario: Retry a failed test run
    Given a completed test run with status "failed" exists
    When I store the response field "id" as "original_run_id"
    And I send a POST request to "/api/v1/runs/{original_run_id}/retry"
    Then the response status code should be 202
    And a new test run should be created
    And the new run should have the same configuration as the original

  @execution @retry @in-progress
  Scenario: Cannot retry an in-progress test run
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I send a POST request to "/api/v1/runs/{run_id}/retry"
    Then the response status code should be 400
    And the response body should contain "in progress"

  # =============================================================================
  # Test Run Report
  # =============================================================================

  @execution @report
  Scenario: Get HTML report for completed run
    Given a completed test run exists
    When I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the response status code should be 200
    And the response content type should be text/html

  @execution @report @pending
  Scenario: Report not available for pending run
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the response status code should be 404
    And the response body should contain "not yet generated"

  # =============================================================================
  # Error Handling
  # =============================================================================

  @execution @error @no-scenarios
  Scenario: Test run fails when no matching scenarios found
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["nonexistent-tag-xyz123"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 400
    And the response body should contain "No scenarios found"

  @execution @error @invalid-env
  Scenario: Test run fails with non-existent environment
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "nonexistent-env",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 404
    And the response body should contain "not found"

  @execution @error @auth
  Scenario: Unauthorized execution request is rejected
    Given I have no API key configured
    When I send a POST request to "/api/v1/runs" without authentication with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 401

  # =============================================================================
  # Execution Timestamps
  # =============================================================================

  @execution @timestamps
  Scenario: Test run tracks execution timestamps
    Given a simple test scenario exists
    When I trigger a test run for the scenario
    And I store the response field "id" as "run_id"
    And I wait for the run to complete with timeout 120 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the response should contain "started_at"
    And the response should contain "finished_at"
    And finished_at should be after started_at

  @execution @timestamps @created
  Scenario: Test run has creation timestamp
    When I trigger a test run with tags "phase1" on environment "test-environment"
    Then the response status code should be 202
    And the response should contain "created_at"
    And the created_at timestamp should be recent

  # =============================================================================
  # Scenario Selection
  # =============================================================================

  @execution @selection @tags
  Scenario: Execute scenarios by tag
    When I trigger a test run with tags "phase1" on environment "test-environment"
    Then the response status code should be 202
    And the run should include matching scenarios

  @execution @selection @ids
  Scenario: Execute scenarios by explicit IDs
    Given at least one scenario exists
    When I store the response field "id" as "scenario_id"
    And I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_ids": ["{scenario_id}"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 202

  @execution @selection @multiple-tags
  Scenario: Execute scenarios matching multiple tags
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1", "health"],
        "environment": "test-environment",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 202
