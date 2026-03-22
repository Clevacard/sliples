# Sliples Acceptance Tests
# ========================
# These scenarios are designed to test Sliples using Sliples itself (dogfooding).
# Run these tests against your own Sliples instance to verify each phase is complete.
#
# Usage: Configure Sliples to test its own deployment by setting:
#   - Environment base_url to your Sliples instance URL
#   - API credentials for the Sliples API
#
# Organization: Scenarios are grouped by implementation phase/epic.

# =============================================================================
# EPIC: Phase 1 - Foundation
# =============================================================================

@phase1 @foundation @infrastructure
Feature: Phase 1 - Foundation Infrastructure
  As a Sliples administrator
  I want the core infrastructure to be operational
  So that the platform has a stable base for development

  @health @api @critical
  Scenario: AC1.1 - Backend health endpoint returns healthy status
    Given I have a valid API endpoint configured
    When I send a GET request to "/api/v1/health"
    Then the response status code should be 200
    And the response body should contain "status"
    And the JSON field "status" should equal "healthy"

  @health @api
  Scenario: AC1.2 - Health endpoint includes database connectivity status
    Given I have a valid API endpoint configured
    When I send a GET request to "/api/v1/health"
    Then the response status code should be 200
    And the JSON field "database" should equal "connected"

  @health @api
  Scenario: AC1.3 - Health endpoint includes Redis connectivity status
    Given I have a valid API endpoint configured
    When I send a GET request to "/api/v1/health"
    Then the response status code should be 200
    And the JSON field "redis" should equal "connected"

  @frontend @ui @critical
  Scenario: AC1.4 - Frontend application loads without errors
    Given I navigate to the Sliples home page
    When the page finishes loading
    Then I should not see any JavaScript console errors
    And I should see the "Sliples" logo or title
    And the page should load within 5 seconds

  @frontend @ui
  Scenario: AC1.5 - Frontend routing works for all main pages
    Given I navigate to the Sliples home page
    When I click on "Dashboard" in the navigation
    Then I should be on the "/dashboard" page
    When I click on "Test Runs" in the navigation
    Then I should be on the "/runs" page
    When I click on "Environments" in the navigation
    Then I should be on the "/environments" page
    When I click on "Settings" in the navigation
    Then I should be on the "/settings" page

  @database @migrations @critical
  Scenario: AC1.6 - Database migrations run successfully
    Given I have access to the database
    When I check the alembic version history
    Then all migrations should be applied
    And there should be no pending migrations

  @docker @infrastructure
  Scenario: AC1.7 - All Docker containers are running
    Given I have access to the Docker environment
    When I list all running containers for Sliples
    Then the "sliples-backend" container should be running
    And the "sliples-frontend" container should be running
    And the "sliples-postgres" container should be running
    And the "sliples-redis" container should be running

# =============================================================================
# EPIC: Phase 2 - Core API
# =============================================================================

@phase2 @core-api @authentication
Feature: Phase 2 - Core API and Authentication
  As an API consumer
  I want secure and functional API endpoints
  So that I can integrate Sliples with my CI/CD pipeline

  @authentication @api @critical
  Scenario: AC2.1 - Valid API key authenticates successfully
    Given I have a valid API key
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 200
    And I should receive a valid JSON response

  @authentication @api @security
  Scenario: AC2.2 - Invalid API key is rejected
    Given I have an invalid API key "invalid-key-12345"
    When I send a GET request to "/api/v1/scenarios" with the API key header
    Then the response status code should be 401
    And the response body should contain "Unauthorized"

  @authentication @api @security
  Scenario: AC2.3 - Missing API key is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/scenarios" without authentication
    Then the response status code should be 401
    And the response body should contain "API key required"

  @environments @api @crud
  Scenario: AC2.4 - Create a new environment
    Given I have a valid API key
    When I send a POST request to "/api/v1/environments" with body:
      """
      {
        "name": "acceptance-test-env",
        "base_url": "https://test.example.com",
        "variables": {"timeout": "30"}
      }
      """
    Then the response status code should be 201
    And the JSON field "name" should equal "acceptance-test-env"
    And the JSON field "id" should be a valid UUID

  @environments @api @crud
  Scenario: AC2.5 - List all environments
    Given I have a valid API key
    And at least one environment exists
    When I send a GET request to "/api/v1/environments"
    Then the response status code should be 200
    And the response should be a JSON array
    And each item should have fields "id", "name", "base_url"

  @environments @api @crud
  Scenario: AC2.6 - Update an existing environment
    Given I have a valid API key
    And an environment with name "acceptance-test-env" exists
    When I send a PUT request to "/api/v1/environments/{id}" with body:
      """
      {
        "name": "acceptance-test-env-updated",
        "base_url": "https://updated.example.com"
      }
      """
    Then the response status code should be 200
    And the JSON field "name" should equal "acceptance-test-env-updated"

  @scenarios @api
  Scenario: AC2.7 - List all test scenarios
    Given I have a valid API key
    When I send a GET request to "/api/v1/scenarios"
    Then the response status code should be 200
    And the response should be a JSON array

  @scenarios @api
  Scenario: AC2.8 - Sync scenarios from filesystem
    Given I have a valid API key
    And feature files exist in the scenarios directory
    When I send a POST request to "/api/v1/scenarios/sync"
    Then the response status code should be 200
    And the response should contain "synced_count"
    And the JSON field "synced_count" should be greater than 0

  @runs @api @critical
  Scenario: AC2.9 - Trigger a test run via API
    Given I have a valid API key
    And at least one scenario exists
    And at least one environment exists
    When I send a POST request to "/api/v1/runs" with body:
      """
      {
        "scenario_tags": ["phase1"],
        "environment": "acceptance-test-env",
        "browsers": ["chrome"]
      }
      """
    Then the response status code should be 202
    And the JSON field "id" should be a valid UUID
    And the JSON field "status" should equal "queued"

  @celery @infrastructure
  Scenario: AC2.10 - Celery worker is processing tasks
    Given I have a valid API key
    And I have triggered a test run
    When I wait for up to 30 seconds
    And I send a GET request to "/api/v1/runs/{run_id}"
    Then the JSON field "status" should not equal "queued"

# =============================================================================
# EPIC: Phase 3 - Test Runner
# =============================================================================

@phase3 @test-runner @playwright
Feature: Phase 3 - Test Runner with Playwright
  As a QA engineer
  I want tests to execute in real browsers
  So that I can validate web application behavior

  @playwright @execution @critical
  Scenario: AC3.1 - Simple navigation test executes successfully
    Given I have a valid API key
    And a scenario exists with tag "simple-navigation"
    And an environment "test-env" is configured with base_url "https://example.com"
    When I trigger a test run for tag "simple-navigation" on "test-env"
    And I wait for the run to complete with timeout 120 seconds
    Then the run status should be "passed" or "failed"
    And the run should have at least one test result

  @playwright @screenshots @critical
  Scenario: AC3.2 - Screenshots are captured on test failure
    Given I have a valid API key
    And a scenario exists that is designed to fail
    When I trigger a test run for the failing scenario
    And I wait for the run to complete with timeout 120 seconds
    Then the run status should be "failed"
    And the test results should include screenshot URLs
    And the screenshot URLs should be accessible

  @playwright @screenshots
  Scenario: AC3.3 - Screenshots are uploaded to S3/MinIO
    Given I have a valid API key
    And a test run has completed with screenshots
    When I retrieve the screenshot URL from the test results
    Then the URL should point to S3 or MinIO storage
    And I should be able to download the screenshot image

  @playwright @browsers
  Scenario: AC3.4 - Tests can run on Chrome browser
    Given I have a valid API key
    And a simple test scenario exists
    When I trigger a test run with browser "chrome"
    And I wait for the run to complete with timeout 120 seconds
    Then the run should complete without infrastructure errors
    And the test results should indicate browser "chrome"

  @playwright @browsers
  Scenario: AC3.5 - Tests can run on Firefox browser
    Given I have a valid API key
    And a simple test scenario exists
    When I trigger a test run with browser "firefox"
    And I wait for the run to complete with timeout 120 seconds
    Then the run should complete without infrastructure errors
    And the test results should indicate browser "firefox"

  @step-definitions @gherkin
  Scenario: AC3.6 - Navigation step definitions work correctly
    Given I have a valid API key
    And a scenario using navigation steps exists:
      """
      Given I navigate to "https://example.com"
      Then I should see "Example Domain"
      """
    When I trigger a test run for this scenario
    And I wait for the run to complete with timeout 120 seconds
    Then all steps should pass

  @step-definitions @gherkin
  Scenario: AC3.7 - Form interaction step definitions work correctly
    Given I have a valid API key
    And a scenario using form steps exists:
      """
      Given I navigate to "https://httpbin.org/forms/post"
      When I enter "Test User" into the "custname" field
      And I click the "submit" button
      Then I should see "Test User"
      """
    When I trigger a test run for this scenario
    And I wait for the run to complete with timeout 120 seconds
    Then the test should complete without step definition errors

  @test-results @reporting
  Scenario: AC3.8 - Test results are stored with step-level detail
    Given I have a valid API key
    And a test run has completed
    When I send a GET request to "/api/v1/runs/{run_id}"
    Then the response should include "results" array
    And each result should have "step_name", "status", "duration_ms"

  @parallel @concurrency
  Scenario: AC3.9 - Multiple scenarios can run in parallel
    Given I have a valid API key
    And at least 3 test scenarios exist
    When I trigger test runs for all 3 scenarios simultaneously
    And I wait for all runs to complete with timeout 180 seconds
    Then all runs should complete successfully
    And the total execution time should be less than 3x single run time

# =============================================================================
# EPIC: Phase 4 - Frontend
# =============================================================================

@phase4 @frontend @ui
Feature: Phase 4 - Frontend User Interface
  As a Sliples user
  I want a functional web interface
  So that I can manage tests without using the API directly

  @dashboard @ui @critical
  Scenario: AC4.1 - Dashboard displays recent test runs
    Given I navigate to the Sliples dashboard
    And at least one test run has been executed
    When the dashboard page loads
    Then I should see a list of recent test runs
    And each run should display status, timestamp, and scenario name

  @dashboard @ui
  Scenario: AC4.2 - Dashboard shows pass/fail statistics
    Given I navigate to the Sliples dashboard
    And at least 5 test runs have been executed
    When the dashboard page loads
    Then I should see pass/fail rate statistics
    And the statistics should include a visual chart or graph

  @editor @ui @critical
  Scenario: AC4.3 - Scenario editor loads with syntax highlighting
    Given I navigate to the Sliples scenario editor page
    When I select a feature file to edit
    Then I should see the Monaco editor component
    And Gherkin keywords should be syntax highlighted
    And the editor should display line numbers

  @editor @ui
  Scenario: AC4.4 - Scenario editor saves changes
    Given I navigate to the Sliples scenario editor page
    And I have selected a feature file
    When I modify the scenario content
    And I click the "Save" button
    Then I should see a success notification
    And the changes should persist after page reload

  @runs @ui @critical
  Scenario: AC4.5 - Test runs page allows triggering new runs
    Given I navigate to the Sliples test runs page
    When I click on "New Test Run" button
    Then I should see a form to configure the test run
    And I should be able to select scenarios by tag
    And I should be able to select target environment
    And I should be able to select browser type

  @runs @ui
  Scenario: AC4.6 - Test runs can be filtered and searched
    Given I navigate to the Sliples test runs page
    And at least 10 test runs exist
    When I filter by status "failed"
    Then I should only see test runs with failed status
    When I search for a specific scenario name
    Then I should only see matching test runs

  @run-details @ui @critical
  Scenario: AC4.7 - Run details page shows step-by-step results
    Given I navigate to a completed test run details page
    When the page loads
    Then I should see each test step listed
    And each step should show pass/fail status
    And each step should show execution duration
    And failed steps should be visually highlighted

  @run-details @ui
  Scenario: AC4.8 - Run details page displays screenshots
    Given I navigate to a test run details page with screenshots
    When the page loads
    Then I should see thumbnail images for captured screenshots
    When I click on a screenshot thumbnail
    Then I should see the full-size screenshot image

  @environments @ui
  Scenario: AC4.9 - Environments page allows CRUD operations
    Given I navigate to the Sliples environments page
    When I click "Add Environment"
    And I fill in environment details
    And I click "Save"
    Then the new environment should appear in the list
    When I click "Edit" on the environment
    And I modify the base URL
    And I click "Save"
    Then the updated URL should be displayed

  @settings @ui
  Scenario: AC4.10 - Settings page allows API key management
    Given I navigate to the Sliples settings page
    When I click on "API Keys" section
    Then I should see existing API keys (masked)
    When I click "Generate New Key"
    Then I should see a new API key displayed
    And I should be warned to copy it as it won't be shown again

# =============================================================================
# EPIC: Phase 5 - Notifications & Reports
# =============================================================================

@phase5 @notifications @reports
Feature: Phase 5 - Notifications and Reports
  As a Sliples user
  I want to receive notifications and view reports
  So that I can monitor test results without constant manual checking

  @reports @html @critical
  Scenario: AC5.1 - HTML report is generated for completed runs
    Given I have a valid API key
    And a test run has completed
    When I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the response status code should be 200
    And the content-type should be "text/html"
    And the HTML should contain test scenario details
    And the HTML should contain pass/fail summary

  @reports @html
  Scenario: AC5.2 - HTML report includes embedded screenshots
    Given I have a valid API key
    And a test run with screenshots has completed
    When I send a GET request to "/api/v1/runs/{run_id}/report"
    Then the HTML report should contain image elements
    And the images should be displayable (valid src URLs)

  @reports @download
  Scenario: AC5.3 - HTML report can be downloaded from UI
    Given I navigate to a completed test run details page
    When I click the "Download Report" button
    Then an HTML file should be downloaded
    And the file should open correctly in a browser

  @email @notifications @critical
  Scenario: AC5.4 - Email notification is sent on test completion
    Given I have a valid API key
    And email notifications are configured
    And I have configured a notification email address
    When I trigger a test run
    And the test run completes
    Then an email should be sent to the configured address
    And the email should contain the run status
    And the email should contain a link to the report

  @email @notifications
  Scenario: AC5.5 - Email notification includes failure details
    Given I have a valid API key
    And email notifications are configured
    When I trigger a test run that will fail
    And the test run completes with failures
    Then the email notification should list failed steps
    And the email should include error messages

  @websocket @realtime @critical
  Scenario: AC5.6 - WebSocket provides real-time run updates
    Given I have established a WebSocket connection to Sliples
    And I am subscribed to run updates
    When a test run is triggered
    Then I should receive a WebSocket message when the run starts
    And I should receive messages as each step completes
    And I should receive a final message when the run finishes

  @websocket @ui
  Scenario: AC5.7 - UI updates in real-time during test execution
    Given I navigate to the Sliples test runs page
    And I have triggered a test run
    When the test run is executing
    Then the run status should update without page refresh
    And I should see step progress indicators updating

  @reports @storage
  Scenario: AC5.8 - Reports are stored in PostgreSQL
    Given I have a valid API key
    And multiple test runs have completed
    When I query the database for test run reports
    Then each completed run should have a stored HTML report
    And reports should be retrievable by run ID

# =============================================================================
# EPIC: Phase 6 - OpenShift Deployment
# =============================================================================

@phase6 @openshift @deployment
Feature: Phase 6 - OpenShift Deployment
  As a DevOps engineer
  I want Sliples deployed on OpenShift
  So that we have a production-ready, scalable platform

  @openshift @manifests
  Scenario: AC6.1 - OpenShift manifests are valid
    Given I have access to the OpenShift CLI
    When I validate all YAML manifests in the openshift directory
    Then all manifests should pass validation
    And there should be no syntax errors

  @openshift @deployment @critical
  Scenario: AC6.2 - All deployments are running in OpenShift
    Given I am logged into the OpenShift cluster
    And the Sliples namespace exists
    When I check the deployment status
    Then "sliples-backend" deployment should have ready replicas
    And "sliples-frontend" deployment should have ready replicas
    And "sliples-worker" deployment should have ready replicas

  @openshift @secrets @security
  Scenario: AC6.3 - Secrets are properly configured
    Given I am logged into the OpenShift cluster
    When I check the secrets in the Sliples namespace
    Then "sliples-db-credentials" secret should exist
    And "sliples-s3-credentials" secret should exist
    And "sliples-smtp-credentials" secret should exist
    And secret values should not be visible in deployment logs

  @openshift @routes @critical
  Scenario: AC6.4 - Routes are accessible externally
    Given I am logged into the OpenShift cluster
    When I check the routes in the Sliples namespace
    Then the frontend route should be accessible via HTTPS
    And the API route should be accessible via HTTPS
    And both routes should have valid TLS certificates

  @openshift @scaling
  Scenario: AC6.5 - Worker pods can scale horizontally
    Given I am logged into the OpenShift cluster
    And the Sliples worker deployment exists
    When I scale the worker deployment to 5 replicas
    Then 5 worker pods should become ready within 120 seconds
    When I scale back to 3 replicas
    Then exactly 3 worker pods should be running

  @openshift @persistence
  Scenario: AC6.6 - PostgreSQL data persists across restarts
    Given I am logged into the OpenShift cluster
    And the PostgreSQL pod is running
    When I create a test record in the database
    And I restart the PostgreSQL pod
    And the pod becomes ready again
    Then the test record should still exist

  @cicd @integration @critical
  Scenario: AC6.7 - CI/CD pipeline can trigger tests via API
    Given the Sliples API is accessible from CI/CD environment
    And a valid API key is configured in CI/CD secrets
    When the CI/CD pipeline sends a test trigger request
    Then the request should be accepted with status 202
    And the pipeline should be able to poll for results
    And the final status should be retrievable

  @openshift @resources
  Scenario: AC6.8 - Resource limits are properly configured
    Given I am logged into the OpenShift cluster
    When I check the resource specifications for all deployments
    Then each deployment should have CPU limits defined
    And each deployment should have memory limits defined
    And the PostgreSQL PVC should have at least 10Gi allocated

# =============================================================================
# EPIC: Phase 7 - Polish & Documentation
# =============================================================================

@phase7 @polish @documentation
Feature: Phase 7 - Polish and Documentation
  As a Sliples user or developer
  I want comprehensive documentation and a polished experience
  So that I can effectively use and maintain the platform

  @api-docs @openapi @critical
  Scenario: AC7.1 - OpenAPI documentation is available
    Given I have access to the Sliples API
    When I send a GET request to "/docs" or "/openapi.json"
    Then I should receive valid OpenAPI documentation
    And all endpoints should be documented
    And request/response schemas should be defined

  @api-docs @swagger
  Scenario: AC7.2 - Swagger UI is accessible
    Given I navigate to the Sliples API documentation URL
    When the Swagger UI loads
    Then I should see all API endpoints listed
    And I should be able to test endpoints interactively
    And authentication should be configurable in the UI

  @user-guide @documentation
  Scenario: AC7.3 - User guide documentation exists
    Given I navigate to the Sliples documentation
    When I access the user guide section
    Then I should find instructions for creating scenarios
    And I should find instructions for configuring environments
    And I should find instructions for triggering test runs
    And I should find instructions for viewing reports

  @performance @load
  Scenario: AC7.4 - System handles 10 concurrent test scenarios
    Given I have a valid API key
    And at least 10 test scenarios exist
    When I trigger 10 test runs simultaneously
    Then all runs should be queued successfully
    And the system should remain responsive
    And all runs should complete within acceptable time limits

  @performance @response-time
  Scenario: AC7.5 - API response times are acceptable
    Given I have a valid API key
    When I measure response time for GET "/api/v1/health"
    Then the response time should be under 200ms
    When I measure response time for GET "/api/v1/scenarios"
    Then the response time should be under 500ms
    When I measure response time for GET "/api/v1/runs"
    Then the response time should be under 500ms

  @security @review
  Scenario: AC7.6 - Security headers are properly configured
    Given I send a request to the Sliples API
    When I examine the response headers
    Then the "X-Content-Type-Options" header should be "nosniff"
    And the "X-Frame-Options" header should be present
    And the "Strict-Transport-Security" header should be present
    And CORS headers should restrict allowed origins

  @security @input-validation
  Scenario: AC7.7 - Input validation prevents injection attacks
    Given I have a valid API key
    When I send a POST request with malicious payload:
      """
      {
        "name": "<script>alert('xss')</script>",
        "base_url": "'; DROP TABLE environments; --"
      }
      """
    Then the request should be rejected or sanitized
    And no script execution should occur
    And the database should remain intact

  @error-handling @ux
  Scenario: AC7.8 - Error messages are user-friendly
    Given I have a valid API key
    When I send a request with invalid data
    Then the error response should be in JSON format
    And the error should include a human-readable message
    And the error should include the field that caused the issue

# =============================================================================
# DOGFOODING: Self-Test Scenarios
# =============================================================================

@dogfooding @meta @self-test
Feature: Dogfooding - Sliples Testing Sliples
  As the Sliples development team
  I want Sliples to test itself
  So that we validate the platform with real-world usage

  @dogfooding @critical
  Scenario: AC-DOG-1 - Sliples can load its own acceptance tests
    Given Sliples is running and configured
    When I sync scenarios from the sliples repository
    Then the "sliples-acceptance.feature" file should be recognized
    And scenarios should be parsed without errors
    And all tags should be extractable

  @dogfooding @critical
  Scenario: AC-DOG-2 - Sliples can execute tests against itself
    Given Sliples is running and configured
    And an environment "sliples-self-test" points to the Sliples instance
    When I trigger a test run with tag "health" against "sliples-self-test"
    And I wait for the run to complete
    Then the health check scenarios should pass

  @dogfooding
  Scenario: AC-DOG-3 - Sliples UI tests pass when run by Sliples
    Given Sliples is running and configured
    And an environment "sliples-self-test" points to the Sliples frontend
    When I trigger a test run with tag "frontend" against "sliples-self-test"
    And I wait for the run to complete
    Then the frontend scenarios should execute
    And screenshots of Sliples UI should be captured

  @dogfooding @regression
  Scenario: AC-DOG-4 - Full regression suite can run nightly
    Given Sliples is running and configured
    And a scheduled job is configured for nightly runs
    When the nightly trigger fires
    Then all acceptance tests should be executed
    And a summary report should be generated
    And notification should be sent with results

  @dogfooding @ci
  Scenario: AC-DOG-5 - PR validation uses Sliples to test changes
    Given a pull request is opened on the Sliples repository
    When the CI pipeline triggers
    Then Sliples should execute smoke tests against the PR branch
    And the PR should be blocked if critical tests fail
    And test results should be posted as PR comments
