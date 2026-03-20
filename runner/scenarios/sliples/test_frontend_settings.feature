@phase5 @frontend @ui @settings
Feature: Settings Page - Profile, API Keys, and Preferences
  As a Sliples user
  I want to manage my profile, API keys, and preferences through the Settings page
  So that I can customize my experience and manage secure API access

  # =============================================================================
  # Profile Tab - User Information Display
  # =============================================================================

  @profile @display @critical
  Scenario: View user profile information on Settings page
    Given I am logged in as "test.user@example.com"
    When I navigate to the settings page
    Then I should see "Settings"
    And the "profile-tab" should be visible
    And the "profile-tab" should be active

  @profile @display @avatar
  Scenario: See user avatar from Google profile
    Given I am logged in as "test.user@example.com"
    And the user has a Google profile picture
    When I navigate to the settings page
    Then the "profile-avatar" should be visible
    And the profile avatar should display the user's Google picture
    And the "profile-avatar" should have an image source

  @profile @display @info
  Scenario: See user email and name on profile
    Given I am logged in as "Test User" with email "test.user@example.com"
    When I navigate to the settings page
    Then I should see "test.user@example.com"
    And I should see "Test User"
    And the "profile-email" should be visible
    And the "profile-name" should be visible

  @profile @display @info
  Scenario: See user role on profile
    Given I am logged in as "test.user@example.com" with role "user"
    When I navigate to the settings page
    Then I should see the user role displayed
    And the "profile-role" should be visible

  @profile @display @date
  Scenario: See account creation date on profile
    Given I am logged in as "test.user@example.com"
    And the user account was created on "2026-01-15"
    When I navigate to the settings page
    Then I should see "Member since"
    And the "profile-created-date" should be visible
    And I should see "January 15, 2026" or similar date format

  @profile @display @admin
  Scenario: Admin user sees admin badge on profile
    Given I am logged in as "admin@example.com" with role "admin"
    When I navigate to the settings page
    Then I should see the admin badge
    And the "admin-badge" should be visible
    And the badge should display "Admin"

  @profile @display @user
  Scenario: Regular user sees user badge on profile
    Given I am logged in as "regular.user@example.com" with role "user"
    When I navigate to the settings page
    Then I should see the user badge
    And the "user-badge" should be visible
    And the badge should display "User"

  # =============================================================================
  # API Keys Tab - Viewing Keys
  # =============================================================================

  @apikeys @list @critical
  Scenario: Navigate to API Keys tab and view list
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    When I click on the "API Keys" tab
    Then the "api-keys-tab-content" should be visible
    And I should see "API Keys"
    And the "api-keys-list" should be visible

  @apikeys @list @display
  Scenario: See API key name, prefix, and dates in list
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "CI Pipeline Key"
    When I navigate to the settings page
    And I click on the "API Keys" tab
    Then I should see "CI Pipeline Key" in the API keys list
    And I should see the key prefix starting with "slp_"
    And I should see the key creation date
    And I should see the "last used" information

  @apikeys @list @masked
  Scenario: API key shows as masked in the list
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "My Secret Key"
    When I navigate to the settings page
    And I click on the "API Keys" tab
    Then the API key should display as masked
    And I should see "slp_****" pattern
    And the full key should NOT be visible

  @apikeys @empty
  Scenario: Empty state when user has no API keys
    Given I am logged in as "test.user@example.com"
    And the user has no API keys
    When I navigate to the settings page
    And I click on the "API Keys" tab
    Then I should see "No API keys yet"
    And I should see "Create your first API key to enable CI/CD integration"
    And the "create-api-key-btn" should be visible

  # =============================================================================
  # API Keys Tab - Creating Keys
  # =============================================================================

  @apikeys @create @critical
  Scenario: Create new API key opens modal
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    And I am on the API Keys tab
    When I click the "Create API Key" button
    Then the "create-api-key-modal" should be visible
    And I should see "Create New API Key"
    And the "api-key-name-input" should be visible

  @apikeys @create @input
  Scenario: Enter key name in create modal
    Given I am logged in as "test.user@example.com"
    And the create API key modal is open
    When I enter "My New CI Key" into the "api-key-name-input" field
    And I click the "Create" button
    Then I should see "API key created successfully"
    And the "new-api-key-display" should be visible

  @apikeys @create @display @critical
  Scenario: See full key after creation (shown only once)
    Given I am logged in as "test.user@example.com"
    And I have just created an API key named "Fresh Key"
    Then I should see the full API key displayed
    And I should see "Copy this key now - it won't be shown again"
    And the key should start with "slp_"
    And the "copy-key-btn" should be visible

  @apikeys @create @copy @critical
  Scenario: Copy API key to clipboard after creation
    Given I am logged in as "test.user@example.com"
    And I have just created an API key named "Copy Test Key"
    And the full key is displayed
    When I click the "Copy" button
    Then I should see "Key copied to clipboard"
    And the clipboard should contain the API key

  @apikeys @create @refresh
  Scenario: Key shows as masked after page refresh
    Given I am logged in as "test.user@example.com"
    And I have created an API key named "Refresh Test Key"
    When I refresh the page
    And I click on the "API Keys" tab
    Then the API key "Refresh Test Key" should display as masked
    And the full key should NOT be visible

  @apikeys @create @validation
  Scenario: Cannot create API key with empty name
    Given I am logged in as "test.user@example.com"
    And the create API key modal is open
    When I leave the "api-key-name-input" field empty
    And I click the "Create" button
    Then I should see "Name is required"
    And the "create-api-key-modal" should still be visible

  @apikeys @create @validation @duplicate
  Scenario: Cannot create API key with duplicate name
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "Existing Key"
    And the create API key modal is open
    When I enter "Existing Key" into the "api-key-name-input" field
    And I click the "Create" button
    Then I should see "An API key with this name already exists"
    And the "create-api-key-modal" should still be visible

  # =============================================================================
  # API Keys Tab - Revoking Keys
  # =============================================================================

  @apikeys @revoke @critical
  Scenario: Revoke API key with confirmation dialog
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "Key To Revoke"
    And I am on the API Keys tab
    When I click the revoke button for API key "Key To Revoke"
    Then the "revoke-confirmation-modal" should be visible
    And I should see "Are you sure you want to revoke this key?"
    And I should see "This action cannot be undone"

  @apikeys @revoke @confirm
  Scenario: Confirm revoke deletes the API key
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "Confirmed Revoke"
    And I am on the API Keys tab
    And the revoke confirmation modal is open for "Confirmed Revoke"
    When I click the "Revoke" button in the confirmation modal
    Then I should see "API key revoked successfully"
    And I should not see "Confirmed Revoke" in the API keys list

  @apikeys @revoke @cancel
  Scenario: Cancel revoke confirmation keeps the key
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "Keep This Key"
    And I am on the API Keys tab
    And the revoke confirmation modal is open for "Keep This Key"
    When I click the "Cancel" button in the confirmation modal
    Then the "revoke-confirmation-modal" should not be visible
    And I should see "Keep This Key" in the API keys list

  @apikeys @tracking
  Scenario: API key last_used updates after API call
    Given I am logged in as "test.user@example.com"
    And the user has an API key named "Tracked Key"
    And the API key "Tracked Key" was used just now
    When I navigate to the settings page
    And I click on the "API Keys" tab
    Then the "Tracked Key" should show "Last used: just now" or similar
    And the "last-used" timestamp should be recent

  # =============================================================================
  # Preferences Tab - Theme Settings
  # =============================================================================

  @preferences @theme @critical
  Scenario: Navigate to Preferences tab
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    When I click on the "Preferences" tab
    Then the "preferences-tab-content" should be visible
    And I should see "Preferences"
    And the "theme-toggle" should be visible

  @preferences @theme @toggle
  Scenario: Toggle dark theme to light theme
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And the current theme is "dark"
    When I click the theme toggle
    Then the theme should change to "light"
    And the page should use light theme styling
    And the "theme-toggle" should show "Light" as active

  @preferences @theme @toggle
  Scenario: Toggle light theme to dark theme
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And the current theme is "light"
    When I click the theme toggle
    Then the theme should change to "dark"
    And the page should use dark theme styling
    And the "theme-toggle" should show "Dark" as active

  @preferences @theme @persist @critical
  Scenario: Theme preference persists after page refresh
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And I set the theme to "light"
    When I refresh the page
    Then the theme should still be "light"
    And the page should use light theme styling

  # =============================================================================
  # Preferences Tab - Notification Settings
  # =============================================================================

  @preferences @notifications @email
  Scenario: Toggle email notifications on
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And email notifications are currently off
    When I click the email notifications toggle
    Then email notifications should be enabled
    And the "email-notifications-toggle" should be in the "on" position
    And I should see "Email notifications enabled"

  @preferences @notifications @email
  Scenario: Toggle email notifications off
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And email notifications are currently on
    When I click the email notifications toggle
    Then email notifications should be disabled
    And the "email-notifications-toggle" should be in the "off" position

  @preferences @notifications @browser
  Scenario: Toggle browser notifications on
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And browser notifications are currently off
    When I click the browser notifications toggle
    Then browser notifications should be enabled
    And the "browser-notifications-toggle" should be in the "on" position

  @preferences @notifications @browser
  Scenario: Toggle browser notifications off
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And browser notifications are currently on
    When I click the browser notifications toggle
    Then browser notifications should be disabled
    And the "browser-notifications-toggle" should be in the "off" position

  # =============================================================================
  # Preferences Tab - Persistence and Reset
  # =============================================================================

  @preferences @storage @critical
  Scenario: Preferences are saved to localStorage
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    When I change the theme to "light"
    And I enable email notifications
    Then the preferences should be saved to localStorage
    And localStorage should contain the theme preference
    And localStorage should contain the notification preferences

  @preferences @reset
  Scenario: Reset preferences to defaults
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And I have customized preferences
    When I click the "Reset to Defaults" button
    Then I should see "Preferences reset to defaults"
    And the theme should be "dark"
    And email notifications should be enabled
    And browser notifications should be disabled

  @preferences @reset @confirm
  Scenario: Reset preferences shows confirmation
    Given I am logged in as "test.user@example.com"
    And I am on the Preferences tab
    And I have customized preferences
    When I click the "Reset to Defaults" button
    Then the "reset-confirmation-modal" should be visible
    And I should see "Are you sure you want to reset all preferences?"

  # =============================================================================
  # Settings Page - Tab Navigation
  # =============================================================================

  @navigation @tabs
  Scenario: Navigate between Profile and API Keys tabs
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    And I am on the Profile tab
    When I click on the "API Keys" tab
    Then the "api-keys-tab-content" should be visible
    And the "profile-tab-content" should not be visible

  @navigation @tabs
  Scenario: Navigate between API Keys and Preferences tabs
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    And I am on the API Keys tab
    When I click on the "Preferences" tab
    Then the "preferences-tab-content" should be visible
    And the "api-keys-tab-content" should not be visible

  @navigation @tabs @url
  Scenario: Tab selection persists in URL
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    When I click on the "API Keys" tab
    Then the URL should contain "tab=api-keys"
    When I refresh the page
    Then the "api-keys-tab-content" should be visible

  @navigation @tabs @keyboard
  Scenario: Navigate tabs with keyboard
    Given I am logged in as "test.user@example.com"
    And I am on the settings page
    And the Profile tab is focused
    When I press the "ArrowRight" key
    Then the "API Keys" tab should be focused
    When I press the "Enter" key
    Then the "api-keys-tab-content" should be visible
