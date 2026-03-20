# Google Workspace SSO Authentication Tests
# ==========================================
# Tests for Google OAuth 2.0 / OpenID Connect integration
#
# These scenarios test:
# - OAuth authorization flow
# - Domain restrictions for Google Workspace
# - JWT session management
# - User management during SSO login
# - Error handling for various failure cases

@phase2 @sso @google @api
Feature: Google Workspace SSO Authentication
  As a Sliples administrator
  I want to integrate Google Workspace SSO
  So that users can securely authenticate using their corporate Google accounts

  Background:
    Given the API server is running at "http://localhost:8000"
    And Google OAuth is configured

  # =============================================================================
  # OAuth Flow - Authorization URL Generation
  # =============================================================================

  @sso @oauth @authorization-url @happy-path
  Scenario: Get Google authorization URL
    When I request the Google authorization URL
    Then the response status code should be 200
    And the response should contain "authorization_url"
    And the authorization URL should start with "https://accounts.google.com/o/oauth2/v2/auth"

  @sso @oauth @authorization-url @happy-path
  Scenario: Authorization URL contains correct client_id parameter
    When I request the Google authorization URL
    Then the response status code should be 200
    And the authorization URL should contain parameter "client_id"
    And the client_id should match the configured Google client ID

  @sso @oauth @authorization-url @happy-path
  Scenario: Authorization URL contains correct redirect_uri parameter
    When I request the Google authorization URL
    Then the response status code should be 200
    And the authorization URL should contain parameter "redirect_uri"
    And the redirect_uri should match the configured callback URL

  @sso @oauth @authorization-url @happy-path
  Scenario: Authorization URL contains required scopes
    When I request the Google authorization URL
    Then the response status code should be 200
    And the authorization URL should contain parameter "scope"
    And the scope should include "openid"
    And the scope should include "email"
    And the scope should include "profile"

  @sso @oauth @authorization-url @security
  Scenario: Authorization URL contains state parameter for CSRF protection
    When I request the Google authorization URL
    Then the response status code should be 200
    And the authorization URL should contain parameter "state"
    And the state should be a non-empty string

  @sso @oauth @authorization-url @happy-path
  Scenario: Authorization URL uses code response type
    When I request the Google authorization URL
    Then the response status code should be 200
    And the authorization URL should contain parameter "response_type"
    And the response_type should equal "code"

  # =============================================================================
  # OAuth Flow - Callback Handling
  # =============================================================================

  @sso @oauth @callback @happy-path
  Scenario: Successful OAuth callback creates new user
    Given a valid Google OAuth code for user "newuser@company.com"
    And no user with email "newuser@company.com" exists
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And a new user should be created with email "newuser@company.com"
    And the user should have the default role "viewer"
    And the JWT cookie should be set

  @sso @oauth @callback @happy-path
  Scenario: Successful OAuth callback updates existing user
    Given an existing user with email "existinguser@company.com"
    And the user's last_login is "2024-01-01T10:00:00Z"
    And a valid Google OAuth code for user "existinguser@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user's last_login should be updated to approximately now
    And the JWT cookie should be set

  @sso @oauth @callback @error
  Scenario: OAuth callback with invalid code returns error
    Given an invalid Google OAuth code "invalid_code_12345"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 400
    And the response body should contain "invalid_grant"

  @sso @oauth @callback @error
  Scenario: OAuth callback with missing code returns error
    When I send a GET request to "/api/v1/auth/google/callback" without code parameter
    Then the response status code should be 400
    And the response body should contain "code is required"

  @sso @oauth @callback @error
  Scenario: OAuth callback with expired code returns error
    Given an expired Google OAuth code for user "user@company.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 400
    And the response body should contain "code expired"

  @sso @oauth @callback @security
  Scenario: OAuth callback with mismatched state is rejected
    Given a valid Google OAuth code for user "user@company.com"
    And the state parameter does not match the session state
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 400
    And the response body should contain "invalid state"

  # =============================================================================
  # Domain Restriction
  # =============================================================================

  @sso @domain @happy-path
  Scenario: User from allowed workspace domain can login
    Given the allowed domains are configured as "company.com, partner.org"
    And a valid Google OAuth code for user "employee@company.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user should be authenticated successfully
    And the JWT cookie should be set

  @sso @domain @security
  Scenario: User from non-allowed domain is rejected
    Given the allowed domains are configured as "company.com"
    And a valid Google OAuth code for user "outsider@other-company.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 403
    And the response body should contain "domain not allowed"
    And no JWT cookie should be set

  @sso @domain @happy-path
  Scenario: Multiple allowed domains work correctly
    Given the allowed domains are configured as "company.com, subsidiary.com, partner.org"
    And a valid Google OAuth code for user "user@subsidiary.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user should be authenticated successfully

  @sso @domain @security
  Scenario: Personal Gmail account is rejected when workspace-only configured
    Given only workspace domains are allowed
    And a valid Google OAuth code for user "personal@gmail.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 403
    And the response body should contain "personal Gmail accounts not allowed"

  @sso @domain @happy-path
  Scenario: Subdomain handling for allowed domains
    Given the allowed domains are configured as "company.com"
    And subdomain matching is disabled
    And a valid Google OAuth code for user "user@hr.company.com"
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 403
    And the response body should contain "domain not allowed"

  # =============================================================================
  # JWT Session Management
  # =============================================================================

  @sso @jwt @happy-path
  Scenario: Successful login returns JWT token
    Given a valid Google OAuth code for user "user@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the response should contain "access_token"
    And the access_token should be a valid JWT

  @sso @jwt @security
  Scenario: JWT token is set as httpOnly cookie
    Given a valid Google OAuth code for user "user@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the Set-Cookie header should be present
    And the cookie should have the HttpOnly flag
    And the cookie should have the Secure flag
    And the cookie should have the SameSite attribute set to "Lax"

  @sso @jwt @happy-path
  Scenario: Valid JWT allows access to /auth/me
    Given I am logged in as "user@company.com" via Google SSO
    When I send a GET request to "/api/v1/auth/me" with the JWT cookie
    Then the response status code should be 200
    And the response should contain "email"
    And the JSON field "email" should equal "user@company.com"

  @sso @jwt @security
  Scenario: Expired JWT returns 401
    Given I have an expired JWT token for user "user@company.com"
    When I send a GET request to "/api/v1/auth/me" with the expired JWT cookie
    Then the response status code should be 401
    And the response body should contain "token expired"

  @sso @jwt @security
  Scenario: Invalid JWT returns 401
    Given I have an invalid JWT token "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload"
    When I send a GET request to "/api/v1/auth/me" with the invalid JWT cookie
    Then the response status code should be 401
    And the response body should contain "invalid token"

  @sso @jwt @security
  Scenario: Missing JWT returns 401
    When I send a GET request to "/api/v1/auth/me" without any authentication
    Then the response status code should be 401
    And the response body should contain "authentication required"

  @sso @jwt @logout @happy-path
  Scenario: Logout clears JWT cookie
    Given I am logged in as "user@company.com" via Google SSO
    When I send a POST request to "/api/v1/auth/logout"
    Then the response status code should be 200
    And the Set-Cookie header should clear the JWT cookie
    And subsequent requests to "/api/v1/auth/me" should return 401

  @sso @jwt @claims @happy-path
  Scenario: Token contains correct user claims
    Given I am logged in as "user@company.com" via Google SSO
    When I decode the JWT token
    Then the token should contain claim "sub" with the user ID
    And the token should contain claim "email" with "user@company.com"
    And the token should contain claim "exp" with a future timestamp
    And the token should contain claim "iat" with a recent timestamp

  # =============================================================================
  # User Management
  # =============================================================================

  @sso @user @creation @happy-path
  Scenario: New user is created on first login
    Given no user with email "firsttime@company.com" exists
    And a valid Google OAuth code for user "firsttime@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And a user with email "firsttime@company.com" should exist in the database
    And the user should have name from Google profile
    And the user created_at should be approximately now

  @sso @user @update @happy-path
  Scenario: User last_login is updated on subsequent logins
    Given an existing user with email "returning@company.com"
    And the user's last_login is "2024-01-15T10:00:00Z"
    And a valid Google OAuth code for user "returning@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user's last_login should be updated to approximately now
    And the user's created_at should remain unchanged

  @sso @user @profile @happy-path
  Scenario: User picture_url is updated from Google profile
    Given an existing user with email "photouser@company.com"
    And the user has picture_url "https://old-picture.com/photo.jpg"
    And a valid Google OAuth code for user "photouser@company.com" with picture "https://new-picture.com/photo.jpg"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user's picture_url should be "https://new-picture.com/photo.jpg"

  @sso @user @disabled @security
  Scenario: Disabled user cannot login
    Given an existing user with email "disabled@company.com"
    And the user account is disabled
    And a valid Google OAuth code for user "disabled@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 403
    And the response body should contain "account disabled"
    And no JWT cookie should be set

  @sso @user @role @happy-path
  Scenario: User role is preserved across logins
    Given an existing user with email "admin@company.com" and role "admin"
    And a valid Google OAuth code for user "admin@company.com"
    And the domain "company.com" is in the allowed domains list
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 200
    And the user's role should still be "admin"

  # =============================================================================
  # Error Handling
  # =============================================================================

  @sso @error @google-api
  Scenario: Google API error is handled gracefully
    Given Google's token endpoint returns a server error
    And a valid authorization code is provided
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 502
    And the response body should contain "Google authentication service unavailable"

  @sso @error @timeout
  Scenario: Network timeout to Google returns appropriate error
    Given Google's token endpoint times out
    And a valid authorization code is provided
    When I exchange the OAuth code at the callback endpoint
    Then the response status code should be 504
    And the response body should contain "authentication timeout"

  @sso @error @csrf @security
  Scenario: Invalid state parameter is rejected (CSRF protection)
    Given a valid Google OAuth code for user "user@company.com"
    And the state parameter is "tampered_state_value"
    When I exchange the OAuth code with the tampered state
    Then the response status code should be 400
    And the response body should contain "CSRF validation failed"

  @sso @error @rate-limit @security
  Scenario: Rate limiting on login attempts
    Given I have made 10 login attempts in the last minute
    When I request the Google authorization URL
    Then the response status code should be 429
    And the response body should contain "too many login attempts"
    And the Retry-After header should be present

  @sso @error @misconfiguration
  Scenario: Missing Google OAuth configuration returns error
    Given Google OAuth client credentials are not configured
    When I request the Google authorization URL
    Then the response status code should be 500
    And the response body should contain "OAuth not configured"

  # =============================================================================
  # Token Refresh (Optional Feature)
  # =============================================================================

  @sso @jwt @refresh @happy-path
  Scenario: Refresh token extends session
    Given I am logged in as "user@company.com" via Google SSO
    And my JWT token is about to expire in 5 minutes
    When I send a POST request to "/api/v1/auth/refresh"
    Then the response status code should be 200
    And a new JWT cookie should be set
    And the new token should have a fresh expiration time

  @sso @jwt @refresh @security
  Scenario: Cannot refresh with expired token
    Given I have an expired JWT token for user "user@company.com"
    When I send a POST request to "/api/v1/auth/refresh" with the expired JWT cookie
    Then the response status code should be 401
    And the response body should contain "token expired"
    And I should be required to re-authenticate via Google

  # =============================================================================
  # Session Management
  # =============================================================================

  @sso @session @concurrent @happy-path
  Scenario: User can have multiple active sessions
    Given I am logged in as "multidevice@company.com" via Google SSO on device A
    And I log in again as "multidevice@company.com" via Google SSO on device B
    Then both sessions should be valid
    And requests from device A with JWT A should succeed
    And requests from device B with JWT B should succeed

  @sso @session @logout-all @happy-path
  Scenario: Logout all sessions invalidates all tokens
    Given I am logged in as "alllout@company.com" via Google SSO on multiple devices
    When I send a POST request to "/api/v1/auth/logout-all"
    Then the response status code should be 200
    And all active sessions for the user should be invalidated
    And subsequent requests with any of the old JWT tokens should return 401
