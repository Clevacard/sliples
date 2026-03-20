@phase4 @frontend @ui
Feature: Frontend Test Runs, Run Details, and Scenarios Pages
  As a Sliples user
  I want to manage test runs and view scenarios through the web interface
  So that I can trigger, monitor, and analyze test executions visually

  Background:
    Given I am on the Sliples application
    And I am authenticated

  # =============================================================================
  # Test Runs Page - List View
  # =============================================================================

  @testruns @list @critical
  Scenario: View list of test runs
    Given I am on the "runs" page
    When the page finishes loading
    Then I should see the test runs list
    And each test run should display status, browser, and timestamp
    And the "test-runs-list" should be visible

  @testruns @list
  Scenario: Test runs list shows run metadata
    Given I am on the "runs" page
    And at least one test run exists in the system
    When the page finishes loading
    Then I should see the run status indicator
    And I should see the environment name for each run
    And I should see the execution duration for completed runs

  @testruns @list @empty
  Scenario: Empty state when no test runs exist
    Given I am on the "runs" page
    And no test runs exist in the system
    When the page finishes loading
    Then I should see "No test runs found"
    And I should see a "Create New Run" call-to-action button

  # =============================================================================
  # Test Runs Page - Filtering
  # =============================================================================

  @testruns @filter @status @critical
  Scenario: Filter test runs by passed status
    Given I am on the "runs" page
    And test runs with various statuses exist
    When I select "Passed" from "status-filter"
    Then I should only see test runs with passed status
    And the URL should contain "status=passed"

  @testruns @filter @status
  Scenario: Filter test runs by failed status
    Given I am on the "runs" page
    And test runs with various statuses exist
    When I select "Failed" from "status-filter"
    Then I should only see test runs with failed status
    And the URL should contain "status=failed"

  @testruns @filter @status
  Scenario: Filter test runs by running status
    Given I am on the "runs" page
    And a test run is currently running
    When I select "Running" from "status-filter"
    Then I should only see test runs with running status
    And the run should show a progress indicator

  @testruns @filter @status
  Scenario: Filter test runs by queued status
    Given I am on the "runs" page
    When I select "Queued" from "status-filter"
    Then I should only see test runs with queued status

  @testruns @filter @clear
  Scenario: Clear status filter shows all runs
    Given I am on the "runs" page
    And I have filtered by status "failed"
    When I click the "Clear Filters" button
    Then I should see test runs with all statuses
    And the URL should not contain "status="

  @testruns @filter @environment
  Scenario: Filter test runs by environment
    Given I am on the "runs" page
    And test runs exist for multiple environments
    When I select "test-environment" from "environment-filter"
    Then I should only see test runs for the selected environment

  # =============================================================================
  # Test Runs Page - Create New Run Modal
  # =============================================================================

  @testruns @create @modal @critical
  Scenario: Open new test run modal
    Given I am on the "runs" page
    When I click the "New Test Run" button
    Then I should see the new test run modal
    And the modal should display tag selection
    And the modal should display environment selection
    And the modal should display browser selection

  @testruns @create @tags @critical
  Scenario: Select scenarios by tag for new run
    Given I am on the "runs" page
    And I open the new test run modal
    When I click on tag "smoke"
    Then the tag "smoke" should be selected
    And the selected scenarios count should update
    When I click on tag "regression"
    Then both tags should be selected
    And the selected scenarios count should increase

  @testruns @create @tags
  Scenario: Deselect tag removes it from selection
    Given I am on the "runs" page
    And I open the new test run modal
    And I have selected tag "smoke"
    When I click on tag "smoke" again
    Then the tag "smoke" should not be selected
    And the selected scenarios count should decrease

  @testruns @create @environment @critical
  Scenario: Select environment for new run
    Given I am on the "runs" page
    And I open the new test run modal
    When I select "staging" from "environment-select"
    Then the environment "staging" should be selected
    And the environment configuration should be displayed

  @testruns @create @browser @critical
  Scenario: Select browser for new run
    Given I am on the "runs" page
    And I open the new test run modal
    When I check the "chrome" checkbox
    Then Chrome should be selected for the run
    When I check the "firefox" checkbox
    Then both Chrome and Firefox should be selected

  @testruns @create @browser
  Scenario: Select multiple browsers for parallel run
    Given I am on the "runs" page
    And I open the new test run modal
    When I check the "chrome" checkbox
    And I check the "firefox" checkbox
    And I check the "webkit" checkbox
    Then all three browsers should be selected
    And the estimated run time should be displayed

  @testruns @create @submit @critical
  Scenario: Submit new test run
    Given I am on the "runs" page
    And I open the new test run modal
    And I have selected tag "smoke"
    And I have selected environment "test-environment"
    And I have selected browser "chrome"
    When I click the "Start Run" button
    Then the modal should close
    And I should see a success notification "Test run started"
    And the new run should appear in the list with status "queued"

  @testruns @create @validation
  Scenario: Cannot submit run without required fields
    Given I am on the "runs" page
    And I open the new test run modal
    When I click the "Start Run" button without selecting any options
    Then I should see validation error "Please select at least one tag"
    And I should see validation error "Please select an environment"
    And the "Start Run" button should be disabled

  @testruns @create @cancel
  Scenario: Cancel new test run modal
    Given I am on the "runs" page
    And I open the new test run modal
    And I have selected some options
    When I click the "Cancel" button
    Then the modal should close
    And no test run should be created

  # =============================================================================
  # Test Runs Page - Pagination
  # =============================================================================

  @testruns @pagination @critical
  Scenario: Paginate through test runs
    Given I am on the "runs" page
    And more than 20 test runs exist
    When the page finishes loading
    Then I should see the first 20 test runs
    And the pagination controls should be visible
    When I click the "Next" pagination button
    Then I should see the next page of test runs
    And the page number should update

  @testruns @pagination
  Scenario: Navigate to specific page
    Given I am on the "runs" page
    And more than 50 test runs exist
    When I click on page number "3" in pagination
    Then I should see test runs from page 3
    And page "3" should be highlighted in pagination

  @testruns @pagination
  Scenario: Previous page navigation
    Given I am on the "runs" page
    And I am on page 2 of test runs
    When I click the "Previous" pagination button
    Then I should see the first page of test runs
    And page "1" should be highlighted in pagination

  @testruns @pagination @edge
  Scenario: Previous button disabled on first page
    Given I am on the "runs" page
    And I am on the first page
    Then the "Previous" pagination button should be disabled

  @testruns @pagination @edge
  Scenario: Next button disabled on last page
    Given I am on the "runs" page
    And I am on the last page of test runs
    Then the "Next" pagination button should be disabled

  # =============================================================================
  # Test Runs Page - Navigation to Details
  # =============================================================================

  @testruns @navigation @critical
  Scenario: Navigate to run details by clicking on a run
    Given I am on the "runs" page
    And at least one test run exists
    When I click on a test run in the list
    Then I should be on the run details page
    And the URL should contain "/runs/"
    And the URL should contain the run ID

  @testruns @navigation
  Scenario: Navigate to run details via view button
    Given I am on the "runs" page
    And at least one test run exists
    When I click the "View Details" button for a run
    Then I should be on the run details page

  # =============================================================================
  # Run Details Page - Summary View
  # =============================================================================

  @rundetails @summary @critical
  Scenario: View run summary with status and duration
    Given I am on a completed test run details page
    When the page finishes loading
    Then I should see the run status badge
    And I should see the total execution duration
    And I should see the environment name
    And I should see the browser used
    And I should see the timestamp of execution

  @rundetails @summary
  Scenario: Run summary shows scenario count
    Given I am on a completed test run details page
    When the page finishes loading
    Then I should see the total scenarios count
    And I should see the passed scenarios count
    And I should see the failed scenarios count

  @rundetails @summary @tags
  Scenario: Run summary shows tags used
    Given I am on a completed test run details page
    When the page finishes loading
    Then I should see the tags that were used to select scenarios
    And the tags should be displayed as badges

  # =============================================================================
  # Run Details Page - Progress and Status
  # =============================================================================

  @rundetails @progress @critical
  Scenario: See progress bar for running tests
    Given I navigate to a running test run details page
    When the page finishes loading
    Then I should see a progress bar
    And the progress bar should show percentage complete
    And I should see "X of Y scenarios completed"

  @rundetails @progress
  Scenario: Progress bar updates as tests complete
    Given I am on a running test run details page
    And 5 of 10 scenarios have completed
    When another scenario completes
    Then the progress bar should update to show 60%
    And the completed count should show "6 of 10"

  @rundetails @autorefresh @critical
  Scenario: Auto-refresh updates status while running
    Given I am on a running test run details page
    When I wait for 5 seconds
    Then the page should auto-refresh the run status
    And new completed steps should appear
    And the progress should update without full page reload

  @rundetails @autorefresh
  Scenario: Auto-refresh stops when run completes
    Given I am on a running test run details page
    When the test run completes
    Then the auto-refresh should stop
    And I should see the final status badge
    And a completion notification should appear

  @rundetails @status @complete
  Scenario: See final status when run completes successfully
    Given I am on a completed test run details page
    And all scenarios passed
    When the page finishes loading
    Then I should see a "Passed" status badge with green styling
    And the progress bar should show 100%
    And I should see "All scenarios passed"

  @rundetails @status @failed
  Scenario: See final status when run has failures
    Given I am on a completed test run details page
    And some scenarios failed
    When the page finishes loading
    Then I should see a "Failed" status badge with red styling
    And I should see the failure count prominently
    And failed scenarios should be highlighted

  # =============================================================================
  # Run Details Page - Step Results
  # =============================================================================

  @rundetails @steps @critical
  Scenario: View step-by-step results
    Given I am on a completed test run details page
    When the page finishes loading
    Then I should see a list of all executed steps
    And each step should show its status (passed/failed/skipped)
    And each step should show its execution time

  @rundetails @steps
  Scenario: Steps are grouped by scenario
    Given I am on a completed test run details page
    When the page finishes loading
    Then I should see steps organized by scenario name
    And each scenario group should be collapsible
    And the scenario header should show pass/fail status

  @rundetails @steps @expand @critical
  Scenario: Expand step to see details
    Given I am on a completed test run details page
    And I see a list of steps
    When I click on a step to expand it
    Then I should see the step details panel
    And the details should include the Gherkin step text
    And the details should include the execution duration
    And the details should include any step data

  @rundetails @steps @failed
  Scenario: Failed step shows error message
    Given I am on a completed test run details page with failures
    When I expand a failed step
    Then I should see the error message
    And I should see the stack trace if available
    And the error should be syntax highlighted

  @rundetails @steps @navigation
  Scenario: Navigate between failed steps
    Given I am on a completed test run details page with multiple failures
    When I click "Next Failed" button
    Then I should jump to the next failed step
    And the step should auto-expand
    When I click "Previous Failed" button
    Then I should jump back to the previous failed step

  # =============================================================================
  # Run Details Page - Screenshots
  # =============================================================================

  @rundetails @screenshot @critical
  Scenario: View screenshot for failed step
    Given I am on a completed test run details page with failures
    And the failed step has a screenshot
    When I expand the failed step
    Then I should see a screenshot thumbnail
    And the thumbnail should be clickable

  @rundetails @screenshot
  Scenario: Open full-size screenshot
    Given I am on a completed test run details page with failures
    And I have expanded a failed step with screenshot
    When I click on the screenshot thumbnail
    Then I should see a full-size screenshot modal
    And the modal should have zoom controls
    And the modal should have a close button

  @rundetails @screenshot
  Scenario: Download screenshot
    Given I am on a screenshot modal
    When I click the "Download" button
    Then the screenshot should be downloaded
    And the filename should include the step name

  @rundetails @screenshot @gallery
  Scenario: View all screenshots in gallery mode
    Given I am on a completed test run details page
    And the run has multiple screenshots
    When I click "View All Screenshots"
    Then I should see a gallery view of all screenshots
    And I should be able to navigate between screenshots
    And each screenshot should show which step it belongs to

  # =============================================================================
  # Run Details Page - Reports
  # =============================================================================

  @rundetails @report @critical
  Scenario: Open HTML report
    Given I am on a completed test run details page
    When I click the "View Report" button
    Then a new tab should open with the HTML report
    And the report should load successfully

  @rundetails @report
  Scenario: Download HTML report
    Given I am on a completed test run details page
    When I click the "Download Report" button
    Then the HTML report should be downloaded
    And the filename should include the run ID and timestamp

  @rundetails @report @not-ready
  Scenario: Report not available for incomplete run
    Given I am on a running test run details page
    When I look for the report button
    Then the "View Report" button should be disabled
    And I should see tooltip "Report available after run completes"

  # =============================================================================
  # Scenarios Page - List View
  # =============================================================================

  @scenarios @list @critical
  Scenario: View list of scenarios
    Given I am on the "scenarios" page
    When the page finishes loading
    Then I should see the scenarios list
    And each scenario should display name and feature path
    And the "scenarios-list" should be visible

  @scenarios @list
  Scenario: Scenarios list shows metadata
    Given I am on the "scenarios" page
    And scenarios exist in the system
    When the page finishes loading
    Then each scenario should show its tags
    And each scenario should show its repository source
    And the total count of scenarios should be displayed

  @scenarios @list @empty
  Scenario: Empty state when no scenarios synced
    Given I am on the "scenarios" page
    And no scenarios are synced
    When the page finishes loading
    Then I should see "No scenarios found"
    And I should see a "Sync Repositories" button

  # =============================================================================
  # Scenarios Page - Filtering
  # =============================================================================

  @scenarios @filter @repo @critical
  Scenario: Filter scenarios by repository
    Given I am on the "scenarios" page
    And scenarios exist from multiple repositories
    When I select "my-test-repo" from "repository-filter"
    Then I should only see scenarios from "my-test-repo"
    And the URL should contain "repo="

  @scenarios @filter @tag @critical
  Scenario: Filter scenarios by tag
    Given I am on the "scenarios" page
    And scenarios with various tags exist
    When I click on the "smoke" tag filter
    Then I should only see scenarios with the "smoke" tag
    And the "smoke" tag should be highlighted as active filter

  @scenarios @filter @tag
  Scenario: Filter by multiple tags
    Given I am on the "scenarios" page
    When I click on the "smoke" tag filter
    And I click on the "api" tag filter
    Then I should see scenarios that have both "smoke" and "api" tags
    And both tags should be highlighted as active filters

  @scenarios @filter @clear
  Scenario: Clear all filters
    Given I am on the "scenarios" page
    And I have active tag and repository filters
    When I click "Clear All Filters"
    Then I should see all scenarios
    And no filters should be highlighted

  # =============================================================================
  # Scenarios Page - Search
  # =============================================================================

  @scenarios @search @critical
  Scenario: Search scenarios by name
    Given I am on the "scenarios" page
    When I enter "login" into the "scenario-search" field
    And I wait for the search results
    Then I should only see scenarios containing "login" in the name
    And the search term should be highlighted in results

  @scenarios @search
  Scenario: Search with no results
    Given I am on the "scenarios" page
    When I enter "xyz123nonexistent" into the "scenario-search" field
    And I wait for the search results
    Then I should see "No scenarios match your search"
    And a "Clear Search" option should be available

  @scenarios @search @debounce
  Scenario: Search has debounce behavior
    Given I am on the "scenarios" page
    When I type "user" quickly into the "scenario-search" field
    Then the search should not trigger for each keystroke
    And the search should trigger after I stop typing

  # =============================================================================
  # Scenarios Page - Details and Tags
  # =============================================================================

  @scenarios @details @critical
  Scenario: View scenario details
    Given I am on the "scenarios" page
    And scenarios exist in the system
    When I click on a scenario card
    Then I should see the scenario details panel
    And I should see the full Gherkin content
    And I should see the feature file path

  @scenarios @details
  Scenario: Scenario details show all steps
    Given I am on the "scenarios" page
    And I have opened a scenario details panel
    Then I should see the Given steps
    And I should see the When steps
    And I should see the Then steps
    And the Gherkin keywords should be highlighted

  @scenarios @tags @critical
  Scenario: See tags on scenario cards
    Given I am on the "scenarios" page
    When the page finishes loading
    Then each scenario card should display its tags as badges
    And clicking a tag badge should filter by that tag

  @scenarios @tags
  Scenario: Tags are color-coded by category
    Given I am on the "scenarios" page
    When the page finishes loading
    Then critical tags should have a distinct color
    And phase tags should have a consistent color
    And feature tags should be visually distinguishable

  # =============================================================================
  # Scenarios Page - Run Actions
  # =============================================================================

  @scenarios @run @quick
  Scenario: Quick run a single scenario
    Given I am on the "scenarios" page
    And I have selected a scenario
    When I click the "Run" button on the scenario card
    Then I should see the quick run modal
    And the scenario should be pre-selected
    And I only need to select environment and browser

  @scenarios @run @batch
  Scenario: Run multiple selected scenarios
    Given I am on the "scenarios" page
    When I check the checkbox on multiple scenario cards
    Then the "Run Selected" button should become enabled
    And I should see a count of selected scenarios
    When I click "Run Selected"
    Then I should see the new test run modal with scenarios pre-selected

  # =============================================================================
  # Cross-Page Navigation
  # =============================================================================

  @navigation @breadcrumbs
  Scenario: Breadcrumb navigation from run details
    Given I am on a test run details page
    Then I should see breadcrumbs showing "Test Runs > Run #123"
    When I click on "Test Runs" in the breadcrumbs
    Then I should be on the "runs" page

  @navigation @back
  Scenario: Back navigation preserves filters
    Given I am on the "runs" page
    And I have filtered by status "failed"
    When I click on a test run
    And I navigate back to the runs page
    Then the "failed" status filter should still be applied
