@phase4 @frontend @ui @auth
Feature: Google Workspace SSO Authentication Frontend
  As a Sliples user
  I want to authenticate using Google Workspace SSO
  So that I can securely access the application with my organization credentials

  # =============================================================================
  # Login Page - Display and Branding
  # =============================================================================

  @login @display @critical
  Scenario: Login page displays Sign in with Google button
    Given I am not logged in
    When I navigate to the login page
    Then I should see the "Sign in with Google" button
    And the "sign-in-google-btn" should be visible

  @login @display
  Scenario: Login page shows app branding and logo
    Given I am not logged in
    When I navigate to the login page
    Then I should see the Sliples logo
    And I should see "Sliples"
    And the "app-logo" should be visible

  @login @display @theme
  Scenario: Login page uses dark theme
    Given I am not logged in
    When I navigate to the login page
    Then the page should use dark theme styling
    And the "login-container" should have class "dark-theme"

  @login @display
  Scenario: Login page shows welcome message
    Given I am not logged in
    When I navigate to the login page
    Then I should see "Welcome to Sliples"
    And I should see "Sign in with your Google Workspace account"

  # =============================================================================
  # Login Page - Sign In Flow
  # =============================================================================

  @login @signin @critical
  Scenario: Clicking Sign in with Google redirects to Google
    Given I am not logged in
    And I am on the login page
    When I click the Sign in with Google button
    Then I should be redirected to Google OAuth
    And the URL should contain "accounts.google.com"

  @login @signin
  Scenario: Sign in button shows loading state when clicked
    Given I am not logged in
    And I am on the login page
    When I click the Sign in with Google button
    Then the "sign-in-google-btn" should show loading state
    And the button text should change to "Redirecting..."

  @login @redirect @critical
  Scenario: Unauthenticated user accessing protected page is redirected to login
    Given I am not logged in
    When I navigate to the dashboard page directly
    Then I should be redirected to the login page
    And the URL should contain "/login"
    And the original URL should be preserved as return parameter

  @login @redirect
  Scenario: Unauthenticated user accessing settings is redirected to login
    Given I am not logged in
    When I navigate to "/settings" directly
    Then I should be redirected to the login page
    And the URL should contain "return=/settings"

  # =============================================================================
  # Login Page - Error Handling
  # =============================================================================

  @login @error @critical
  Scenario: Error message displays when login fails
    Given I am not logged in
    And I am on the login page
    When the OAuth flow returns an error
    Then I should see an error message
    And I should see "Authentication failed"
    And the "login-error-message" should be visible

  @login @error @domain
  Scenario: Error message displays for unauthorized domain
    Given I am not logged in
    And I am on the login page
    When the OAuth returns unauthorized domain error
    Then I should see "Your email domain is not authorized"
    And I should see "Please use your organization email"
    And the "domain-error-message" should be visible

  @login @error
  Scenario: Error message displays for account not found
    Given I am not logged in
    And I am on the login page
    When the OAuth returns account not found error
    Then I should see "Account not found"
    And I should see "Contact your administrator"

  @login @error @retry
  Scenario: User can retry login after error
    Given I am on the login page with an error displayed
    When I click the Sign in with Google button
    Then the error message should be cleared
    And I should be redirected to Google OAuth

  # =============================================================================
  # OAuth Callback Page
  # =============================================================================

  @callback @loading @critical
  Scenario: Callback page shows loading state while processing
    Given I am on the OAuth callback page with a valid code
    Then I should see a loading spinner
    And I should see "Completing sign in..."
    And the "auth-loading-spinner" should be visible

  @callback @success @critical
  Scenario: Successful callback redirects to dashboard
    Given I am on the OAuth callback page with a valid code
    When the authentication completes successfully
    Then I should be redirected to the dashboard
    And the URL should contain "/dashboard"
    And I should see "Dashboard"

  @callback @success @return
  Scenario: Successful callback redirects to original requested page
    Given I tried to access "/scenarios" before login
    And I am on the OAuth callback page with a valid code
    When the authentication completes successfully
    Then I should be redirected to the scenarios page
    And the URL should contain "/scenarios"

  @callback @error @critical
  Scenario: Failed callback shows error message
    Given I am on the OAuth callback page
    When the authentication fails
    Then I should see "Authentication failed"
    And I should see a "Try Again" button
    And the "callback-error" should be visible

  @callback @error @code
  Scenario: Callback with missing code shows error
    Given I navigate to the callback page without a code parameter
    Then I should see "Invalid authentication request"
    And I should see a "Return to Login" button

  @callback @error @code
  Scenario: Callback with invalid code shows error
    Given I navigate to the callback page with an invalid code
    When the authentication fails due to invalid code
    Then I should see "Authentication failed"
    And I should see "Invalid or expired code"

  @callback @retry
  Scenario: User can retry login after callback failure
    Given I am on the callback page with an error displayed
    When I click the "Try Again" button
    Then I should be redirected to the login page
    And I should be able to start a new sign in flow

  # =============================================================================
  # Protected Routes - Authentication Required
  # =============================================================================

  @protected @dashboard @critical
  Scenario: Dashboard requires authentication
    Given I am not logged in
    When I navigate to "/dashboard"
    Then I should be redirected to the login page
    And I should not see the dashboard content

  @protected @testruns @critical
  Scenario: Test Runs page requires authentication
    Given I am not logged in
    When I navigate to "/runs"
    Then I should be redirected to the login page
    And I should not see the test runs list

  @protected @scenarios @critical
  Scenario: Scenarios page requires authentication
    Given I am not logged in
    When I navigate to "/scenarios"
    Then I should be redirected to the login page
    And I should not see the scenarios list

  @protected @settings @critical
  Scenario: Settings page requires authentication
    Given I am not logged in
    When I navigate to "/settings"
    Then I should be redirected to the login page
    And I should not see the settings content

  @protected @repos
  Scenario: Repositories page requires authentication
    Given I am not logged in
    When I navigate to "/repos"
    Then I should be redirected to the login page

  @protected @return @critical
  Scenario: After login user returns to originally requested page
    Given I am not logged in
    And I tried to access "/runs" before login
    When I complete the Google sign in flow
    Then I should be redirected to the test runs page
    And the URL should contain "/runs"

  # =============================================================================
  # User Menu - Display
  # =============================================================================

  @usermenu @display @critical
  Scenario: User avatar displays in header when logged in
    Given I am logged in as "test.user@example.com"
    When I am on the dashboard page
    Then I should see the user avatar in the header
    And the "user-avatar" should be visible

  @usermenu @display @critical
  Scenario: User name displays next to avatar
    Given I am logged in as "Test User"
    When I am on the dashboard page
    Then the user menu should display "Test User"
    And the "user-name" should be visible

  @usermenu @display
  Scenario: User email displays in menu
    Given I am logged in as "test.user@example.com"
    When I open the user menu
    Then I should see "test.user@example.com"

  @usermenu @display
  Scenario: User avatar shows profile picture when available
    Given I am logged in as "test.user@example.com"
    And the user has a Google profile picture
    When I am on the dashboard page
    Then the user avatar should display the profile picture
    And the "user-avatar" should have an image source

  # =============================================================================
  # User Menu - Dropdown Interaction
  # =============================================================================

  @usermenu @dropdown @critical
  Scenario: Clicking avatar opens dropdown menu
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I click on the user avatar
    Then the user dropdown menu should be visible
    And the "user-dropdown" should be visible

  @usermenu @dropdown
  Scenario: Dropdown shows Profile option
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I click on the user avatar
    Then I should see "Profile" in the dropdown
    And the "menu-item-profile" should be visible

  @usermenu @dropdown
  Scenario: Dropdown shows Settings option
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I click on the user avatar
    Then I should see "Settings" in the dropdown
    And the "menu-item-settings" should be visible

  @usermenu @dropdown @critical
  Scenario: Dropdown shows Logout option
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I click on the user avatar
    Then I should see "Logout" in the dropdown
    And the "menu-item-logout" should be visible

  @usermenu @dropdown
  Scenario: Clicking outside dropdown closes it
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I click outside the dropdown menu
    Then the user dropdown menu should not be visible

  @usermenu @dropdown
  Scenario: Pressing Escape closes dropdown
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I press the "Escape" key
    Then the user dropdown menu should not be visible

  @usermenu @navigation
  Scenario: Clicking Profile navigates to profile page
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I click on "Profile" in the dropdown
    Then I should be redirected to the profile page
    And the URL should contain "/profile"

  @usermenu @navigation
  Scenario: Clicking Settings navigates to settings page
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I click on "Settings" in the dropdown
    Then I should be redirected to the settings page
    And the URL should contain "/settings"

  # =============================================================================
  # Logout Flow
  # =============================================================================

  @logout @critical
  Scenario: Clicking Logout clears session and redirects to login
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I click on "Logout" in the dropdown
    Then I should be redirected to the login page
    And my session should be cleared
    And I should see the Sign in with Google button

  @logout
  Scenario: After logout user cannot access protected pages
    Given I was logged in as "test.user@example.com"
    And I have logged out
    When I try to navigate to the dashboard
    Then I should be redirected to the login page
    And I should not see the dashboard content

  @logout
  Scenario: Logout shows confirmation message
    Given I am logged in as "test.user@example.com"
    And the user dropdown menu is open
    When I click on "Logout" in the dropdown
    Then I should see "You have been logged out"

  @logout
  Scenario: After logout user can login again
    Given I have logged out
    And I am on the login page
    When I click the Sign in with Google button
    Then I should be redirected to Google OAuth
    And I should be able to complete a new sign in

  # =============================================================================
  # Session Persistence
  # =============================================================================

  @session @persistence @critical
  Scenario: Session persists after page refresh
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I refresh the page
    Then I should still be logged in
    And I should see the user avatar
    And I should see the dashboard content

  @session @persistence
  Scenario: Session persists across different pages
    Given I am logged in as "test.user@example.com"
    And I am on the dashboard page
    When I navigate to the scenarios page
    Then I should still be logged in
    And I should see the user avatar in the header

  @session @persistence @critical
  Scenario: Session persists after browser tab is closed and reopened
    Given I am logged in as "test.user@example.com"
    And the session is stored in local storage
    When I close and reopen the browser tab
    Then I should still be logged in
    And I should see the dashboard content

  @session @expiry @critical
  Scenario: Expired session redirects to login
    Given I am logged in as "test.user@example.com"
    And my session has expired
    When I navigate to the dashboard
    Then I should be redirected to the login page
    And I should see "Your session has expired"
    And I should see "Please sign in again"

  @session @invalid
  Scenario: Invalid session token redirects to login
    Given I have an invalid session token
    When I try to access the dashboard
    Then I should be redirected to the login page
    And my invalid session should be cleared

  @session @relogin
  Scenario: User can login again after session expires
    Given my session has expired
    And I am on the login page
    When I click the Sign in with Google button
    And I complete the Google sign in flow
    Then I should be logged in successfully
    And I should see the dashboard content

  @session @token
  Scenario: Session token is refreshed before expiry
    Given I am logged in as "test.user@example.com"
    And my session is about to expire
    When the application refreshes the token
    Then my session should be extended
    And I should remain logged in

  # =============================================================================
  # Security - Token Storage
  # =============================================================================

  @security @token
  Scenario: Auth token is stored securely
    Given I complete the Google sign in flow
    Then the auth token should be stored in httpOnly cookie or secure storage
    And the token should not be accessible via JavaScript directly

  @security @headers
  Scenario: API requests include authorization header
    Given I am logged in as "test.user@example.com"
    When I navigate to the dashboard
    Then API requests should include the Authorization header
    And the header should contain a valid Bearer token
