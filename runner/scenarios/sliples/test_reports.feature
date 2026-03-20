# Test Reports and Email Notifications
# =====================================
# Tests for Phase 3 - Reports & Notifications
#
# These scenarios test report generation and email notifications including:
# - HTML report generation after test run completion
# - Report content validation (pass/fail counts, screenshots)
# - Report API download endpoints
# - Email notification queuing and content
# - Failure notification details

@phase3 @reports @api
Feature: Test Reports
  As a Sliples user
  I want to access test reports after run completion
  So that I can review test results and share them with stakeholders

  Background:
    Given I have a valid API key
    And at least one environment exists

  # =============================================================================
  # HTML Report Generation
  # =============================================================================

  @reports @generation @critical
  Scenario: HTML report is generated for completed run
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the response content-type should be "text/html"
    And the report should be a valid HTML document

  @reports @generation
  Scenario: HTML report generated for failed run
    Given a test run with status "failed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the response content-type should be "text/html"
    And the report should contain failure details

  @reports @generation @not-ready
  Scenario: Report not available for queued run
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And I store the response field "id" as "run_id"
    And I request the report for run "{run_id}"
    Then the response status code should be 404
    And the response body should contain "not yet generated"

  @reports @generation @not-ready
  Scenario: Report not available for running test
    Given a test run with status "running" exists
    When I request the report for the completed run
    Then the response status code should be 404
    And the response body should contain "not yet generated"

  # =============================================================================
  # Report Content - Pass/Fail Counts
  # =============================================================================

  @reports @content @counts @critical
  Scenario: Report contains correct pass count
    Given a completed test run with known results exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should contain the run summary
    And the report should include pass count

  @reports @content @counts
  Scenario: Report contains correct fail count
    Given a test run with status "failed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include fail count

  @reports @content @counts
  Scenario: Report contains correct skip count
    Given a completed test run with skipped tests exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include skip count

  @reports @content @counts
  Scenario: Report summary shows total test count
    Given a completed test run with known results exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include total test count

  # =============================================================================
  # Report Content - Screenshots
  # =============================================================================

  @reports @screenshots @critical
  Scenario: Report includes screenshot links for failures
    Given a test run with status "failed" exists
    And the run has captured screenshots
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include screenshot links

  @reports @screenshots
  Scenario: Screenshot links are accessible
    Given a test run with status "failed" exists
    And the run has captured screenshots
    When I request the report for the completed run
    And I extract screenshot links from the report
    Then each screenshot link should be accessible

  @reports @screenshots
  Scenario: Report shows screenshot thumbnail previews
    Given a test run with status "failed" exists
    And the run has captured screenshots
    When I request the report for the completed run
    Then the report should include screenshot thumbnails

  # =============================================================================
  # Report Download via API
  # =============================================================================

  @reports @download @critical
  Scenario: Download report via API endpoint
    Given a test run with status "passed" exists
    When I send a GET request to download the report
    Then the response status code should be 200
    And the response content-type should be "text/html"
    And the response should include Content-Disposition header

  @reports @download @json
  Scenario: Download report as JSON
    Given a test run with status "passed" exists
    When I request the report in JSON format
    Then the response status code should be 200
    And the response content-type should be "application/json"
    And the JSON should include test results

  @reports @download @pdf
  Scenario: Download report as PDF
    Given a test run with status "passed" exists
    When I request the report in PDF format
    Then the response status code should be 200
    And the response content-type should be "application/pdf"

  @reports @download @not-found
  Scenario: Download report for non-existent run returns 404
    When I send a GET request to "/api/v1/runs/00000000-0000-0000-0000-000000000000/report"
    Then the response status code should be 404
    And the response body should contain "not found"

  # =============================================================================
  # Report Content - Environment Info
  # =============================================================================

  @reports @environment @critical
  Scenario: Report includes environment information
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include environment name
    And the report should include environment base URL

  @reports @environment
  Scenario: Report includes browser information
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include browser type
    And the report should include browser version

  @reports @environment
  Scenario: Report includes run timestamps
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include start timestamp
    And the report should include end timestamp
    And the report should include duration

  @reports @environment
  Scenario: Report includes triggered by information
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include triggered by information

  # =============================================================================
  # Report Content - Step Details
  # =============================================================================

  @reports @steps
  Scenario: Report includes step-level details
    Given a test run with status "passed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include step names
    And the report should include step statuses
    And the report should include step durations

  @reports @steps @errors
  Scenario: Report includes error messages for failed steps
    Given a test run with status "failed" exists
    When I request the report for the completed run
    Then the response status code should be 200
    And the report should include error messages
    And the report should include stack traces


@phase3 @notifications @api
Feature: Email Notifications
  As a Sliples user
  I want to receive email notifications when test runs complete
  So that I can be promptly informed of test results

  Background:
    Given I have a valid API key
    And at least one environment exists

  # =============================================================================
  # Email Notification on Completion
  # =============================================================================

  @notifications @completion @critical
  Scenario: Email is sent when test run completes successfully
    Given email notifications are configured
    And I have a valid notification recipient
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then an email notification should be queued
    And the email should be sent to the configured recipient

  @notifications @completion @critical
  Scenario: Email is sent when test run fails
    Given email notifications are configured
    And I have a valid notification recipient
    When I trigger a test run with tags "failing-tests" on environment "test-environment"
    And the run completes with failures
    Then an email notification should be queued
    And the email should indicate test failures

  @notifications @completion
  Scenario: No email sent when notifications are disabled
    Given email notifications are disabled
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then no email notification should be queued

  @notifications @completion
  Scenario: Email notification respects per-run settings
    Given email notifications are configured
    When I trigger a test run with notifications disabled
    And the run completes successfully
    Then no email notification should be queued

  # =============================================================================
  # Email Content - Run Summary
  # =============================================================================

  @notifications @summary @critical
  Scenario: Email contains run summary
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email should contain run summary
    And the summary should include total test count
    And the summary should include pass count
    And the summary should include fail count

  @notifications @summary
  Scenario: Email subject indicates test status
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email subject should contain "PASSED"

  @notifications @summary
  Scenario: Email subject indicates failure status
    Given email notifications are configured
    When I trigger a test run with tags "failing-tests" on environment "test-environment"
    And the run completes with failures
    Then the email subject should contain "FAILED"

  @notifications @summary
  Scenario: Email includes environment name in subject
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email subject should contain "test-environment"

  # =============================================================================
  # Email Content - Failure Details
  # =============================================================================

  @notifications @failures @critical
  Scenario: Email includes failure details for failed runs
    Given email notifications are configured
    When I trigger a test run with tags "failing-tests" on environment "test-environment"
    And the run completes with failures
    Then the email should include failure details
    And each failure should have scenario name
    And each failure should have error message

  @notifications @failures
  Scenario: Email includes screenshot attachment for failures
    Given email notifications are configured
    And screenshot attachments are enabled
    When I trigger a test run with tags "failing-tests" on environment "test-environment"
    And the run completes with failures
    Then the email should include screenshot attachments

  @notifications @failures
  Scenario: Email limits failure details to configured maximum
    Given email notifications are configured
    And max failure details is set to 5
    When I trigger a test run with many failures
    And the run completes with failures
    Then the email should include at most 5 failure details
    And the email should indicate more failures exist

  # =============================================================================
  # Email Content - Report Link
  # =============================================================================

  @notifications @report-link @critical
  Scenario: Email contains link to full report
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email should contain link to report
    And the report link should be a valid URL

  @notifications @report-link
  Scenario: Report link in email is accessible
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    And I extract the report link from the email
    Then the report link should return status 200

  # =============================================================================
  # Email Delivery - Celery Task Verification
  # =============================================================================

  @notifications @celery @critical
  Scenario: Email notification task is queued in Celery
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then a Celery task for email notification should be created
    And the task should be in the queue

  @notifications @celery
  Scenario: Email task contains correct payload
    Given email notifications are configured
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email task payload should include run_id
    And the email task payload should include recipient
    And the email task payload should include subject
    And the email task payload should include body

  @notifications @celery @retry
  Scenario: Failed email delivery is retried
    Given email notifications are configured
    And email delivery is temporarily failing
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then the email task should be retried
    And the retry count should be incremented

  # =============================================================================
  # Notification Configuration
  # =============================================================================

  @notifications @config
  Scenario: Configure notification recipients via API
    When I configure notification settings with:
      | field       | value               |
      | recipients  | team@example.com    |
      | on_success  | true                |
      | on_failure  | true                |
    Then the response status code should be 200
    And the notification settings should be saved

  @notifications @config
  Scenario: Configure notification to send only on failure
    When I configure notification settings with:
      | field       | value               |
      | recipients  | team@example.com    |
      | on_success  | false               |
      | on_failure  | true                |
    Then the response status code should be 200
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then no email notification should be queued

  @notifications @config
  Scenario: Multiple recipients receive notification
    When I configure notification settings with:
      | field       | value                           |
      | recipients  | dev@example.com,qa@example.com  |
      | on_success  | true                            |
    When I trigger a test run with tags "phase1" on environment "test-environment"
    And the run completes successfully
    Then email notifications should be queued for all recipients

  # =============================================================================
  # Error Cases
  # =============================================================================

  @notifications @error
  Scenario: Invalid email address is rejected
    When I configure notification settings with:
      | field       | value               |
      | recipients  | not-an-email        |
    Then the response status code should be 400
    And the error should indicate "invalid email"

  @notifications @error
  Scenario: Empty recipients list is rejected
    When I configure notification settings with:
      | field       | value  |
      | recipients  |        |
    Then the response status code should be 400
    And the error should indicate "recipients required"
