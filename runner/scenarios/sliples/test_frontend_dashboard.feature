@phase4 @frontend @ui
Feature: Dashboard and Repositories UI
  As a Sliples user
  I want to view the dashboard and manage repositories through the UI
  So that I can monitor test status and organize scenario sources

  # =============================================================================
  # Dashboard - Summary Statistics
  # =============================================================================

  @dashboard @critical
  Scenario: View dashboard with summary statistics
    Given I am on the "dashboard" page
    When I wait for the page to load
    Then I should see "Dashboard"
    And the "total-scenarios-card" should be visible
    And the "total-repos-card" should be visible
    And the "recent-runs-card" should be visible
    And the "pass-rate-card" should be visible

  @dashboard @statistics
  Scenario: Dashboard shows correct total scenarios count
    Given I am on the "dashboard" page
    And there are 25 scenarios in the system
    When I wait for the page to load
    Then the dashboard should show 25 total scenarios

  @dashboard @statistics
  Scenario: Dashboard shows correct repository count
    Given I am on the "dashboard" page
    And there are 3 repositories in the system
    When I wait for the page to load
    Then the dashboard should show 3 total repositories

  # =============================================================================
  # Dashboard - Recent Test Runs
  # =============================================================================

  @dashboard @runs @critical
  Scenario: See recent test runs with status
    Given I am on the "dashboard" page
    And at least one test run exists
    When I wait for the page to load
    Then the "recent-runs-list" should be visible
    And I should see the run status badge
    And I should see the run timestamp

  @dashboard @runs
  Scenario: Recent runs show passed status correctly
    Given I am on the "dashboard" page
    And a test run with status "passed" exists
    When I wait for the page to load
    Then I should see the status badge "passed" in the recent runs

  @dashboard @runs
  Scenario: Recent runs show failed status correctly
    Given I am on the "dashboard" page
    And a test run with status "failed" exists
    When I wait for the page to load
    Then I should see the status badge "failed" in the recent runs

  @dashboard @runs
  Scenario: Recent runs show running status correctly
    Given I am on the "dashboard" page
    And a test run with status "running" exists
    When I wait for the page to load
    Then I should see the status badge "running" in the recent runs

  @dashboard @runs
  Scenario: Navigate to test run details from dashboard
    Given I am on the "dashboard" page
    And at least one test run exists
    When I click on a recent run in the list
    Then I should be on the "runs" page
    And the URL should contain "/runs/"

  # =============================================================================
  # Dashboard - Quick Actions
  # =============================================================================

  @dashboard @actions @critical
  Scenario: Click Run All Tests quick action
    Given I am on the "dashboard" page
    And at least one scenario exists
    When I click the "Run All Tests" button
    Then I should see "Test run started"
    And a new test run should be queued

  @dashboard @actions @critical
  Scenario: Click Sync All Repos quick action
    Given I am on the "dashboard" page
    And at least one repository exists
    When I click the "Sync All Repos" button
    Then I should see "Sync started"
    And repository sync should be initiated

  @dashboard @actions
  Scenario: Run All Tests button is disabled when no scenarios exist
    Given I am on the "dashboard" page
    And no scenarios exist
    When I wait for the page to load
    Then the "run-all-tests-btn" should be disabled

  @dashboard @actions
  Scenario: Sync All Repos button is disabled when no repos exist
    Given I am on the "dashboard" page
    And no repositories exist
    When I wait for the page to load
    Then the "sync-all-repos-btn" should be disabled

  # =============================================================================
  # Dashboard - Trend Chart
  # =============================================================================

  @dashboard @chart
  Scenario: See pass/fail trend chart
    Given I am on the "dashboard" page
    And there is test run history data
    When I wait for the page to load
    Then the "trend-chart" should be visible
    And the chart should show pass and fail data

  @dashboard @chart
  Scenario: Trend chart updates time range
    Given I am on the "dashboard" page
    And there is test run history data
    When I select "Last 7 days" from "chart-timerange"
    Then the chart should update with filtered data

  @dashboard @chart
  Scenario: Empty trend chart shows message
    Given I am on the "dashboard" page
    And no test run history exists
    When I wait for the page to load
    Then I should see "No test runs yet"

  # =============================================================================
  # Dashboard - Real-time Updates
  # =============================================================================

  @dashboard @realtime
  Scenario: Dashboard updates after new test run completes
    Given I am on the "dashboard" page
    And I note the current pass rate
    When a test run completes successfully
    And I wait for 2 seconds
    Then the pass rate should be updated
    And the recent runs list should show the new run

  @dashboard @realtime
  Scenario: Dashboard shows notification when run fails
    Given I am on the "dashboard" page
    When a test run completes with failure
    Then I should see a notification "Test run failed"

  # =============================================================================
  # Repositories Page - List View
  # =============================================================================

  @repos @list @critical
  Scenario: View list of repositories
    Given I am on the "repos" page
    And at least one repository exists
    When I wait for the page to load
    Then the "repos-list" should be visible
    And I should see the repository name
    And I should see the repository URL

  @repos @list
  Scenario: Repositories list shows scenario count per repository
    Given I am on the "repos" page
    And a repository with 15 scenarios exists
    When I wait for the page to load
    Then I should see "15 scenarios" for the repository

  @repos @list
  Scenario: Repositories list shows last sync timestamp
    Given I am on the "repos" page
    And a repository that was synced recently exists
    When I wait for the page to load
    Then I should see the last sync timestamp

  @repos @list
  Scenario: Empty repositories page shows message
    Given I am on the "repos" page
    And no repositories exist
    When I wait for the page to load
    Then I should see "No repositories added yet"
    And I should see "Add Repository"

  # =============================================================================
  # Repositories Page - Add Repository
  # =============================================================================

  @repos @add @critical
  Scenario: Add a new repository with valid git URL
    Given I am on the "repos" page
    When I click the "Add Repository" button
    Then the "add-repo-modal" should be visible
    When I fill the repo form with name "my-test-repo"
    And I fill the repo form with url "https://github.com/example/test-scenarios.git"
    And I click the "Save" button
    Then I should see "Repository added successfully"
    And I should see "my-test-repo" in the repos list

  @repos @add
  Scenario: Add repository with custom branch
    Given I am on the "repos" page
    When I click the "Add Repository" button
    And I fill the repo form with name "custom-branch-repo"
    And I fill the repo form with url "https://github.com/example/tests.git"
    And I fill the repo form with branch "develop"
    And I click the "Save" button
    Then I should see "Repository added successfully"
    And the repository should have branch "develop"

  @repos @add
  Scenario: Add repository with custom sync path
    Given I am on the "repos" page
    When I click the "Add Repository" button
    And I fill the repo form with name "custom-path-repo"
    And I fill the repo form with url "https://github.com/example/tests.git"
    And I fill the repo form with sync path "tests/e2e"
    And I click the "Save" button
    Then I should see "Repository added successfully"

  @repos @add @validation
  Scenario: Add repository with invalid git URL shows validation error
    Given I am on the "repos" page
    When I click the "Add Repository" button
    And I fill the repo form with name "invalid-url-repo"
    And I fill the repo form with url "not-a-valid-url"
    And I click the "Save" button
    Then I should see "Invalid git URL"
    And the "add-repo-modal" should be visible

  @repos @add @validation
  Scenario: Add repository with empty name shows validation error
    Given I am on the "repos" page
    When I click the "Add Repository" button
    And I fill the repo form with url "https://github.com/example/tests.git"
    And I click the "Save" button
    Then I should see "Name is required"
    And the "add-repo-modal" should be visible

  @repos @add @validation
  Scenario: Add repository with duplicate name shows error
    Given I am on the "repos" page
    And a repository with name "existing-repo" exists
    When I click the "Add Repository" button
    And I fill the repo form with name "existing-repo"
    And I fill the repo form with url "https://github.com/other/tests.git"
    And I click the "Save" button
    Then I should see "Repository with this name already exists"

  @repos @add
  Scenario: Cancel adding a repository
    Given I am on the "repos" page
    When I click the "Add Repository" button
    And I fill the repo form with name "cancelled-repo"
    And I click the "Cancel" button
    Then the "add-repo-modal" should not be visible
    And I should not see "cancelled-repo" in the repos list

  # =============================================================================
  # Repositories Page - Sync Repository
  # =============================================================================

  @repos @sync @critical
  Scenario: Sync a single repository
    Given I am on the "repos" page
    And a repository with name "sync-me-repo" exists
    When I click the sync button for repository "sync-me-repo"
    Then I should see "Sync started"
    And the sync status should show "syncing"

  @repos @sync
  Scenario: Sync shows progress indicator
    Given I am on the "repos" page
    And a repository is currently syncing
    When I wait for the page to load
    Then I should see the sync progress spinner

  @repos @sync
  Scenario: Sync updates scenario count on completion
    Given I am on the "repos" page
    And a repository with name "count-update-repo" exists
    When I click the sync button for repository "count-update-repo"
    And the sync completes successfully
    Then the scenario count should be updated

  @repos @sync
  Scenario: Sync failure shows error message
    Given I am on the "repos" page
    And a repository with invalid credentials exists
    When I click the sync button for the repository
    Then I should see "Sync failed"
    And the error details should be visible

  # =============================================================================
  # Repositories Page - Delete Repository
  # =============================================================================

  @repos @delete @critical
  Scenario: Delete a repository with confirmation
    Given I am on the "repos" page
    And a repository with name "delete-me-repo" exists
    When I click the delete button for repository "delete-me-repo"
    Then the "confirm-delete-modal" should be visible
    And I should see "Are you sure you want to delete"
    When I click the "Delete" button
    Then I should see "Repository deleted successfully"
    And I should not see "delete-me-repo" in the repos list

  @repos @delete
  Scenario: Cancel delete confirmation
    Given I am on the "repos" page
    And a repository with name "keep-me-repo" exists
    When I click the delete button for repository "keep-me-repo"
    Then the "confirm-delete-modal" should be visible
    When I click the "Cancel" button
    Then the "confirm-delete-modal" should not be visible
    And I should see "keep-me-repo" in the repos list

  @repos @delete
  Scenario: Delete warns about associated scenarios
    Given I am on the "repos" page
    And a repository with 10 scenarios exists
    When I click the delete button for the repository
    Then the "confirm-delete-modal" should be visible
    And I should see "This will also delete 10 scenarios"

  # =============================================================================
  # Repositories Page - Edit Repository
  # =============================================================================

  @repos @edit
  Scenario: Edit repository name
    Given I am on the "repos" page
    And a repository with name "edit-me-repo" exists
    When I click the edit button for repository "edit-me-repo"
    And I clear the "name" field
    And I enter "renamed-repo" into the "name" field
    And I click the "Save" button
    Then I should see "Repository updated successfully"
    And I should see "renamed-repo" in the repos list

  @repos @edit
  Scenario: Edit repository branch
    Given I am on the "repos" page
    And a repository with name "branch-edit-repo" exists
    When I click the edit button for repository "branch-edit-repo"
    And I clear the "branch" field
    And I enter "feature/new-tests" into the "branch" field
    And I click the "Save" button
    Then I should see "Repository updated successfully"

  # =============================================================================
  # Navigation Between Dashboard and Repos
  # =============================================================================

  @navigation @dashboard @repos
  Scenario: Navigate from dashboard to repos page
    Given I am on the "dashboard" page
    When I click the link "Repositories"
    Then I should be on the "repos" page

  @navigation @dashboard @repos
  Scenario: Navigate from repos to dashboard
    Given I am on the "repos" page
    When I click the link "Dashboard"
    Then I should be on the "dashboard" page

  @navigation @dashboard
  Scenario: Dashboard link in sidebar is highlighted when active
    Given I am on the "dashboard" page
    Then the "dashboard-nav-link" should have class "active"

  @navigation @repos
  Scenario: Repos link in sidebar is highlighted when active
    Given I am on the "repos" page
    Then the "repos-nav-link" should have class "active"
