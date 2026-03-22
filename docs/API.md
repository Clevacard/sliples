# Sliples API Documentation

Comprehensive API documentation for the Sliples Web UI Automation Testing Platform.

**Base URL:** `/api/v1`

**API Version:** 1.0

---

## Table of Contents

1. [Authentication](#authentication)
   - [Google SSO](#google-sso)
   - [API Key Authentication](#api-key-authentication)
2. [Health Check](#health-check)
3. [Environments](#environments)
4. [Scenarios](#scenarios)
5. [Test Runs](#test-runs)
6. [Repositories](#repositories)
7. [Custom Steps](#custom-steps)
8. [Schedules](#schedules)
9. [Test Sessions (Interactive)](#test-sessions-interactive)
10. [Users (Admin Only)](#users-admin-only)
11. [API Keys](#api-keys)
12. [Browsers](#browsers)
13. [CI/CD Integration](#cicd-integration)
    - [GitHub Actions](#github-actions)
    - [GitLab CI](#gitlab-ci)
    - [Jenkins](#jenkins)
14. [Error Handling](#error-handling)
15. [WebSocket Endpoints](#websocket-endpoints)

---

## Authentication

Sliples supports two authentication methods:

### Google SSO

For browser-based access, Sliples uses Google Workspace SSO (Single Sign-On). Only users from allowed workspace domains can authenticate.

#### Initiate Login

```http
GET /api/v1/auth/google/login
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `redirect` | boolean | `true` | If `true`, redirects to Google. If `false`, returns JSON with authorization URL. |

**Response (redirect=false):**

```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-string"
}
```

#### OAuth Callback

```http
GET /api/v1/auth/google/callback
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `code` | string | Authorization code from Google |
| `state` | string | State parameter for CSRF protection |
| `error` | string | Error code if authorization failed |
| `error_description` | string | Human-readable error description |

This endpoint is called by Google after user authorization. On success:
- Sets an `access_token` httpOnly cookie
- Redirects to the frontend application

**Error Handling:**
- If Google returns an error, redirects to `/login?error={error_message}`
- If workspace domain is not allowed, redirects to `/login?error=domain_not_allowed`

#### Get Current User

```http
GET /api/v1/auth/me
```

**Headers:**

| Header | Description |
|--------|-------------|
| `Cookie: access_token=...` | Session cookie (set automatically) |
| `Authorization: Bearer {token}` | OR Bearer token for API access |

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@company.com",
  "name": "John Doe",
  "picture_url": "https://lh3.googleusercontent.com/...",
  "workspace_domain": "company.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-03-20T10:00:00Z",
  "last_login": "2026-03-21T09:00:00Z"
}
```

**Error Codes:**
- `401` - Not authenticated

#### Refresh Token

```http
GET /api/v1/auth/token
```

Returns a new JWT token for the current user. Useful for refreshing tokens before expiration.

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

#### Logout

```http
POST /api/v1/auth/logout
```

Clears the session cookie.

**Response:** `200 OK`

```json
{
  "message": "Successfully logged out"
}
```

---

### API Key Authentication

For CI/CD pipelines and programmatic access, use API key authentication.

**Header Format:**
```
X-API-Key: {your-64-character-api-key}
```

**Example Request:**

```bash
curl -H "X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2" \
     https://sliples.example.com/api/v1/runs
```

#### Creating and Managing API Keys

See the [API Keys](#api-keys) section for complete CRUD operations.

---

## Health Check

### Check API Health

```http
GET /api/v1/health
```

**Authentication:** Not required

Checks the health of the API and its dependencies (PostgreSQL, Redis).

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

**Degraded Response:**

```json
{
  "status": "degraded",
  "database": "connected",
  "redis": "disconnected",
  "redis_error": "Connection refused"
}
```

**Status Values:**
| Status | Description |
|--------|-------------|
| `healthy` | All services operational |
| `degraded` | One or more services unavailable |

---

## Environments

Environments define target systems for test execution (e.g., development, staging, production).

### List Environments

```http
GET /api/v1/environments
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "staging",
    "base_url": "https://staging.example.com",
    "credentials_env": "STAGING_CREDS",
    "variables": {
      "ADMIN_USER": "admin@test.com",
      "TIMEOUT": "30000"
    },
    "retention_days": 365,
    "browser_configs": [
      {
        "id": "661f8400-e29b-41d4-a716-446655440001",
        "browser": "chrome",
        "version": "latest",
        "channel": "stable"
      }
    ]
  }
]
```

### Create Environment

```http
POST /api/v1/environments
```

**Request Body:**

```json
{
  "name": "staging",
  "base_url": "https://staging.example.com",
  "credentials_env": "STAGING_CREDS",
  "variables": {
    "ADMIN_USER": "admin@test.com",
    "FEATURE_FLAG_X": "true"
  },
  "retention_days": 365,
  "browser_configs": [
    {
      "browser": "chrome",
      "version": "latest",
      "channel": "stable"
    },
    {
      "browser": "firefox",
      "version": "latest",
      "channel": "stable"
    }
  ]
}
```

**Required Fields:**

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | 1-100 chars | Unique environment name |
| `base_url` | string | Valid HTTP(S) URL | Base URL for the test target |

**Optional Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `credentials_env` | string | null | Environment variable name for credentials |
| `variables` | object | {} | Custom key-value variables |
| `retention_days` | integer | 365 | Data retention period (1-3650 days) |
| `browser_configs` | array | [] | Browser configurations |

**Browser Config Fields:**

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `browser` | string | `chrome`, `chromium`, `firefox`, `webkit`, `edge` | required |
| `version` | string | Version string | `latest` |
| `channel` | string | `stable`, `beta`, `dev`, `canary` | `stable` |

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "staging",
  "base_url": "https://staging.example.com",
  "credentials_env": "STAGING_CREDS",
  "variables": {"ADMIN_USER": "admin@test.com"},
  "retention_days": 365,
  "browser_configs": [...]
}
```

**Error Codes:**
- `400` - Environment with this name already exists
- `422` - Validation error (invalid URL, browser type, etc.)

### Get Environment

```http
GET /api/v1/environments/{environment_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `environment_id` | UUID | Environment ID |

**Response:** `200 OK`

**Error Codes:**
- `404` - Environment not found

### Update Environment

```http
PUT /api/v1/environments/{environment_id}
```

**Request Body:** (all fields optional)

```json
{
  "name": "production",
  "base_url": "https://app.example.com",
  "variables": {"DEBUG": "false"},
  "retention_days": 90,
  "browser_configs": [
    {"browser": "chrome", "version": "latest", "channel": "stable"}
  ]
}
```

**Note:** If `browser_configs` is provided, it replaces all existing configurations.

**Response:** `200 OK`

### Delete Environment

```http
DELETE /api/v1/environments/{environment_id}
```

**Response:** `204 No Content`

**Error Codes:**
- `404` - Environment not found

### Browser Configuration Endpoints

#### List Browser Configs

```http
GET /api/v1/environments/{environment_id}/browsers
```

#### Add Browser Config

```http
POST /api/v1/environments/{environment_id}/browsers
```

**Request Body:**

```json
{
  "browser": "firefox",
  "version": "latest",
  "channel": "stable"
}
```

**Response:** `201 Created`

**Error Codes:**
- `400` - Browser config for this browser/channel already exists
- `404` - Environment not found

#### Update Browser Config

```http
PUT /api/v1/environments/{environment_id}/browsers/{browser_config_id}
```

#### Delete Browser Config

```http
DELETE /api/v1/environments/{environment_id}/browsers/{browser_config_id}
```

---

## Scenarios

Scenarios are Gherkin-style test definitions stored in `.feature` files.

### List Scenarios

```http
GET /api/v1/scenarios
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tag` | string | Filter by single tag |
| `tags` | string | Comma-separated tags (OR filter) |
| `repo_id` | UUID | Filter by repository |
| `search` | string | Search in scenario name (case-insensitive) |
| `limit` | integer | Max results (1-500, default: 100) |
| `offset` | integer | Pagination offset (default: 0) |

**Example Requests:**

```http
# Filter by single tag
GET /api/v1/scenarios?tag=smoke

# Filter by multiple tags (OR logic)
GET /api/v1/scenarios?tags=smoke,regression,critical

# Search by name
GET /api/v1/scenarios?search=login

# Combine filters
GET /api/v1/scenarios?tags=smoke,regression&repo_id=550e8400-...&limit=50
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "661f8400-e29b-41d4-a716-446655440001",
    "name": "User Login",
    "feature_path": "features/auth/login.feature",
    "tags": ["smoke", "auth", "critical"],
    "updated_at": "2026-03-20T15:00:00Z"
  }
]
```

### Get All Tags

```http
GET /api/v1/scenarios/tags
```

Returns all unique tags across all scenarios.

**Response:** `200 OK`

```json
{
  "tags": ["auth", "checkout", "critical", "regression", "smoke"],
  "count": 5
}
```

### Get Scenario

```http
GET /api/v1/scenarios/{scenario_id}
```

Returns full scenario details including Gherkin content.

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "repo_id": "661f8400-e29b-41d4-a716-446655440001",
  "name": "User Login",
  "feature_path": "features/auth/login.feature",
  "tags": ["smoke", "auth"],
  "content": "Feature: User Login\n\n  @smoke @auth\n  Scenario: Successful login with valid credentials\n    Given I am on the login page\n    When I enter \"user@example.com\" as email\n    And I enter \"password123\" as password\n    And I click the login button\n    Then I should see the dashboard\n    And I should see \"Welcome back\" message",
  "updated_at": "2026-03-20T15:00:00Z"
}
```

### Get Scenario Content

```http
GET /api/v1/scenarios/{scenario_id}/content
```

Returns just the Gherkin content (useful for editors).

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "User Login",
  "feature_path": "features/auth/login.feature",
  "content": "Feature: User Login\n\n  Scenario: Successful login\n    Given I am on the login page\n    ..."
}
```

### Update Scenario Content

```http
PUT /api/v1/scenarios/{scenario_id}/content
```

**Request Body:**

```json
{
  "content": "Feature: User Login\n\n  @smoke @auth\n  Scenario: Successful login with valid credentials\n    Given I am on the login page\n    When I enter valid credentials\n    Then I should see the dashboard"
}
```

**Response:** `200 OK` with updated scenario

### Create Scenario

```http
POST /api/v1/scenarios
```

**Request Body:**

```json
{
  "name": "User Registration",
  "feature_path": "features/auth/register.feature",
  "content": "Feature: User Registration\n\n  Scenario: New user can register\n    Given I am on the registration page\n    When I fill in the registration form\n    Then I should receive a confirmation email",
  "tags": ["auth", "regression"],
  "repo_id": "661f8400-e29b-41d4-a716-446655440001"
}
```

**Response:** `201 Created`

### Delete Scenario

```http
DELETE /api/v1/scenarios/{scenario_id}
```

**Response:** `204 No Content`

### Sync Scenarios

```http
POST /api/v1/scenarios/sync
```

Triggers background sync from all configured repositories.

**Response:** `200 OK`

```json
{
  "status": "sync_queued",
  "message": "Sync started for 3 repositories",
  "task_id": "celery-task-id-xxx",
  "repos": [
    {"id": "550e8400-...", "name": "main-tests"},
    {"id": "661f8400-...", "name": "integration-tests"}
  ]
}
```

**No Repositories Response:**

```json
{
  "status": "no_repos",
  "message": "No repositories configured. Add a repository first.",
  "synced_count": 0
}
```

---

## Test Runs

Test runs execute scenarios against environments using Playwright.

### List Test Runs

```http
GET /api/v1/runs
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status_filter` | string | Filter by status |
| `environment_id` | UUID | Filter by environment |
| `limit` | integer | Max results (default: 50) |
| `offset` | integer | Pagination offset (default: 0) |

**Status Values:** `queued`, `running`, `passed`, `failed`, `cancelled`, `error`

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "scenario_ids": ["uuid-1", "uuid-2", "uuid-3"],
    "environment_id": "661f8400-e29b-41d4-a716-446655440001",
    "status": "passed",
    "browser": "chrome",
    "browser_version": "latest",
    "triggered_by": "user@example.com",
    "parallel": true,
    "progress_message": "Completed 15/15 steps",
    "started_at": "2026-03-21T10:00:00Z",
    "finished_at": "2026-03-21T10:05:32Z",
    "created_at": "2026-03-21T09:59:45Z"
  }
]
```

### Create Test Run

```http
POST /api/v1/runs
```

Triggers a new test run. Returns `202 Accepted` as execution is asynchronous.

**Request Body:**

```json
{
  "scenario_tags": ["smoke", "regression"],
  "scenario_ids": [],
  "environment": "staging",
  "browsers": ["chrome", "firefox"],
  "parallel": true
}
```

**Scenario Selection Logic:**
1. If `scenario_ids` provided: runs those specific scenarios
2. If `scenario_tags` provided (and no `scenario_ids`): runs all scenarios matching ANY of the tags
3. If neither provided: runs ALL scenarios

**Response:** `202 Accepted`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "environment_id": "661f8400-e29b-41d4-a716-446655440001",
  "status": "queued",
  "browser": "chrome",
  "browser_version": "latest",
  "triggered_by": "user@example.com",
  "parallel": true,
  "started_at": null,
  "finished_at": null,
  "created_at": "2026-03-21T10:00:00Z"
}
```

**Error Codes:**
- `400` - No scenarios found matching tags / No scenarios available
- `404` - Environment not found

### Get Test Run

```http
GET /api/v1/runs/{run_id}
```

Returns run details including all step results.

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_ids": ["uuid-1", "uuid-2"],
  "environment_id": "661f8400-e29b-41d4-a716-446655440001",
  "status": "passed",
  "browser": "chrome",
  "browser_version": "latest",
  "triggered_by": "user@example.com",
  "parallel": true,
  "progress_message": "Completed",
  "started_at": "2026-03-21T10:00:00Z",
  "finished_at": "2026-03-21T10:05:00Z",
  "created_at": "2026-03-21T09:59:00Z",
  "results": [
    {
      "id": "772e8400-e29b-41d4-a716-446655440002",
      "step_name": "Given I am on the login page",
      "status": "passed",
      "duration_ms": 1234,
      "error_message": null,
      "screenshot_url": "/api/v1/screenshots/runs/550e8400.../step-0.png"
    },
    {
      "id": "883f8400-e29b-41d4-a716-446655440003",
      "step_name": "When I enter valid credentials",
      "status": "passed",
      "duration_ms": 567,
      "error_message": null,
      "screenshot_url": "/api/v1/screenshots/runs/550e8400.../step-1.png"
    },
    {
      "id": "994e8400-e29b-41d4-a716-446655440004",
      "step_name": "Then I should see the dashboard",
      "status": "failed",
      "duration_ms": 2345,
      "error_message": "Element not found: #dashboard-header",
      "screenshot_url": "/api/v1/screenshots/runs/550e8400.../step-2.png"
    }
  ]
}
```

### Get Run Status (Lightweight)

```http
GET /api/v1/runs/{run_id}/status
```

Optimized endpoint for polling (minimal payload).

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "started_at": "2026-03-21T10:00:00Z",
  "finished_at": null,
  "total_scenarios": 5,
  "completed_steps": 12
}
```

### Get Run Report

```http
GET /api/v1/runs/{run_id}/report
```

Returns HTML test report (pytest-html style).

**Response:** `200 OK` (`text/html`)

**Error Codes:**
- `404` - Test run not found / Report not yet generated

### Cancel Test Run

```http
DELETE /api/v1/runs/{run_id}
```

Cancels a queued or running test.

**Response:** `204 No Content`

**Error Codes:**
- `400` - Can only cancel queued or running tests
- `404` - Test run not found

### Retry Test Run

```http
POST /api/v1/runs/{run_id}/retry
```

Creates a new run with the same configuration as the original.

**Response:** `202 Accepted` with new run details

**Error Codes:**
- `400` - Cannot retry a run that is still in progress
- `404` - Test run not found

### Update Run Status (Internal)

```http
PATCH /api/v1/runs/{run_id}/status
```

Used by workers to update run status.

**Request Body:**

```json
{
  "status": "running"
}
```

**Valid Statuses:** `queued`, `running`, `passed`, `failed`, `cancelled`, `error`

### Get Screenshot

```http
GET /api/v1/screenshots/{path}
```

**Authentication:** Not required (URLs contain UUIDs and are not guessable)

Streams the screenshot image directly from S3/MinIO storage.

**Response:** `200 OK` (`image/png`)

**Headers:**
```
Cache-Control: public, max-age=86400
Content-Type: image/png
```

---

## Repositories

Repositories are Git sources for scenario files.

### List Repositories

```http
GET /api/v1/repos
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "main-tests",
    "git_url": "git@github.com:company/tests.git",
    "branch": "main",
    "sync_path": "scenarios",
    "last_synced": "2026-03-21T08:00:00Z"
  },
  {
    "id": "661f8400-e29b-41d4-a716-446655440001",
    "name": "integration-tests",
    "git_url": "git@github.com:company/integration.git",
    "branch": "develop",
    "sync_path": "features",
    "last_synced": "2026-03-21T07:30:00Z"
  }
]
```

### Create Repository

```http
POST /api/v1/repos
```

**Request Body:**

```json
{
  "name": "main-tests",
  "git_url": "git@github.com:company/tests.git",
  "branch": "main",
  "sync_path": "scenarios"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Unique repository name |
| `git_url` | string | required | Git clone URL (SSH or HTTPS) |
| `branch` | string | `main` | Branch to sync from |
| `sync_path` | string | `scenarios` | Path to `.feature` files |

**Response:** `201 Created`

**Error Codes:**
- `400` - Repository with this name already exists

### Sync Repository

```http
POST /api/v1/repos/{repo_id}/sync
```

Triggers a background sync for a specific repository.

**Response:** `200 OK`

```json
{
  "status": "sync_queued",
  "repo": "main-tests",
  "task_id": "celery-task-id-xxx"
}
```

### Sync All Repositories

```http
POST /api/v1/repos/sync-all
```

Triggers sync for all configured repositories.

**Response:** `200 OK`

```json
{
  "status": "sync_queued",
  "repos": ["main-tests", "integration-tests"],
  "task_id": "celery-task-id-xxx"
}
```

### Delete Repository

```http
DELETE /api/v1/repos/{repo_id}
```

Deletes a repository and all its associated scenarios.

**Response:** `204 No Content`

---

## Custom Steps

Custom step definitions extend Gherkin capabilities with Python/Playwright code.

### List Custom Steps

```http
GET /api/v1/steps
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repo_id` | UUID | Filter by repository |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": null,
    "name": "Login Step",
    "pattern": "I login as {role}",
    "code": "async def step(context, role):\n    page = context.page\n    if role == 'admin':\n        await page.fill('#email', 'admin@example.com')\n    await page.click('#submit')",
    "committed": false
  }
]
```

### Create Custom Step

```http
POST /api/v1/steps
```

**Request Body:**

```json
{
  "name": "Login Step",
  "pattern": "I login as {role}",
  "implementation": "async def step(context, role):\n    page = context.page\n    credentials = {\n        'admin': ('admin@example.com', 'admin123'),\n        'user': ('user@example.com', 'user123')\n    }\n    email, password = credentials.get(role, credentials['user'])\n    await page.fill('#email', email)\n    await page.fill('#password', password)\n    await page.click('#login-button')",
  "description": "Logs in as a specific user role",
  "repo_id": null
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Step name |
| `pattern` | string | yes | Gherkin pattern with `{placeholders}` |
| `implementation` | string | yes | Python async function code |
| `description` | string | no | Human-readable description |
| `repo_id` | UUID | no | Associated repository |

**Response:** `201 Created`

**Error Codes:**
- `400` - Step with this pattern already exists

### Get Custom Step

```http
GET /api/v1/steps/{step_id}
```

### Update Custom Step

```http
PUT /api/v1/steps/{step_id}
```

**Request Body:**

```json
{
  "name": "Updated Login Step",
  "pattern": "I login as {role} user",
  "implementation": "async def step(context, role):\n    ..."
}
```

**Note:** Updating pattern or implementation marks the step as uncommitted.

### Save Step to Repository

```http
POST /api/v1/steps/custom/{step_id}/save-to-repo
```

Commits the step definition to its associated Git repository.

**Response:** `200 OK`

```json
{
  "status": "committed",
  "step_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Codes:**
- `400` - Step is not associated with a repository
- `404` - Step not found

### Delete Custom Step

```http
DELETE /api/v1/steps/{step_id}
```

**Response:** `204 No Content`

---

## Schedules

Scheduled test runs using cron expressions.

### List Schedules

```http
GET /api/v1/schedules
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled_only` | boolean | Filter to enabled schedules only |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Nightly Smoke Tests",
    "cron_expression": "0 0 * * *",
    "cron_description": "Every day at midnight",
    "scenario_tags": ["smoke"],
    "scenario_ids": [],
    "environment_id": "661f8400-e29b-41d4-a716-446655440001",
    "environment_name": "staging",
    "browsers": ["chromium"],
    "enabled": true,
    "created_by": "user@example.com",
    "last_run_at": "2026-03-21T00:00:00Z",
    "next_run_at": "2026-03-22T00:00:00Z",
    "last_run_id": "772e8400-e29b-41d4-a716-446655440002",
    "created_at": "2026-03-01T10:00:00Z",
    "updated_at": "2026-03-20T15:00:00Z"
  }
]
```

### Create Schedule

```http
POST /api/v1/schedules
```

**Request Body:**

```json
{
  "name": "Nightly Smoke Tests",
  "cron_expression": "0 0 * * *",
  "scenario_tags": ["smoke"],
  "scenario_ids": [],
  "environment_id": "661f8400-e29b-41d4-a716-446655440001",
  "browsers": ["chromium", "firefox"],
  "enabled": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | - | Schedule name (1-100 chars) |
| `cron_expression` | string | yes | - | Standard 5-field cron |
| `environment_id` | UUID | yes | - | Target environment |
| `scenario_tags` | array | no | [] | Tags to filter scenarios |
| `scenario_ids` | array | no | [] | Specific scenario IDs |
| `browsers` | array | no | ["chromium"] | Browsers to test |
| `enabled` | boolean | no | true | Schedule active state |

**Common Cron Expressions:**

| Expression | Description |
|------------|-------------|
| `* * * * *` | Every minute |
| `*/15 * * * *` | Every 15 minutes |
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 * * 0` | Sundays at midnight |
| `0 0 1 * *` | First day of month |

**Response:** `201 Created`

**Error Codes:**
- `400` - Invalid cron expression / Scenarios not found
- `404` - Environment not found

### Get Schedule

```http
GET /api/v1/schedules/{schedule_id}
```

### Update Schedule

```http
PUT /api/v1/schedules/{schedule_id}
```

All fields are optional. Changing `cron_expression` or `enabled` recalculates `next_run_at`.

### Delete Schedule

```http
DELETE /api/v1/schedules/{schedule_id}
```

**Response:** `204 No Content`

### Toggle Schedule

```http
POST /api/v1/schedules/{schedule_id}/toggle
```

Toggles the enabled/disabled state.

**Response:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nightly Smoke Tests",
  "enabled": false,
  "next_run_at": null,
  ...
}
```

### Run Schedule Now

```http
POST /api/v1/schedules/{schedule_id}/run-now
```

Manually triggers a scheduled run immediately.

**Response:** `202 Accepted`

```json
{
  "message": "Schedule triggered",
  "schedule_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "celery-task-id-xxx"
}
```

### Describe Cron Expression

```http
GET /api/v1/schedules/cron/describe?expression={cron_expression}
```

**Example:**

```http
GET /api/v1/schedules/cron/describe?expression=0%209%20*%20*%201-5
```

**Response:** `200 OK`

```json
{
  "expression": "0 9 * * 1-5",
  "description": "At 9:00 AM on weekdays",
  "next_runs": [
    "2026-03-24T09:00:00",
    "2026-03-25T09:00:00",
    "2026-03-26T09:00:00",
    "2026-03-27T09:00:00",
    "2026-03-28T09:00:00"
  ]
}
```

---

## Test Sessions (Interactive)

Interactive test sessions allow step-by-step test execution with a visible browser window.

### Start Test Session

```http
POST /api/v1/test-session/start
```

**Request Body:**

```json
{
  "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
  "environment_id": "661f8400-e29b-41d4-a716-446655440001",
  "browser_type": "chromium"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `environment_id` | UUID | yes | - | Target environment |
| `scenario_id` | UUID | no | - | Pre-load a scenario |
| `browser_type` | string | no | `chromium` | Browser to use |

**Browser Types:** `chromium`, `firefox`, `webkit`, `chrome`, `edge`

**Response:** `201 Created`

```json
{
  "id": "772e8400-e29b-41d4-a716-446655440002",
  "status": "active",
  "browser_type": "chromium",
  "environment_name": "staging",
  "environment_base_url": "https://staging.example.com",
  "scenario_name": "User Login",
  "current_step_index": 0,
  "total_steps": 5,
  "started_at": "2026-03-21T10:00:00Z",
  "last_activity": "2026-03-21T10:00:00Z",
  "websocket_url": "/api/v1/test-session/772e8400.../ws"
}
```

### List Test Sessions

```http
GET /api/v1/test-sessions
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | true | Only return active/paused sessions |

### Load Scenario into Session

```http
POST /api/v1/test-session/{session_id}/load-scenario
```

**Request Body (by ID):**

```json
{
  "scenario_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Request Body (direct content):**

```json
{
  "content": "Feature: Quick Test\n\n  Scenario: Verify homepage\n    Given I am on the home page\n    Then I should see the welcome message"
}
```

**Response:** `200 OK`

```json
{
  "steps": [
    {
      "index": 0,
      "keyword": "Given",
      "text": "I am on the home page",
      "full": "Given I am on the home page",
      "status": "pending"
    },
    {
      "index": 1,
      "keyword": "Then",
      "text": "I should see the welcome message",
      "full": "Then I should see the welcome message",
      "status": "pending"
    }
  ],
  "total_steps": 2
}
```

### Execute Step

```http
POST /api/v1/test-session/{session_id}/step
```

**Request Body:**

```json
{
  "step_index": null
}
```

If `step_index` is null or omitted, executes the current step.

**Response:** `200 OK`

```json
{
  "step_name": "Given I am on the home page",
  "status": "passed",
  "duration_ms": 1523,
  "error_message": null,
  "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "current_url": "https://staging.example.com/",
  "page_title": "Home - Example App",
  "next_step_index": 1,
  "total_steps": 5
}
```

**Status Values:** `passed`, `failed`, `skipped`, `error`, `completed`

### Skip Step

```http
POST /api/v1/test-session/{session_id}/skip
```

Marks the current step as skipped and moves to the next.

### Take Screenshot

```http
POST /api/v1/test-session/{session_id}/screenshot
```

**Response:** `200 OK`

```json
{
  "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "current_url": "https://staging.example.com/dashboard",
  "page_title": "Dashboard - Example App"
}
```

### Get Session Status

```http
GET /api/v1/test-session/{session_id}/status
```

**Response:** `200 OK`

```json
{
  "id": "772e8400-e29b-41d4-a716-446655440002",
  "status": "active",
  "current_step_index": 2,
  "total_steps": 5,
  "current_url": "https://staging.example.com/dashboard",
  "page_title": "Dashboard",
  "step_results": [
    {
      "step_index": 0,
      "step_name": "Given I am on the login page",
      "status": "passed",
      "duration_ms": 1234,
      "error_message": null,
      "executed_at": "2026-03-21T10:01:00Z"
    }
  ],
  "logs": [
    "[10:01:00] Navigated to /login",
    "[10:01:01] Filled email field",
    "[10:01:02] Clicked login button"
  ]
}
```

### Navigate to URL

```http
POST /api/v1/test-session/{session_id}/navigate
```

**Request Body:**

```json
{
  "url": "https://staging.example.com/settings"
}
```

### Run Custom Action

```http
POST /api/v1/test-session/{session_id}/action
```

**Request Body:**

```json
{
  "action": "click",
  "selector": "#submit-button",
  "value": ""
}
```

| Action | Description | Requires Selector | Requires Value |
|--------|-------------|-------------------|----------------|
| `click` | Click element | yes | no |
| `dblclick` | Double-click element | yes | no |
| `fill` | Fill input field | yes | yes |
| `select` | Select dropdown option | yes | yes (option value) |
| `check` | Check checkbox | yes | no |
| `uncheck` | Uncheck checkbox | yes | no |
| `hover` | Hover over element | yes | no |

### Pause Session

```http
POST /api/v1/test-session/{session_id}/pause
```

**Response:** `200 OK`

```json
{
  "status": "paused",
  "session_id": "772e8400-e29b-41d4-a716-446655440002"
}
```

### Resume Session

```http
POST /api/v1/test-session/{session_id}/resume
```

**Response:** `200 OK`

```json
{
  "status": "active",
  "session_id": "772e8400-e29b-41d4-a716-446655440002"
}
```

### End Session

```http
DELETE /api/v1/test-session/{session_id}
```

Closes the browser and marks the session as terminated.

**Response:** `204 No Content`

---

## Users (Admin Only)

User management endpoints require admin role.

### List Users

```http
GET /api/v1/users
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in name or email (case-insensitive) |

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@company.com",
    "name": "Admin User",
    "picture_url": "https://lh3.googleusercontent.com/...",
    "workspace_domain": "company.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-03-01T10:00:00Z",
    "last_login": "2026-03-21T09:00:00Z"
  }
]
```

### Get User

```http
GET /api/v1/users/{user_id}
```

### Update User Role

```http
PUT /api/v1/users/{user_id}/role
```

**Request Body:**

```json
{
  "role": "admin"
}
```

**Roles:** `admin`, `user`

**Restrictions:**
- Cannot demote yourself from admin

**Error Codes:**
- `400` - Cannot demote yourself from admin
- `404` - User not found

### Toggle User Active Status

```http
PUT /api/v1/users/{user_id}/active
```

**Request Body:**

```json
{
  "is_active": false
}
```

**Restrictions:**
- Cannot deactivate yourself

---

## API Keys

Manage API keys for programmatic access.

### List API Keys

```http
GET /api/v1/auth/keys
```

**Response:** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "CI Pipeline Key",
    "key_prefix": "a1b2c3d4",
    "environment_ids": [],
    "created_at": "2026-03-01T10:00:00Z",
    "last_used_at": "2026-03-21T08:30:00Z",
    "active": true
  }
]
```

### Create API Key

```http
POST /api/v1/auth/keys
```

**Request Body:**

```json
{
  "name": "CI Pipeline Key",
  "environment_ids": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Key name (1-100 chars) |
| `environment_ids` | array | no | Restrict to specific environments |

**Response:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "CI Pipeline Key",
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "key_prefix": "a1b2c3d4",
  "environment_ids": [],
  "created_at": "2026-03-21T10:00:00Z",
  "active": true
}
```

**IMPORTANT:** The full `key` is only returned once at creation time. Store it securely immediately.

**Error Codes:**
- `400` - An active API key with this name already exists

### Get API Key

```http
GET /api/v1/auth/keys/{key_id}
```

Returns key metadata with masked key (only prefix shown).

### Revoke API Key

```http
DELETE /api/v1/auth/keys/{key_id}
```

Performs a soft delete (sets `active=false`). The key can no longer be used for authentication.

**Response:** `204 No Content`

---

## Browsers

Available browser configurations.

### List Browsers

```http
GET /api/v1/browsers
```

**Response:** `200 OK`

```json
{
  "browsers": [
    {
      "name": "chrome",
      "display_name": "Google Chrome",
      "versions": ["latest", "stable", "beta", "dev"],
      "default": "latest"
    },
    {
      "name": "firefox",
      "display_name": "Mozilla Firefox",
      "versions": ["latest", "stable", "beta", "dev"],
      "default": "latest"
    }
  ],
  "note": "Version pinning to specific versions available in Phase 3"
}
```

---

## CI/CD Integration

### GitHub Actions

Complete workflow for running Sliples tests in GitHub Actions:

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
      tags:
        description: 'Test tags (comma-separated)'
        required: false
        default: 'smoke'

env:
  SLIPLES_URL: https://sliples.example.com
  SLIPLES_API_KEY: ${{ secrets.SLIPLES_API_KEY }}

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Trigger Sliples Test Run
        id: trigger
        run: |
          # Determine environment and tags
          ENVIRONMENT="${{ github.event.inputs.environment || 'staging' }}"
          TAGS="${{ github.event.inputs.tags || 'smoke' }}"

          # Convert comma-separated tags to JSON array
          TAGS_JSON=$(echo "$TAGS" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$";""))')

          echo "Running tests with tags: $TAGS_JSON on $ENVIRONMENT"

          # Trigger test run
          RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
            -H "X-API-Key: $SLIPLES_API_KEY" \
            -H "Content-Type: application/json" \
            -d "{\"scenario_tags\": $TAGS_JSON, \"environment\": \"$ENVIRONMENT\", \"browsers\": [\"chrome\"]}" \
            "$SLIPLES_URL/api/v1/runs")

          HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
          BODY=$(echo "$RESPONSE" | sed '$d')

          if [[ "$HTTP_CODE" != "202" ]]; then
            echo "Failed to trigger test run: $BODY"
            exit 1
          fi

          RUN_ID=$(echo "$BODY" | jq -r '.id')
          echo "run_id=$RUN_ID" >> $GITHUB_OUTPUT
          echo "Test run started: $RUN_ID"

      - name: Wait for Test Completion
        id: wait
        run: |
          RUN_ID="${{ steps.trigger.outputs.run_id }}"
          MAX_WAIT=1800  # 30 minutes
          INTERVAL=10
          ELAPSED=0

          echo "Waiting for test run $RUN_ID to complete..."

          while [[ $ELAPSED -lt $MAX_WAIT ]]; do
            RESPONSE=$(curl -s \
              -H "X-API-Key: $SLIPLES_API_KEY" \
              "$SLIPLES_URL/api/v1/runs/$RUN_ID/status")

            STATUS=$(echo "$RESPONSE" | jq -r '.status')
            COMPLETED=$(echo "$RESPONSE" | jq -r '.completed_steps // 0')
            TOTAL=$(echo "$RESPONSE" | jq -r '.total_scenarios // 0')

            echo "[$ELAPSED s] Status: $STATUS ($COMPLETED steps completed)"

            case $STATUS in
              passed)
                echo "status=passed" >> $GITHUB_OUTPUT
                echo "All tests passed!"
                exit 0
                ;;
              failed)
                echo "status=failed" >> $GITHUB_OUTPUT
                echo "Tests failed!"
                exit 1
                ;;
              error)
                echo "status=error" >> $GITHUB_OUTPUT
                echo "Test run errored!"
                exit 1
                ;;
              cancelled)
                echo "status=cancelled" >> $GITHUB_OUTPUT
                echo "Test run was cancelled!"
                exit 1
                ;;
            esac

            sleep $INTERVAL
            ELAPSED=$((ELAPSED + INTERVAL))
          done

          echo "Timeout waiting for test completion"
          exit 1

      - name: Download Test Report
        if: always()
        run: |
          RUN_ID="${{ steps.trigger.outputs.run_id }}"

          curl -s -H "X-API-Key: $SLIPLES_API_KEY" \
            "$SLIPLES_URL/api/v1/runs/$RUN_ID/report" > test-report.html

          echo "Report saved to test-report.html"

      - name: Upload Test Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: sliples-test-report
          path: test-report.html
          retention-days: 30

      - name: Post Summary
        if: always()
        run: |
          RUN_ID="${{ steps.trigger.outputs.run_id }}"
          STATUS="${{ steps.wait.outputs.status || 'unknown' }}"

          # Get detailed results
          RESULTS=$(curl -s -H "X-API-Key: $SLIPLES_API_KEY" \
            "$SLIPLES_URL/api/v1/runs/$RUN_ID")

          PASSED=$(echo "$RESULTS" | jq '[.results[]? | select(.status=="passed")] | length')
          FAILED=$(echo "$RESULTS" | jq '[.results[]? | select(.status=="failed")] | length')

          echo "## Sliples Test Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Metric | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|--------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Status | $STATUS |" >> $GITHUB_STEP_SUMMARY
          echo "| Passed | $PASSED |" >> $GITHUB_STEP_SUMMARY
          echo "| Failed | $FAILED |" >> $GITHUB_STEP_SUMMARY
          echo "| Run ID | \`$RUN_ID\` |" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "[View Full Report]($SLIPLES_URL/runs/$RUN_ID)" >> $GITHUB_STEP_SUMMARY
```

### GitLab CI

Complete GitLab CI configuration:

```yaml
stages:
  - test

variables:
  SLIPLES_URL: https://sliples.example.com

.sliples_test:
  image: alpine:latest
  before_script:
    - apk add --no-cache curl jq

e2e-smoke-tests:
  extends: .sliples_test
  stage: test
  variables:
    TEST_TAGS: "smoke"
    TEST_ENVIRONMENT: "staging"
  script:
    # Trigger test run
    - |
      echo "Triggering Sliples tests with tags: $TEST_TAGS on $TEST_ENVIRONMENT"

      TAGS_JSON=$(echo "$TEST_TAGS" | jq -R 'split(",") | map(gsub("^\\s+|\\s+$";""))')

      RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
        -H "X-API-Key: $SLIPLES_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"scenario_tags\": $TAGS_JSON, \"environment\": \"$TEST_ENVIRONMENT\"}" \
        "$SLIPLES_URL/api/v1/runs")

      HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
      BODY=$(echo "$RESPONSE" | sed '$d')

      if [ "$HTTP_CODE" != "202" ]; then
        echo "Failed to trigger test run: $BODY"
        exit 1
      fi

      RUN_ID=$(echo "$BODY" | jq -r '.id')
      echo "RUN_ID=$RUN_ID" > run.env
      echo "Test run started: $RUN_ID"

    # Wait for completion
    - |
      source run.env
      MAX_WAIT=1800
      ELAPSED=0

      while [ $ELAPSED -lt $MAX_WAIT ]; do
        RESPONSE=$(curl -s \
          -H "X-API-Key: $SLIPLES_API_KEY" \
          "$SLIPLES_URL/api/v1/runs/$RUN_ID/status")

        STATUS=$(echo "$RESPONSE" | jq -r '.status')
        echo "[$ELAPSED s] Status: $STATUS"

        case $STATUS in
          passed)
            echo "All tests passed!"
            break
            ;;
          failed|error|cancelled)
            echo "Tests finished with status: $STATUS"
            exit 1
            ;;
        esac

        sleep 10
        ELAPSED=$((ELAPSED + 10))
      done

      if [ $ELAPSED -ge $MAX_WAIT ]; then
        echo "Timeout waiting for test completion"
        exit 1
      fi

    # Download report
    - |
      source run.env
      curl -s -H "X-API-Key: $SLIPLES_API_KEY" \
        "$SLIPLES_URL/api/v1/runs/$RUN_ID/report" > report.html

  artifacts:
    paths:
      - report.html
    reports:
      junit: junit-report.xml
    when: always
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

e2e-regression-tests:
  extends: .sliples_test
  stage: test
  variables:
    TEST_TAGS: "regression"
    TEST_ENVIRONMENT: "staging"
  script:
    # Same script as above, or use a shared script
    - !reference [e2e-smoke-tests, script]
  artifacts:
    paths:
      - report.html
    when: always
    expire_in: 1 week
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: always
    - when: manual
      allow_failure: true
```

### Jenkins

Declarative Pipeline for Jenkins:

```groovy
pipeline {
    agent any

    environment {
        SLIPLES_URL = 'https://sliples.example.com'
        SLIPLES_API_KEY = credentials('sliples-api-key')
    }

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['staging', 'production'],
            description: 'Target test environment'
        )
        string(
            name: 'TAGS',
            defaultValue: 'smoke',
            description: 'Test tags (comma-separated)'
        )
        choice(
            name: 'BROWSER',
            choices: ['chrome', 'firefox', 'chromium'],
            description: 'Browser for test execution'
        )
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Trigger Tests') {
            steps {
                script {
                    // Parse tags into JSON array
                    def tagsList = params.TAGS.split(',').collect { it.trim() }

                    // Build request body
                    def requestBody = [
                        scenario_tags: tagsList,
                        environment: params.ENVIRONMENT,
                        browsers: [params.BROWSER],
                        parallel: true
                    ]

                    echo "Triggering Sliples tests..."
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "Tags: ${tagsList}"
                    echo "Browser: ${params.BROWSER}"

                    // Trigger test run
                    def response = httpRequest(
                        url: "${SLIPLES_URL}/api/v1/runs",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        requestBody: groovy.json.JsonOutput.toJson(requestBody),
                        validResponseCodes: '202'
                    )

                    def runData = readJSON text: response.content
                    env.RUN_ID = runData.id

                    echo "Test run started: ${env.RUN_ID}"
                }
            }
        }

        stage('Wait for Completion') {
            steps {
                script {
                    def maxAttempts = 180  // 30 minutes at 10s intervals
                    def attempt = 0
                    def finalStatus = ''

                    while (attempt < maxAttempts) {
                        def statusResponse = httpRequest(
                            url: "${SLIPLES_URL}/api/v1/runs/${env.RUN_ID}/status",
                            httpMode: 'GET',
                            customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                            validResponseCodes: '200'
                        )

                        def statusData = readJSON text: statusResponse.content
                        def status = statusData.status
                        def completed = statusData.completed_steps ?: 0
                        def total = statusData.total_scenarios ?: 0

                        echo "[${attempt * 10}s] Status: ${status} (${completed} steps completed)"

                        if (status in ['passed', 'failed', 'error', 'cancelled']) {
                            finalStatus = status
                            break
                        }

                        sleep(10)
                        attempt++
                    }

                    if (attempt >= maxAttempts) {
                        error("Timeout waiting for test completion")
                    }

                    env.FINAL_STATUS = finalStatus

                    if (finalStatus != 'passed') {
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('Download Report') {
            steps {
                script {
                    def reportResponse = httpRequest(
                        url: "${SLIPLES_URL}/api/v1/runs/${env.RUN_ID}/report",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        validResponseCodes: '200'
                    )

                    writeFile file: 'sliples-report.html', text: reportResponse.content
                    echo "Report saved to sliples-report.html"
                }
            }
        }

        stage('Get Results') {
            steps {
                script {
                    def resultsResponse = httpRequest(
                        url: "${SLIPLES_URL}/api/v1/runs/${env.RUN_ID}",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        validResponseCodes: '200'
                    )

                    def results = readJSON text: resultsResponse.content
                    def passed = results.results?.count { it.status == 'passed' } ?: 0
                    def failed = results.results?.count { it.status == 'failed' } ?: 0
                    def total = results.results?.size() ?: 0

                    echo """
                    ====================================
                    SLIPLES TEST RESULTS
                    ====================================
                    Status: ${env.FINAL_STATUS}
                    Passed: ${passed}/${total}
                    Failed: ${failed}/${total}
                    Run ID: ${env.RUN_ID}
                    ====================================
                    """

                    // Fail build if tests failed
                    if (env.FINAL_STATUS != 'passed') {
                        error("Tests failed with status: ${env.FINAL_STATUS}")
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'sliples-report.html', allowEmptyArchive: true

            publishHTML(target: [
                allowMissing: true,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'sliples-report.html',
                reportName: 'Sliples Test Report'
            ])
        }

        failure {
            script {
                if (env.RUN_ID) {
                    echo "View failed test details: ${SLIPLES_URL}/runs/${env.RUN_ID}"
                }
            }
        }
    }
}
```

### Python Script (Reusable)

A reusable Python script for CI/CD integration:

```python
#!/usr/bin/env python3
"""
Sliples CI/CD Integration Script

Usage:
    python sliples_runner.py --tags smoke,regression --env staging
    python sliples_runner.py --scenario-ids uuid1,uuid2 --env production
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

import requests


class SliplesClient:
    """Client for Sliples API."""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
        })

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make API request."""
        url = f"{self.base_url}/api/v1{path}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def trigger_run(
        self,
        environment: str,
        tags: Optional[list] = None,
        scenario_ids: Optional[list] = None,
        browsers: Optional[list] = None,
    ) -> dict:
        """Trigger a new test run."""
        payload = {
            'environment': environment,
            'scenario_tags': tags or [],
            'scenario_ids': scenario_ids or [],
            'browsers': browsers or ['chrome'],
            'parallel': True,
        }
        return self._request('POST', '/runs', json=payload)

    def get_run_status(self, run_id: str) -> dict:
        """Get lightweight run status."""
        return self._request('GET', f'/runs/{run_id}/status')

    def get_run_details(self, run_id: str) -> dict:
        """Get full run details with results."""
        return self._request('GET', f'/runs/{run_id}')

    def get_report(self, run_id: str) -> str:
        """Download HTML report."""
        url = f"{self.base_url}/api/v1/runs/{run_id}/report"
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def wait_for_completion(
        self,
        run_id: str,
        timeout: int = 1800,
        poll_interval: int = 10,
        callback=None,
    ) -> str:
        """Wait for run to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_data = self.get_run_status(run_id)
            status = status_data['status']
            elapsed = int(time.time() - start_time)

            if callback:
                callback(status_data, elapsed)
            else:
                completed = status_data.get('completed_steps', 0)
                print(f"[{elapsed}s] Status: {status} ({completed} steps)")

            if status in ('passed', 'failed', 'error', 'cancelled'):
                return status

            time.sleep(poll_interval)

        raise TimeoutError(f"Test run {run_id} timed out after {timeout}s")


def main():
    parser = argparse.ArgumentParser(description='Run Sliples E2E tests')
    parser.add_argument(
        '--url',
        default=os.environ.get('SLIPLES_URL', 'https://sliples.example.com'),
        help='Sliples API URL',
    )
    parser.add_argument(
        '--api-key',
        default=os.environ.get('SLIPLES_API_KEY'),
        help='Sliples API key',
    )
    parser.add_argument(
        '--env', '-e',
        required=True,
        help='Target environment name',
    )
    parser.add_argument(
        '--tags', '-t',
        help='Comma-separated test tags',
    )
    parser.add_argument(
        '--scenario-ids',
        help='Comma-separated scenario IDs',
    )
    parser.add_argument(
        '--browsers', '-b',
        default='chrome',
        help='Comma-separated browsers (default: chrome)',
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=1800,
        help='Timeout in seconds (default: 1800)',
    )
    parser.add_argument(
        '--output', '-o',
        default='sliples-report.html',
        help='Output report file path',
    )
    parser.add_argument(
        '--json-output',
        help='Output results as JSON to file',
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required (--api-key or SLIPLES_API_KEY env var)")
        sys.exit(1)

    # Parse inputs
    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None
    scenario_ids = [s.strip() for s in args.scenario_ids.split(',')] if args.scenario_ids else None
    browsers = [b.strip() for b in args.browsers.split(',')]

    # Initialize client
    client = SliplesClient(args.url, args.api_key)

    print(f"{'='*50}")
    print(f"SLIPLES TEST RUN")
    print(f"{'='*50}")
    print(f"URL: {args.url}")
    print(f"Environment: {args.env}")
    print(f"Tags: {tags}")
    print(f"Browsers: {browsers}")
    print(f"{'='*50}")

    try:
        # Trigger run
        print("\nTriggering test run...")
        run = client.trigger_run(
            environment=args.env,
            tags=tags,
            scenario_ids=scenario_ids,
            browsers=browsers,
        )
        run_id = run['id']
        print(f"Run started: {run_id}")

        # Wait for completion
        print("\nWaiting for completion...")
        final_status = client.wait_for_completion(run_id, timeout=args.timeout)

        # Get detailed results
        print("\nFetching results...")
        results = client.get_run_details(run_id)

        passed = sum(1 for r in results.get('results', []) if r['status'] == 'passed')
        failed = sum(1 for r in results.get('results', []) if r['status'] == 'failed')
        total = len(results.get('results', []))

        print(f"\n{'='*50}")
        print(f"RESULTS")
        print(f"{'='*50}")
        print(f"Status: {final_status.upper()}")
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {failed}/{total}")
        print(f"Run ID: {run_id}")
        print(f"{'='*50}")

        # Download report
        print(f"\nSaving report to {args.output}...")
        report = client.get_report(run_id)
        with open(args.output, 'w') as f:
            f.write(report)

        # Save JSON results if requested
        if args.json_output:
            with open(args.json_output, 'w') as f:
                json.dump({
                    'run_id': run_id,
                    'status': final_status,
                    'passed': passed,
                    'failed': failed,
                    'total': total,
                    'results': results.get('results', []),
                }, f, indent=2, default=str)
            print(f"JSON results saved to {args.json_output}")

        # Exit with appropriate code
        sys.exit(0 if final_status == 'passed' else 1)

    except requests.HTTPError as e:
        print(f"API Error: {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except TimeoutError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Errors (422)

Field-level validation errors include location and type:

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "base_url"],
      "msg": "Invalid URL format",
      "type": "value_error"
    }
  ]
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `202` | Accepted (async operation queued) |
| `204` | No Content (successful delete) |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Missing or invalid authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `422` | Validation Error - Invalid request body |
| `500` | Internal Server Error |
| `503` | Service Unavailable - Dependency failure |

---

## WebSocket Endpoints

### Test Run Updates

```websocket
WS /api/v1/ws/runs/{run_id}
```

Real-time updates for test run progress.

**Connection:** Connect after triggering a run to receive live updates.

**Keepalive:** Send `ping` message to receive `pong` response.

**Message Types:**

```json
// Status change
{
  "type": "status_update",
  "data": {
    "id": "run-uuid",
    "old_status": "queued",
    "new_status": "running",
    "started_at": "2026-03-21T10:00:00Z",
    "finished_at": null
  }
}

// New step result
{
  "type": "result_added",
  "data": {
    "id": "result-uuid",
    "step_name": "Given I am on the login page",
    "status": "passed",
    "duration_ms": 1234,
    "error_message": null,
    "screenshot_url": "/api/v1/screenshots/..."
  }
}

// Progress update
{
  "type": "progress",
  "data": {
    "id": "run-uuid",
    "status": "running",
    "progress_message": "Executing step 5/10",
    "total_scenarios": 3,
    "completed_steps": 5,
    "passed": 4,
    "failed": 1
  }
}

// Run completed
{
  "type": "completed",
  "data": {
    "id": "run-uuid",
    "status": "passed",
    "started_at": "2026-03-21T10:00:00Z",
    "finished_at": "2026-03-21T10:05:00Z",
    "total_results": 10,
    "passed": 9,
    "failed": 1,
    "skipped": 0
  }
}

// Error
{
  "type": "error",
  "data": {
    "message": "Error description"
  }
}
```

### Test Session Updates

```websocket
WS /api/v1/test-session/{session_id}/ws
```

Real-time updates for interactive test sessions.

**Message Types:**

```json
// Status update (sent every 2 seconds)
{
  "type": "status",
  "data": {
    "session_id": "session-uuid",
    "status": "active",
    "current_step_index": 2,
    "total_steps": 5,
    "current_url": "https://example.com/page",
    "page_title": "Page Title",
    "step_results": [...],  // Last 10 results
    "logs": [...]           // Last 20 log entries
  }
}

// Error
{
  "type": "error",
  "message": "Session not found or terminated"
}
```

---

## Rate Limiting

Currently, Sliples does not enforce rate limits. However, it is recommended to:

1. **Use WebSockets** for real-time updates instead of polling
2. **Implement exponential backoff** for API errors
3. **Limit parallel test runs** based on your worker capacity

---

## OpenAPI Documentation

The complete OpenAPI specification is available at:

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (documentation) |
| `/openapi.json` | OpenAPI JSON schema |

---

## Versioning

The API uses URL versioning. The current version is `v1`.

- All endpoints are prefixed with `/api/v1`
- Future versions will be available at `/api/v2`, etc.
- Backward compatibility maintained for at least 12 months after new version release
