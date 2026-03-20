@phase7 @scheduling @frontend @ui
Feature: Run Scheduling - Create, Manage, and Execute Scheduled Test Runs
  As a Sliples user
  I want to schedule test runs using cron expressions
  So that tests run automatically at specified times without manual intervention

  Background:
    Given I am logged in as "test.user@example.com"
    And I have a valid API key

  # =============================================================================
  # Schedule List - Viewing Schedules
  # =============================================================================

  @schedule-list @critical
  Scenario: View list of schedules on the Schedules page
    Given there are existing schedules in the system
    When I navigate to the schedules page
    Then I should see "Schedules"
    And the "schedules-list" should be visible
    And I should see at least one schedule in the list

  @schedule-list @display
  Scenario: See schedule name, cron expression, and next run time
    Given there is a schedule named "Nightly Regression" with cron "0 2 * * *"
    When I navigate to the schedules page
    Then I should see "Nightly Regression" in the schedules list
    And I should see the cron expression "0 2 * * *" displayed
    And I should see the next run time displayed

  @schedule-list @display @last-run
  Scenario: See last run timestamp for a schedule
    Given there is a schedule named "Daily Smoke Tests" that has run before
    And the last run was at "2026-03-19T10:00:00Z"
    When I navigate to the schedules page
    Then I should see "Daily Smoke Tests" in the schedules list
    And I should see the last run timestamp
    And the last run should show "March 19, 2026" or similar format

  @schedule-list @display @status
  Scenario: See enabled/disabled status for each schedule
    Given there is an enabled schedule named "Active Tests"
    And there is a disabled schedule named "Paused Tests"
    When I navigate to the schedules page
    Then the schedule "Active Tests" should show as enabled
    And the schedule "Paused Tests" should show as disabled

  @schedule-list @empty-state
  Scenario: Empty state when no schedules exist
    Given there are no schedules in the system
    When I navigate to the schedules page
    Then I should see "No schedules yet"
    And I should see "Create your first schedule to automate test runs"
    And the "create-schedule-btn" should be visible

  @schedule-list @filter @status
  Scenario: Filter schedules by enabled status
    Given there are both enabled and disabled schedules
    When I navigate to the schedules page
    And I filter schedules by status "enabled"
    Then I should only see enabled schedules in the list
    And disabled schedules should not be visible

  @schedule-list @filter @status
  Scenario: Filter schedules by disabled status
    Given there are both enabled and disabled schedules
    When I navigate to the schedules page
    And I filter schedules by status "disabled"
    Then I should only see disabled schedules in the list
    And enabled schedules should not be visible

  # =============================================================================
  # Create Schedule - Form and Workflow
  # =============================================================================

  @create-schedule @critical
  Scenario: Open create schedule form
    Given I am on the schedules page
    When I click the "Create Schedule" button
    Then the "create-schedule-modal" should be visible
    And I should see "Create New Schedule"
    And the "schedule-name-input" should be visible
    And the "cron-builder" should be visible

  @create-schedule @name
  Scenario: Enter schedule name
    Given the create schedule modal is open
    When I enter "My Nightly Tests" into the "schedule-name-input" field
    Then the "schedule-name-input" should have value "My Nightly Tests"

  @create-schedule @cron @preset
  Scenario: Select hourly cron preset
    Given the create schedule modal is open
    When I select the "hourly" cron preset
    Then the cron expression should be "0 * * * *"
    And the human-readable preview should show "Every hour"

  @create-schedule @cron @preset
  Scenario: Select daily cron preset
    Given the create schedule modal is open
    When I select the "daily" cron preset
    Then the cron expression should be "0 0 * * *"
    And the human-readable preview should show "Every day at midnight"

  @create-schedule @cron @preset
  Scenario: Select weekly cron preset
    Given the create schedule modal is open
    When I select the "weekly" cron preset
    Then the cron expression should be "0 0 * * 0"
    And the human-readable preview should show "Every Sunday at midnight"

  @create-schedule @cron @custom
  Scenario: Enter custom cron expression
    Given the create schedule modal is open
    When I select the "custom" cron mode
    And I enter "30 14 * * 1-5" into the "cron-expression-input" field
    Then the cron expression should be "30 14 * * 1-5"
    And the human-readable preview should show "At 2:30 PM, Monday through Friday"

  @create-schedule @scenarios @tags
  Scenario: Select scenarios by tag
    Given the create schedule modal is open
    And there are scenarios with tag "smoke"
    When I select the "By Tag" scenario selection mode
    And I enter "smoke" into the "tag-selector" field
    Then the selected tag "smoke" should be visible
    And the scenario count should update

  @create-schedule @scenarios @individual
  Scenario: Select individual scenarios
    Given the create schedule modal is open
    And there are multiple scenarios available
    When I select the "Individual" scenario selection mode
    And I check the scenario "Login flow works correctly"
    And I check the scenario "Homepage loads successfully"
    Then 2 scenarios should be selected

  @create-schedule @environment @critical
  Scenario: Select environment for scheduled run
    Given the create schedule modal is open
    And there are environments "test-environment" and "staging-environment"
    When I select "test-environment" from the environment dropdown
    Then the environment "test-environment" should be selected

  @create-schedule @browsers
  Scenario: Select browsers for scheduled run
    Given the create schedule modal is open
    When I check the browser "chrome"
    And I check the browser "firefox"
    Then browsers "chrome" and "firefox" should be selected
    And the browser selection should show "2 browsers"

  @create-schedule @validation @cron
  Scenario: Validation error for invalid cron expression
    Given the create schedule modal is open
    When I select the "custom" cron mode
    And I enter "invalid cron" into the "cron-expression-input" field
    Then I should see "Invalid cron expression"
    And the "create-btn" should be disabled

  @create-schedule @validation @name
  Scenario: Validation error for empty schedule name
    Given the create schedule modal is open
    When I leave the "schedule-name-input" field empty
    And I click the "Create" button
    Then I should see "Schedule name is required"
    And the "create-schedule-modal" should still be visible

  @create-schedule @success @critical
  Scenario: Successfully create a new schedule
    Given the create schedule modal is open
    When I enter "New CI Schedule" into the "schedule-name-input" field
    And I select the "daily" cron preset
    And I select scenarios with tag "smoke"
    And I select "test-environment" from the environment dropdown
    And I check the browser "chrome"
    And I click the "Create" button
    Then I should see "Schedule created successfully"
    And the "create-schedule-modal" should not be visible
    And I should see "New CI Schedule" in the schedules list

  # =============================================================================
  # Cron Builder - Interactive Cron Configuration
  # =============================================================================

  @cron-builder @preset @hourly
  Scenario: Cron builder hourly preset configures correct expression
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Hourly" preset button
    Then the cron expression should be "0 * * * *"
    And the minute field should be "0"
    And the hour field should be "*"

  @cron-builder @preset @daily
  Scenario: Cron builder daily preset with time selection
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Daily" preset button
    And I set the time to "08:30"
    Then the cron expression should be "30 8 * * *"
    And the human-readable preview should show "Every day at 8:30 AM"

  @cron-builder @preset @weekly
  Scenario: Cron builder weekly preset with day selection
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Weekly" preset button
    And I select "Monday" as the day of week
    And I set the time to "09:00"
    Then the cron expression should be "0 9 * * 1"
    And the human-readable preview should show "Every Monday at 9:00 AM"

  @cron-builder @preset @monthly
  Scenario: Cron builder monthly preset with day of month
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Monthly" preset button
    And I select day "15" of the month
    And I set the time to "06:00"
    Then the cron expression should be "0 6 15 * *"
    And the human-readable preview should show "At 6:00 AM, on day 15 of the month"

  @cron-builder @custom @fields
  Scenario: Custom mode shows all 5 cron fields
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Custom" mode button
    Then the "cron-minute-field" should be visible
    And the "cron-hour-field" should be visible
    And the "cron-day-field" should be visible
    And the "cron-month-field" should be visible
    And the "cron-weekday-field" should be visible

  @cron-builder @preview
  Scenario: Human-readable preview updates as expression changes
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Custom" mode button
    And I set the minute field to "0"
    And I set the hour field to "*/2"
    And I set the day field to "*"
    And I set the month field to "*"
    And I set the weekday field to "*"
    Then the cron expression should be "0 */2 * * *"
    And the human-readable preview should show "At minute 0 past every 2nd hour"

  @cron-builder @validation @error
  Scenario: Invalid cron expression shows error in builder
    Given the create schedule modal is open
    And the cron builder is visible
    When I click the "Custom" mode button
    And I set the minute field to "60"
    Then I should see "Invalid minute value"
    And the cron builder should highlight the error field

  @cron-builder @reset
  Scenario: Reset to preset clears custom configuration
    Given the create schedule modal is open
    And the cron builder is visible
    And I have entered a custom cron expression "15 10 5 * *"
    When I click the "Daily" preset button
    Then the cron expression should be "0 0 * * *"
    And the custom fields should be cleared
    And the human-readable preview should show "Every day at midnight"

  # =============================================================================
  # Edit Schedule - Modifying Existing Schedules
  # =============================================================================

  @edit-schedule @critical
  Scenario: Open schedule for editing
    Given there is a schedule named "Existing Schedule"
    And I am on the schedules page
    When I click the edit button for schedule "Existing Schedule"
    Then the "edit-schedule-modal" should be visible
    And I should see "Edit Schedule"
    And the "schedule-name-input" should have value "Existing Schedule"

  @edit-schedule @name
  Scenario: Update schedule name
    Given I am editing the schedule "Old Name"
    When I clear the "schedule-name-input" field
    And I enter "New Name" into the "schedule-name-input" field
    And I click the "Save" button
    Then I should see "Schedule updated successfully"
    And I should see "New Name" in the schedules list
    And I should not see "Old Name" in the schedules list

  @edit-schedule @cron
  Scenario: Update cron expression
    Given I am editing the schedule "Update Cron Test"
    And the current cron is "0 0 * * *"
    When I select the "weekly" cron preset
    Then the cron expression should be "0 0 * * 0"
    When I click the "Save" button
    Then I should see "Schedule updated successfully"

  @edit-schedule @scenarios
  Scenario: Update scenarios selection
    Given I am editing the schedule "Update Scenarios Test"
    And the schedule has tag "smoke" selected
    When I remove the tag "smoke"
    And I add the tag "regression"
    And I click the "Save" button
    Then I should see "Schedule updated successfully"
    And the schedule should have tag "regression"

  @edit-schedule @save @critical
  Scenario: Save changes persists all updates
    Given I am editing the schedule "Full Update Test"
    When I enter "Renamed Schedule" into the "schedule-name-input" field
    And I select the "hourly" cron preset
    And I select "staging-environment" from the environment dropdown
    And I click the "Save" button
    Then I should see "Schedule updated successfully"
    And the schedule "Renamed Schedule" should have cron "0 * * * *"
    And the schedule "Renamed Schedule" should use environment "staging-environment"

  @edit-schedule @cancel
  Scenario: Cancel editing discards changes
    Given I am editing the schedule "Cancel Test"
    When I enter "Changed Name" into the "schedule-name-input" field
    And I click the "Cancel" button
    Then the "edit-schedule-modal" should not be visible
    And I should see "Cancel Test" in the schedules list
    And I should not see "Changed Name" in the schedules list

  # =============================================================================
  # Enable/Disable Schedule
  # =============================================================================

  @enable-disable @disable @critical
  Scenario: Disable an active schedule
    Given there is an enabled schedule named "Active Schedule"
    And I am on the schedules page
    When I click the toggle for schedule "Active Schedule"
    Then the schedule "Active Schedule" should show as disabled
    And I should see "Schedule disabled"

  @enable-disable @enable @critical
  Scenario: Enable a disabled schedule
    Given there is a disabled schedule named "Paused Schedule"
    And I am on the schedules page
    When I click the toggle for schedule "Paused Schedule"
    Then the schedule "Paused Schedule" should show as enabled
    And I should see "Schedule enabled"

  @enable-disable @display
  Scenario: Disabled schedule shows visual indicator
    Given there is a disabled schedule named "Inactive Tests"
    When I navigate to the schedules page
    Then the schedule "Inactive Tests" should have a disabled badge
    And the schedule row should have muted styling

  @enable-disable @no-run
  Scenario: Disabled schedule will not trigger runs
    Given there is a disabled schedule named "Skipped Tests" with cron "* * * * *"
    And the schedule is due to run
    When the scheduler checks for pending runs
    Then no run should be triggered for "Skipped Tests"
    And the schedule should remain in disabled state

  # =============================================================================
  # Delete Schedule
  # =============================================================================

  @delete-schedule @confirm @critical
  Scenario: Delete schedule shows confirmation dialog
    Given there is a schedule named "Delete Me"
    And I am on the schedules page
    When I click the delete button for schedule "Delete Me"
    Then the "delete-confirmation-modal" should be visible
    And I should see "Are you sure you want to delete this schedule?"
    And I should see "This action cannot be undone"

  @delete-schedule @cancel
  Scenario: Cancel delete keeps the schedule
    Given there is a schedule named "Keep This"
    And I am on the schedules page
    And the delete confirmation modal is open for "Keep This"
    When I click the "Cancel" button in the confirmation modal
    Then the "delete-confirmation-modal" should not be visible
    And I should see "Keep This" in the schedules list

  @delete-schedule @success @critical
  Scenario: Confirm delete removes the schedule
    Given there is a schedule named "Delete Confirmed"
    And I am on the schedules page
    And the delete confirmation modal is open for "Delete Confirmed"
    When I click the "Delete" button in the confirmation modal
    Then I should see "Schedule deleted successfully"
    And I should not see "Delete Confirmed" in the schedules list

  @delete-schedule @running
  Scenario: Cannot delete schedule with active run
    Given there is a schedule named "Running Schedule"
    And the schedule has an active run in progress
    And I am on the schedules page
    When I click the delete button for schedule "Running Schedule"
    Then I should see "Cannot delete schedule with active run"
    And I should see "Wait for the run to complete or cancel it first"
    And the schedule "Running Schedule" should still exist

  # =============================================================================
  # Backend API - Schedule Endpoints
  # =============================================================================

  @api @get @critical
  Scenario: GET /schedules returns all schedules
    Given there are 3 schedules in the system
    When I send a GET request to "/api/v1/schedules"
    Then the response status code should be 200
    And the response should be a JSON array
    And the response should contain 3 schedules
    And each schedule should have fields "id, name, cron_expression, enabled, next_run_at"

  @api @post @critical
  Scenario: POST /schedules creates a new schedule
    When I send a POST request to "/api/v1/schedules" with body:
      """
      {
        "name": "API Created Schedule",
        "cron_expression": "0 6 * * *",
        "scenario_tags": ["smoke"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "enabled": true
      }
      """
    Then the response status code should be 201
    And the JSON field "id" should be a valid UUID
    And the JSON field "name" should equal "API Created Schedule"
    And the JSON field "cron_expression" should equal "0 6 * * *"
    And the JSON field "next_run_at" should not be empty

  @api @put @critical
  Scenario: PUT /schedules/{id} updates a schedule
    Given there is a schedule with id "schedule-123"
    When I send a PUT request to "/api/v1/schedules/schedule-123" with body:
      """
      {
        "name": "Updated Schedule Name",
        "cron_expression": "0 12 * * *"
      }
      """
    Then the response status code should be 200
    And the JSON field "name" should equal "Updated Schedule Name"
    And the JSON field "cron_expression" should equal "0 12 * * *"

  @api @delete @critical
  Scenario: DELETE /schedules/{id} removes a schedule
    Given there is a schedule with id "schedule-to-delete"
    When I send a DELETE request to "/api/v1/schedules/schedule-to-delete"
    Then the response status code should be 204
    When I send a GET request to "/api/v1/schedules/schedule-to-delete"
    Then the response status code should be 404

  @api @next-run
  Scenario: Next run time is calculated correctly from cron
    When I send a POST request to "/api/v1/schedules" with body:
      """
      {
        "name": "Next Run Test",
        "cron_expression": "0 0 * * *",
        "scenario_tags": ["smoke"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "enabled": true
      }
      """
    Then the response status code should be 201
    And the JSON field "next_run_at" should be a valid ISO timestamp
    And the next run time should be within 24 hours

  @api @validation @cron
  Scenario: Invalid cron expression returns validation error
    When I send a POST request to "/api/v1/schedules" with body:
      """
      {
        "name": "Invalid Cron Schedule",
        "cron_expression": "not-a-cron",
        "scenario_tags": ["smoke"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "enabled": true
      }
      """
    Then the response status code should be 422
    And the response body should contain "Invalid cron expression"

  @api @validation @name
  Scenario: Duplicate schedule name returns conflict error
    Given there is a schedule named "Existing Name"
    When I send a POST request to "/api/v1/schedules" with body:
      """
      {
        "name": "Existing Name",
        "cron_expression": "0 0 * * *",
        "scenario_tags": ["smoke"],
        "environment": "test-environment",
        "browsers": ["chrome"],
        "enabled": true
      }
      """
    Then the response status code should be 409
    And the response body should contain "Schedule with this name already exists"

  @api @auth
  Scenario: Unauthorized access to schedules is rejected
    Given I have no API key configured
    When I send a GET request to "/api/v1/schedules" without authentication
    Then the response status code should be 401

  # =============================================================================
  # Schedule Execution
  # =============================================================================

  @execution @trigger
  Scenario: Schedule triggers run at specified time
    Given there is an enabled schedule named "Trigger Test" with cron "* * * * *"
    When the scheduler processes due schedules
    Then a test run should be created for "Trigger Test"
    And the run should have status "queued"
    And the schedule "Trigger Test" should update its last_run_at

  @execution @history
  Scenario: View run history for a schedule
    Given there is a schedule named "History Test" with multiple past runs
    When I click on the schedule "History Test"
    Then I should see the run history section
    And I should see at least 3 past runs
    And each run should show status and timestamp
