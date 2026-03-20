@phase5 @interactive @testmode @ui
Feature: Interactive Test Mode (TEST Mode)
  As a Sliples user
  I want to run test scenarios interactively in a headed browser
  So that I can debug, explore, and develop test scenarios step by step

  Background:
    Given I am on the Sliples application
    And I am authenticated

  # =============================================================================
  # Start Session - Configuration and Launch
  # =============================================================================

  @interactive @session @start @critical
  Scenario: Start interactive test session
    Given I am on the "scenarios" page
    When I click the "Interactive Mode" button
    Then I should see the interactive mode setup panel
    And I should see options for scenario selection
    And I should see options for environment selection
    And I should see options for browser selection

  @interactive @session @scenario
  Scenario: Select scenario for interactive session
    Given I am on the interactive mode setup panel
    When I select scenario "User login workflow" from the list
    Then the scenario should be highlighted as selected
    And I should see the scenario steps preview
    And the "Start Session" button should become enabled

  @interactive @session @environment
  Scenario: Select environment for interactive session
    Given I am on the interactive mode setup panel
    When I select "test-environment" from "environment-select"
    Then the environment should be confirmed as selected
    And environment variables should be loaded
    And the base URL should be displayed

  @interactive @session @browser @critical
  Scenario: Select browser type for interactive session
    Given I am on the interactive mode setup panel
    When I select "Chrome" from "browser-select"
    Then Chrome should be selected for the session
    And browser options should be displayed
    And I should see the "headed mode" toggle enabled by default

  @interactive @session @browser @firefox
  Scenario: Select Firefox browser for interactive session
    Given I am on the interactive mode setup panel
    When I select "Firefox" from "browser-select"
    Then Firefox should be selected for the session
    And I should see Firefox-specific options if available

  @interactive @session @browser @webkit
  Scenario: Select WebKit browser for interactive session
    Given I am on the interactive mode setup panel
    When I select "WebKit" from "browser-select"
    Then WebKit should be selected for the session
    And a warning about WebKit limitations may be shown

  @interactive @session @active @critical
  Scenario: Session shows as active after launch
    Given I have configured an interactive session
    When I click the "Start Session" button
    Then I should see the "Launching browser..." status
    And after the browser launches I should see "Session Active" indicator
    And the session timer should start
    And I should see the interactive control panel

  @interactive @session @headed
  Scenario: Browser launches in headed mode
    Given I have configured an interactive session
    When I click the "Start Session" button
    And the browser launches
    Then a visible browser window should open
    And the browser should navigate to the environment base URL
    And I should see the browser preview in the control panel

  @interactive @session @timeout
  Scenario: Session timeout after inactivity
    Given I have an active interactive session
    When I remain inactive for 30 minutes
    Then I should see a "Session timeout warning" notification
    And I should have option to "Extend Session" or "End Session"
    When I do not respond within 5 minutes
    Then the session should end automatically
    And the browser should close

  @interactive @session @multiple @error
  Scenario: Cannot start multiple concurrent sessions
    Given I have an active interactive session
    When I try to start another interactive session
    Then I should see an error message "You already have an active session"
    And I should see option to "End Current Session" or "View Current Session"

  @interactive @session @validation
  Scenario: Cannot start session without required selections
    Given I am on the interactive mode setup panel
    And I have not selected a scenario
    When I click the "Start Session" button
    Then I should see validation error "Please select a scenario"
    And the session should not start

  # =============================================================================
  # Step Execution - Running Steps Interactively
  # =============================================================================

  @interactive @step @execute @critical
  Scenario: Execute single step
    Given I have an active interactive session
    And I see the list of scenario steps
    When I click the "Execute" button on step "Given I am on the login page"
    Then the step should show "Running..." status
    And the browser should perform the step action
    And the step status should update when complete

  @interactive @step @pass @critical
  Scenario: Step passes with green indicator
    Given I have an active interactive session
    When I execute a step that completes successfully
    Then the step should show a green checkmark indicator
    And the step row should have green highlighting
    And the step duration should be displayed
    And the "Passed" badge should appear next to the step

  @interactive @step @fail @critical
  Scenario: Step fails with red indicator
    Given I have an active interactive session
    When I execute a step that fails
    Then the step should show a red X indicator
    And the step row should have red highlighting
    And the error message should be displayed
    And a screenshot should be captured automatically

  @interactive @step @skip
  Scenario: Skip a step during execution
    Given I have an active interactive session
    And I see the list of scenario steps
    When I click the "Skip" button on a step
    Then the step should show "Skipped" status with gray indicator
    And I should be able to continue to the next step
    And the skipped step should be marked in the execution summary

  @interactive @step @retry @critical
  Scenario: Retry failed step
    Given I have an active interactive session
    And a step has failed
    When I click the "Retry" button on the failed step
    Then the step should re-execute
    And the previous error should be cleared
    And the new result should replace the old result

  @interactive @step @screenshot @critical
  Scenario: See step screenshot after execution
    Given I have an active interactive session
    When I execute a step
    And the step completes
    Then I should see a screenshot thumbnail next to the step
    And I can click the thumbnail to view full-size screenshot
    And the screenshot should show the browser state after step execution

  @interactive @step @edit
  Scenario: Edit step before execution
    Given I have an active interactive session
    And I see a step in the list
    When I click the "Edit" button on the step
    Then I should see an inline editor with the step text
    And I can modify the step parameters
    When I save the changes
    Then the step should update with my modifications
    And I can execute the modified step

  @interactive @step @pause
  Scenario: Pause execution during multi-step run
    Given I have an active interactive session
    And I am running steps in sequence
    When I click the "Pause" button
    Then the execution should pause after the current step completes
    And I should see "Execution Paused" status
    And the "Resume" button should appear

  @interactive @step @resume
  Scenario: Resume paused execution
    Given I have an active interactive session
    And execution is paused
    When I click the "Resume" button
    Then execution should continue from the next step
    And the "Pause" button should reappear
    And I should see "Running..." status

  @interactive @step @logs
  Scenario: View step logs during execution
    Given I have an active interactive session
    When I click the "Logs" tab in the control panel
    Then I should see the execution logs panel
    And logs should show real-time output
    And I can filter logs by level (info, debug, error)
    And I can search within logs

  @interactive @step @runall
  Scenario: Run all remaining steps
    Given I have an active interactive session
    And I have executed some steps
    When I click the "Run All Remaining" button
    Then all unexecuted steps should run in sequence
    And I should see progress indicator
    And I can pause at any time

  @interactive @step @runfrom
  Scenario: Run from specific step
    Given I have an active interactive session
    When I right-click on a step in the middle of the scenario
    And I select "Run from here"
    Then execution should start from that step
    And continue through remaining steps

  # =============================================================================
  # Screenshot Controls - Capture and Manage Screenshots
  # =============================================================================

  @interactive @screenshot @manual @critical
  Scenario: Take manual screenshot
    Given I have an active interactive session
    When I click the "Take Screenshot" button
    Then a screenshot should be captured immediately
    And I should see a "Screenshot captured" notification
    And the screenshot should appear in the gallery

  @interactive @screenshot @gallery
  Scenario: Screenshot saved to gallery
    Given I have an active interactive session
    And I have taken multiple screenshots
    When I click the "Gallery" tab
    Then I should see all captured screenshots
    And screenshots should be displayed in chronological order
    And each screenshot should show capture timestamp
    And each screenshot should show the step context if applicable

  @interactive @screenshot @download @critical
  Scenario: Download screenshot
    Given I have an active interactive session
    And I have a screenshot in the gallery
    When I click the "Download" button on a screenshot
    Then the screenshot should be downloaded as a PNG file
    And the filename should include timestamp and session ID

  @interactive @screenshot @compare
  Scenario: Compare screenshots side by side
    Given I have an active interactive session
    And I have multiple screenshots in the gallery
    When I select two screenshots for comparison
    And I click the "Compare" button
    Then I should see a side-by-side comparison view
    And I should see a diff overlay highlighting differences
    And I can toggle between overlay and side-by-side modes

  @interactive @screenshot @auto @critical
  Scenario: Auto-screenshot on step completion
    Given I have an active interactive session
    And the "Auto-screenshot" toggle is enabled
    When I execute a step
    And the step completes
    Then a screenshot should be automatically captured
    And the screenshot should be associated with the step

  @interactive @screenshot @annotate
  Scenario: Screenshot annotations
    Given I have an active interactive session
    And I have a screenshot open in full view
    When I click the "Annotate" button
    Then I should see annotation tools
    And I can draw rectangles to highlight areas
    And I can add text labels
    And I can add arrows pointing to elements
    When I save the annotation
    Then the annotated screenshot should be saved separately

  # =============================================================================
  # Session Management - Control and Monitor Sessions
  # =============================================================================

  @interactive @management @status @critical
  Scenario: View active session status
    Given I have an active interactive session
    Then I should see the session status panel
    And the panel should show session duration
    And the panel should show steps executed count
    And the panel should show steps passed/failed count
    And the panel should show memory usage indicator

  @interactive @management @end @critical
  Scenario: End session manually
    Given I have an active interactive session
    When I click the "End Session" button
    Then I should see a confirmation dialog
    When I confirm the action
    Then the browser should close
    And the session should end
    And I should see the session summary with results
    And I should have option to save the session log

  @interactive @management @cleanup
  Scenario: Session cleanup on browser close
    Given I have an active interactive session
    When the browser window is closed unexpectedly
    Then the session should detect the browser closure
    And the session should end automatically
    And a notification should appear "Browser closed - Session ended"
    And session data should be preserved

  @interactive @management @resume
  Scenario: Resume interrupted session
    Given I had an active session that was interrupted
    When I navigate back to interactive mode
    Then I should see "Previous session found" notification
    And I should have option to "Resume Session" or "Start New"
    When I click "Resume Session"
    Then the previous session state should be restored
    And the browser should reopen
    And I should continue from where I left off

  @interactive @management @history
  Scenario: View session history
    Given I have completed previous interactive sessions
    When I click "Session History" in the interactive mode menu
    Then I should see a list of past sessions
    And each session should show date, duration, and scenario
    And each session should show pass/fail status
    And I can click a session to view its details and screenshots

  @interactive @management @share
  Scenario: Share session with team member
    Given I have an active interactive session
    When I click the "Share Session" button
    Then I should see sharing options
    And I can generate a view-only link
    And I can invite a team member by email
    When I share with a team member
    Then they should receive a notification
    And they can view the live browser preview (read-only)

  # =============================================================================
  # Browser Preview - Live View and Controls
  # =============================================================================

  @interactive @preview @live @critical
  Scenario: Live browser preview updates
    Given I have an active interactive session
    And the browser preview panel is visible
    When the browser page changes
    Then the preview should update in real-time
    And there should be minimal delay (under 500ms)
    And the preview should reflect current page state

  @interactive @preview @current @critical
  Scenario: Preview shows current page
    Given I have an active interactive session
    When I look at the browser preview panel
    Then I should see a rendered view of the current page
    And the page URL should be displayed above the preview
    And the page title should be shown

  @interactive @preview @zoom
  Scenario: Zoom in/out on preview
    Given I have an active interactive session
    And the browser preview panel is visible
    When I click the "Zoom In" button
    Then the preview should zoom in
    And I should see more detail
    When I click the "Zoom Out" button
    Then the preview should zoom out
    And I should see more of the page
    And zoom level should be displayed

  @interactive @preview @fullscreen @critical
  Scenario: Full-screen preview mode
    Given I have an active interactive session
    When I click the "Fullscreen Preview" button
    Then the browser preview should expand to full screen
    And I should still see basic controls
    When I press Escape or click "Exit Fullscreen"
    Then the preview should return to normal size

  @interactive @preview @interact
  Scenario: Interact directly with preview
    Given I have an active interactive session
    And the preview has "Direct Interaction" mode enabled
    When I click on an element in the preview
    Then the click should be sent to the actual browser
    And the page should respond to the interaction
    And the preview should update

  @interactive @preview @devtools
  Scenario: Open browser DevTools
    Given I have an active interactive session
    When I click the "DevTools" button
    Then browser DevTools should open
    And I can inspect elements
    And I can view console output
    And I can debug JavaScript

  # =============================================================================
  # Additional Interactive Features
  # =============================================================================

  @interactive @locator @finder
  Scenario: Element locator finder tool
    Given I have an active interactive session
    When I click the "Find Locator" button
    Then I should enter locator discovery mode
    And when I hover over elements in the preview they should highlight
    When I click an element
    Then suggested locators should be displayed
    And I can copy the best locator to clipboard
    And I can test the locator immediately

  @interactive @record @steps
  Scenario: Record new steps from browser actions
    Given I have an active interactive session
    When I click the "Record" button
    Then recording mode should start
    And I should see "Recording..." indicator
    When I interact with the browser
    Then my actions should be recorded as new steps
    When I stop recording
    Then the new steps should appear in the scenario

  @interactive @variable @inspect
  Scenario: Inspect and modify test variables
    Given I have an active interactive session
    When I click the "Variables" tab
    Then I should see all current test variables
    And I can modify variable values
    And I can add new variables
    And changes should take effect immediately

  @interactive @step @conditional
  Scenario: Add conditional breakpoint
    Given I have an active interactive session
    When I right-click on a step
    And I select "Add Breakpoint"
    Then a breakpoint indicator should appear on the step
    And I can set a condition for the breakpoint
    When the step is reached and condition is met
    Then execution should pause automatically

  @interactive @network @monitor
  Scenario: Monitor network requests
    Given I have an active interactive session
    When I click the "Network" tab
    Then I should see all network requests made by the browser
    And I can filter requests by type (XHR, Fetch, Document, etc.)
    And I can view request and response details
    And I can mock or block specific requests

  @interactive @console @output
  Scenario: View browser console output
    Given I have an active interactive session
    When I click the "Console" tab
    Then I should see browser console output
    And errors should be highlighted in red
    And warnings should be highlighted in yellow
    And I can execute JavaScript commands

