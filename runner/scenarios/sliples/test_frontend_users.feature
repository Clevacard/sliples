@phase7 @frontend @ui @users @admin
Feature: User Management - Admin Access and User Administration
  As a Sliples administrator
  I want to manage users through the User Management page
  So that I can control access and roles within the application

  # =============================================================================
  # Access Control - Admin-Only Page
  # =============================================================================

  @access @admin @critical
  Scenario: Admin can access users page
    Given I am logged in as "admin@example.com" with role "admin"
    When I navigate to the users page
    Then I should see "User Management"
    And the "users-page" should be visible
    And the "users-list" should be visible

  @access @nonadmin @critical
  Scenario: Non-admin redirected from users page
    Given I am logged in as "regular.user@example.com" with role "user"
    When I navigate to "/users" directly
    Then I should be redirected to the dashboard
    And I should not see "User Management"

  @access @navigation @admin
  Scenario: Users link only visible to admins in navigation
    Given I am logged in as "admin@example.com" with role "admin"
    When I am on the dashboard page
    Then the "nav-users-link" should be visible
    And I should see "Users" in the navigation menu

  @access @navigation @nonadmin
  Scenario: Users link not visible to non-admins in navigation
    Given I am logged in as "regular.user@example.com" with role "user"
    When I am on the dashboard page
    Then the "nav-users-link" should not be visible
    And I should not see "Users" in the navigation menu

  @access @error @nonadmin
  Scenario: Access denied message for non-admins attempting direct URL access
    Given I am logged in as "regular.user@example.com" with role "user"
    When I navigate to "/users" directly
    Then I should see "Access Denied" or be redirected
    And I should not see the users list content

  @access @badge @admin
  Scenario: Admin badge shown for admin users in header
    Given I am logged in as "admin@example.com" with role "admin"
    When I am on the dashboard page
    Then I should see the admin indicator in the header
    And the "user-role-badge" should display "Admin"

  @access @api @critical
  Scenario: Cannot access user management API without admin role
    Given I am logged in as "regular.user@example.com" with role "user"
    When I make an API request to GET "/api/v1/users"
    Then the API should return status 403
    And the response should contain "Forbidden"

  # =============================================================================
  # User List - Display and Information
  # =============================================================================

  @list @display @critical
  Scenario: View list of all users
    Given I am logged in as "admin@example.com" with role "admin"
    And there are multiple users in the system
    When I navigate to the users page
    Then I should see the users list
    And I should see at least 2 user entries
    And each user entry should be in a row

  @list @display @avatar
  Scenario: See user name, email, and avatar in list
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "John Doe" with email "john.doe@example.com"
    When I navigate to the users page
    Then I should see "John Doe" in the users list
    And I should see "john.doe@example.com" in the users list
    And the user row should display an avatar

  @list @display @role
  Scenario: See user role badge in list
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user with role "admin"
    And there is a user with role "user"
    When I navigate to the users page
    Then I should see role badges for each user
    And the "role-badge-admin" should be visible for admin users
    And the "role-badge-user" should be visible for regular users

  @list @display @status
  Scenario: See user status (active/inactive) in list
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an active user "active.user@example.com"
    And there is an inactive user "inactive.user@example.com"
    When I navigate to the users page
    Then I should see "Active" status for "active.user@example.com"
    And I should see "Inactive" status for "inactive.user@example.com"
    And the "status-badge" should be visible for each user

  @list @display @lastlogin
  Scenario: See last login timestamp in user list
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user who logged in "2 hours ago"
    When I navigate to the users page
    Then I should see "Last login" column
    And the last login timestamp should be displayed
    And the timestamp should show relative time or date format

  @list @search @name
  Scenario: Search users by name
    Given I am logged in as "admin@example.com" with role "admin"
    And there are users with names "Alice Smith" and "Bob Johnson"
    When I navigate to the users page
    And I enter "Alice" into the search field
    Then I should see "Alice Smith" in the results
    And I should not see "Bob Johnson" in the results

  @list @search @email
  Scenario: Search users by email
    Given I am logged in as "admin@example.com" with role "admin"
    And there are users with emails "alice@company.com" and "bob@company.com"
    When I navigate to the users page
    And I enter "alice@" into the search field
    Then I should see "alice@company.com" in the results
    And I should not see "bob@company.com" in the results

  @list @search @empty
  Scenario: Empty state when search has no results
    Given I am logged in as "admin@example.com" with role "admin"
    And there are users in the system
    When I navigate to the users page
    And I enter "nonexistent_xyz_user" into the search field
    Then I should see "No users found"
    And I should see "Try adjusting your search criteria"
    And the "empty-search-state" should be visible

  # =============================================================================
  # Change Role - Admin can modify user roles
  # =============================================================================

  @role @change @critical
  Scenario: Change user role to admin
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "regular.user@example.com" with role "user"
    When I navigate to the users page
    And I click the role dropdown for "regular.user@example.com"
    And I select "Admin" from the role dropdown
    Then the confirmation modal should appear
    When I confirm the role change
    Then I should see "Role updated successfully"
    And the user "regular.user@example.com" should display role "Admin"

  @role @change @critical
  Scenario: Change user role to user
    Given I am logged in as "superadmin@example.com" with role "admin"
    And there is a user "another.admin@example.com" with role "admin"
    When I navigate to the users page
    And I click the role dropdown for "another.admin@example.com"
    And I select "User" from the role dropdown
    Then the confirmation modal should appear
    When I confirm the role change
    Then I should see "Role updated successfully"
    And the user "another.admin@example.com" should display role "User"

  @role @modal @confirm
  Scenario: Confirmation modal before role change
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "test.user@example.com" with role "user"
    When I navigate to the users page
    And I click the role dropdown for "test.user@example.com"
    And I select "Admin" from the role dropdown
    Then the "role-change-modal" should be visible
    And I should see "Change User Role"
    And I should see "Are you sure you want to change the role"
    And I should see "Confirm" button
    And I should see "Cancel" button

  @role @modal @cancel
  Scenario: Cancel role change
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "test.user@example.com" with role "user"
    And the role change confirmation modal is open
    When I click the "Cancel" button
    Then the "role-change-modal" should not be visible
    And the user "test.user@example.com" should still display role "User"

  @role @self @denied
  Scenario: Cannot change own role
    Given I am logged in as "admin@example.com" with role "admin"
    When I navigate to the users page
    Then the role dropdown for "admin@example.com" should be disabled
    And I should see a tooltip "Cannot change your own role"

  @role @update @list
  Scenario: Role change reflected in list immediately
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "promote.user@example.com" with role "user"
    When I navigate to the users page
    And I change the role of "promote.user@example.com" to "Admin"
    Then the users list should update without page refresh
    And the "role-badge-admin" should be visible for "promote.user@example.com"

  # =============================================================================
  # Toggle Active Status - Activate/Deactivate Users
  # =============================================================================

  @status @deactivate @critical
  Scenario: Deactivate a user
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an active user "to.deactivate@example.com"
    When I navigate to the users page
    And I click the status toggle for "to.deactivate@example.com"
    Then the deactivation confirmation modal should appear
    When I confirm the deactivation
    Then I should see "User deactivated successfully"
    And the user "to.deactivate@example.com" should show "Inactive" status

  @status @reactivate @critical
  Scenario: Reactivate a user
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an inactive user "to.reactivate@example.com"
    When I navigate to the users page
    And I click the status toggle for "to.reactivate@example.com"
    Then I should see "User activated successfully"
    And the user "to.reactivate@example.com" should show "Active" status

  @status @modal @deactivate
  Scenario: Confirmation modal for deactivation
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an active user "confirm.deactivate@example.com"
    When I navigate to the users page
    And I click the status toggle for "confirm.deactivate@example.com"
    Then the "deactivation-modal" should be visible
    And I should see "Deactivate User"
    And I should see "This user will no longer be able to log in"
    And I should see "Deactivate" button

  @status @self @denied
  Scenario: Cannot deactivate yourself
    Given I am logged in as "admin@example.com" with role "admin"
    When I navigate to the users page
    Then the status toggle for "admin@example.com" should be disabled
    And I should see a tooltip "Cannot deactivate your own account"

  @status @badge @inactive
  Scenario: Deactivated user shows inactive badge
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an inactive user "deactivated@example.com"
    When I navigate to the users page
    Then the "status-badge-inactive" should be visible for "deactivated@example.com"
    And the badge should display "Inactive"
    And the user row should have visual indication of inactive status

  @status @login @blocked
  Scenario: Deactivated user cannot login
    Given there is an inactive user "blocked@example.com"
    And I am not logged in
    When I attempt to login as "blocked@example.com"
    Then I should see "Your account has been deactivated"
    And I should see "Contact your administrator"
    And I should not be logged in

  # =============================================================================
  # Backend API - User Management Endpoints
  # =============================================================================

  @api @list @critical
  Scenario: GET /users returns all users for admin
    Given I am logged in as "admin@example.com" with role "admin"
    When I make an API request to GET "/api/v1/users"
    Then the API should return status 200
    And the response should contain a list of users
    And each user should have id, name, email, role, and active fields

  @api @auth @critical
  Scenario: GET /users requires admin role
    Given I am logged in as "regular.user@example.com" with role "user"
    When I make an API request to GET "/api/v1/users"
    Then the API should return status 403
    And the response should contain "Admin access required"

  @api @role @update
  Scenario: PUT /users/{id}/role updates user role
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user with id "user-123" and role "user"
    When I make an API request to PUT "/api/v1/users/user-123/role" with body '{"role": "admin"}'
    Then the API should return status 200
    And the response should contain "role" as "admin"
    And the user's role should be updated in the database

  @api @status @update
  Scenario: PUT /users/{id}/active toggles user status
    Given I am logged in as "admin@example.com" with role "admin"
    And there is an active user with id "user-456"
    When I make an API request to PUT "/api/v1/users/user-456/active" with body '{"active": false}'
    Then the API should return status 200
    And the response should contain "active" as false
    And the user should be marked as inactive in the database

  @api @auth @forbidden
  Scenario: Non-admin gets 403 on admin endpoints
    Given I am logged in as "regular.user@example.com" with role "user"
    When I make an API request to PUT "/api/v1/users/any-user/role" with body '{"role": "admin"}'
    Then the API should return status 403
    And the response should contain "Forbidden"

  @api @self @denied
  Scenario: Cannot modify own active status via API
    Given I am logged in as "admin@example.com" with role "admin"
    And my user id is "admin-user-id"
    When I make an API request to PUT "/api/v1/users/admin-user-id/active" with body '{"active": false}'
    Then the API should return status 400
    And the response should contain "Cannot modify your own account status"

  # =============================================================================
  # Additional UI Scenarios - Pagination and Sorting
  # =============================================================================

  @list @pagination
  Scenario: Users list supports pagination
    Given I am logged in as "admin@example.com" with role "admin"
    And there are more than 20 users in the system
    When I navigate to the users page
    Then I should see pagination controls
    And I should see "Page 1 of" indicator
    When I click the "Next" pagination button
    Then I should see the next page of users

  @list @sort @name
  Scenario: Sort users by name
    Given I am logged in as "admin@example.com" with role "admin"
    And there are multiple users in the system
    When I navigate to the users page
    And I click the "Name" column header
    Then the users should be sorted alphabetically by name
    When I click the "Name" column header again
    Then the users should be sorted in reverse alphabetical order

  @list @sort @lastlogin
  Scenario: Sort users by last login
    Given I am logged in as "admin@example.com" with role "admin"
    And there are users with different last login times
    When I navigate to the users page
    And I click the "Last Login" column header
    Then the users should be sorted by last login date
    And the most recently logged in user should appear first

  # =============================================================================
  # Error Handling and Edge Cases
  # =============================================================================

  @error @network
  Scenario: Show error when user list fails to load
    Given I am logged in as "admin@example.com" with role "admin"
    And the users API is unavailable
    When I navigate to the users page
    Then I should see "Failed to load users"
    And I should see a "Retry" button
    When I click the "Retry" button
    Then the system should attempt to reload the users list

  @error @rolechange @failure
  Scenario: Show error when role change fails
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "test.user@example.com" with role "user"
    And the role update API will fail
    When I navigate to the users page
    And I change the role of "test.user@example.com" to "Admin"
    Then I should see "Failed to update role"
    And the user "test.user@example.com" should still display role "User"

  @concurrent @update
  Scenario: Handle concurrent user updates
    Given I am logged in as "admin@example.com" with role "admin"
    And there is a user "concurrent.user@example.com"
    And another admin has modified this user's role
    When I try to change the role of "concurrent.user@example.com"
    Then I should see "User data has changed"
    And I should see "Please refresh and try again"
