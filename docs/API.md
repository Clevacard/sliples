# Sliples API Reference

Complete API documentation for the Sliples Web UI Automation Testing Platform.

**Base URL:** `https://your-sliples-instance.com/api/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
   - [Health](#health)
   - [Authentication & API Keys](#authentication--api-keys)
   - [Scenarios](#scenarios)
   - [Test Runs](#test-runs)
   - [Environments](#environments)
   - [Repositories](#repositories)
   - [Schedules](#schedules)
   - [Custom Steps](#custom-steps)
   - [Browsers](#browsers)
   - [Users](#users)
   - [Interactive Test Sessions](#interactive-test-sessions)
   - [Seed Data](#seed-data)
5. [Code Examples](#code-examples)

---

## Authentication

Sliples supports two authentication methods:

### 1. API Key Authentication (for CI/CD)

Include your API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

API keys are generated through the API or UI and are suitable for programmatic access from CI/CD pipelines.

### 2. JWT Authentication (for UI/User Sessions)

After logging in via Google Workspace SSO, a JWT token is set as an httpOnly cookie (`access_token`). For programmatic use, include the token in the Authorization header:

```
Authorization: Bearer your-jwt-token
```

### Creating an API Key

```bash
curl -X POST "https://sliples.example.com/api/v1/auth/keys" \
  -H "X-API-Key: your-existing-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline Key",
    "environment_ids": ["uuid-of-environment"]
  }'
```

Response (store the `key` securely - it will not be shown again):

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "CI/CD Pipeline Key",
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "key_prefix": "a1b2c3d4",
  "environment_ids": ["uuid-of-environment"],
  "created_at": "2026-03-21T10:00:00Z",
  "active": true
}
```

---

## Error Handling

All API errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Status Code | Meaning |
|-------------|---------|
| `200` | Success |
| `201` | Created |
| `202` | Accepted (async operation started) |
| `204` | No Content (successful deletion) |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Invalid or missing authentication |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource does not exist |
| `422` | Validation Error - Request body validation failed |
| `500` | Internal Server Error |

### Validation Errors

For validation errors (422), the response includes field-level details:

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Rate limiting is applied per API key:

- **Default limit:** 100 requests per minute
- **Burst limit:** 20 requests per second

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1679500800
```

---

## Endpoints

### Health

#### Check System Health

```
GET /health
```

Returns the health status of the API and its dependencies.

**Response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

Possible `status` values: `healthy`, `degraded`

---

### Authentication & API Keys

#### Google SSO Login

```
GET /auth/google/login?redirect=true
```

Initiates Google OAuth2 login. By default redirects to Google. Set `redirect=false` to get the URL as JSON.

#### Google SSO Callback

```
GET /auth/google/callback
```

Handles the OAuth2 callback from Google. Sets a session cookie and redirects to the frontend.

#### Get Current User

```
GET /auth/me
```

Returns information about the currently authenticated user.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "name": "John Doe",
  "picture_url": "https://...",
  "workspace_domain": "example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-03-20T10:00:00Z",
  "last_login": "2026-03-21T09:00:00Z"
}
```

#### Logout

```
POST /auth/logout
```

Clears the session cookie.

#### List API Keys

```
GET /auth/keys
```

Lists all active API keys (masked).

#### Create API Key

```
POST /auth/keys
```

**Request Body:**

```json
{
  "name": "My API Key",
  "environment_ids": ["uuid-1", "uuid-2"]
}
```

**Response:** Returns the full key (only shown once).

#### Get API Key

```
GET /auth/keys/{key_id}
```

Returns API key metadata (masked).

#### Revoke API Key

```
DELETE /auth/keys/{key_id}
```

Soft-deletes an API key.

---

### Scenarios

#### List Scenarios

```
GET /scenarios
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tag` | string | Filter by single tag |
| `tags` | string | Comma-separated tags (OR filter) |
| `repo_id` | UUID | Filter by repository |
| `search` | string | Search in scenario name |
| `limit` | int | Max results (default: 100, max: 500) |
| `offset` | int | Pagination offset |

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "uuid-of-repo",
    "name": "User can login successfully",
    "feature_path": "features/login.feature",
    "tags": ["smoke", "login"],
    "updated_at": "2026-03-21T10:00:00Z"
  }
]
```

#### Get Scenario

```
GET /scenarios/{scenario_id}
```

Returns scenario details including full Gherkin content.

#### Get Scenario Content

```
GET /scenarios/{scenario_id}/content
```

Returns just the Gherkin content.

#### Create Scenario

```
POST /scenarios
```

**Request Body:**

```json
{
  "name": "User can login",
  "feature_path": "features/login.feature",
  "content": "Feature: Login\n  Scenario: ...",
  "tags": ["smoke", "login"],
  "repo_id": "uuid-of-repo"
}
```

#### Update Scenario Content

```
PUT /scenarios/{scenario_id}/content
```

**Request Body:**

```json
{
  "content": "Feature: Login\n  Scenario: Updated..."
}
```

#### Delete Scenario

```
DELETE /scenarios/{scenario_id}
```

#### List All Tags

```
GET /scenarios/tags
```

Returns all unique tags across scenarios.

**Response:**

```json
{
  "tags": ["smoke", "regression", "login", "checkout"],
  "count": 4
}
```

#### Sync Scenarios

```
POST /scenarios/sync
```

Triggers background sync of scenarios from all configured repositories.

**Response:**

```json
{
  "status": "sync_queued",
  "message": "Sync started for 3 repositories",
  "task_id": "celery-task-id",
  "repos": [
    {"id": "uuid-1", "name": "main-tests"}
  ]
}
```

---

### Test Runs

#### List Test Runs

```
GET /runs
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status_filter` | string | Filter by status (queued, running, passed, failed, cancelled, error) |
| `environment_id` | UUID | Filter by environment |
| `limit` | int | Max results (default: 50) |
| `offset` | int | Pagination offset |

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "scenario_ids": ["uuid-1", "uuid-2"],
    "environment_id": "uuid-of-env",
    "status": "passed",
    "browser": "chrome",
    "browser_version": "latest",
    "triggered_by": "user@example.com",
    "parallel": true,
    "started_at": "2026-03-21T10:00:00Z",
    "finished_at": "2026-03-21T10:05:00Z",
    "created_at": "2026-03-21T10:00:00Z"
  }
]
```

#### Create Test Run

```
POST /runs
```

Triggers a new test run. Returns 202 Accepted as execution is asynchronous.

**Request Body:**

```json
{
  "scenario_tags": ["smoke"],
  "scenario_ids": [],
  "environment": "staging",
  "browsers": ["chrome", "firefox"],
  "parallel": true
}
```

Either `scenario_tags` or `scenario_ids` should be provided. If neither, all scenarios are run.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_ids": ["uuid-1", "uuid-2"],
  "environment_id": "uuid-of-env",
  "status": "queued",
  "browser": "chrome",
  "browser_version": "latest",
  "parallel": true,
  "created_at": "2026-03-21T10:00:00Z"
}
```

#### Get Test Run

```
GET /runs/{run_id}
```

Returns run details including step results.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "passed",
  "results": [
    {
      "id": "uuid",
      "step_name": "Given I am on the login page",
      "status": "passed",
      "duration_ms": 1234,
      "error_message": null,
      "screenshot_url": "/api/v1/screenshots/uuid/step1.png"
    }
  ]
}
```

#### Get Run Status (Lightweight)

```
GET /runs/{run_id}/status
```

Returns just the status (use for polling).

**Response:**

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

#### Get Run Report

```
GET /runs/{run_id}/report
```

Returns the HTML report (pytest-html style).

**Response:** `text/html`

#### Cancel Test Run

```
DELETE /runs/{run_id}
```

Cancels a queued or running test.

#### Retry Test Run

```
POST /runs/{run_id}/retry
```

Creates a new run with the same configuration.

#### Update Run Status

```
PATCH /runs/{run_id}/status
```

**Request Body:**

```json
{
  "status": "running"
}
```

Valid statuses: `queued`, `running`, `passed`, `failed`, `cancelled`, `error`

---

### Environments

#### List Environments

```
GET /environments
```

#### Create Environment

```
POST /environments
```

**Request Body:**

```json
{
  "name": "staging",
  "base_url": "https://staging.example.com",
  "credentials_env": "STAGING_CREDENTIALS",
  "variables": {
    "TIMEOUT": "30",
    "FEATURE_FLAG": "true"
  },
  "retention_days": 365,
  "browser_configs": [
    {
      "browser": "chrome",
      "version": "latest",
      "channel": "stable"
    }
  ]
}
```

**Browser options:** chrome, chromium, firefox, webkit, edge
**Channel options:** stable, beta, dev, canary

#### Get Environment

```
GET /environments/{environment_id}
```

#### Update Environment

```
PUT /environments/{environment_id}
```

#### Delete Environment

```
DELETE /environments/{environment_id}
```

#### List Browser Configs

```
GET /environments/{environment_id}/browsers
```

#### Add Browser Config

```
POST /environments/{environment_id}/browsers
```

**Request Body:**

```json
{
  "browser": "firefox",
  "version": "latest",
  "channel": "stable"
}
```

#### Update Browser Config

```
PUT /environments/{environment_id}/browsers/{browser_config_id}
```

#### Delete Browser Config

```
DELETE /environments/{environment_id}/browsers/{browser_config_id}
```

---

### Repositories

#### List Repositories

```
GET /repos
```

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "main-tests",
    "git_url": "git@github.com:org/tests.git",
    "branch": "main",
    "sync_path": "scenarios",
    "last_synced": "2026-03-21T10:00:00Z"
  }
]
```

#### Create Repository

```
POST /repos
```

**Request Body:**

```json
{
  "name": "main-tests",
  "git_url": "git@github.com:org/tests.git",
  "branch": "main",
  "sync_path": "scenarios"
}
```

#### Sync Repository

```
POST /repos/{repo_id}/sync
```

Triggers a sync for a specific repository.

**Response:**

```json
{
  "status": "sync_queued",
  "repo": "main-tests",
  "task_id": "celery-task-id"
}
```

#### Sync All Repositories

```
POST /repos/sync-all
```

Triggers sync for all configured repositories.

#### Delete Repository

```
DELETE /repos/{repo_id}
```

---

### Schedules

#### List Schedules

```
GET /schedules
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled_only` | bool | Only return enabled schedules |

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Nightly Smoke Tests",
    "cron_expression": "0 0 * * *",
    "cron_description": "Every day at midnight",
    "scenario_tags": ["smoke"],
    "scenario_ids": [],
    "environment_id": "uuid-of-env",
    "environment_name": "production",
    "browsers": ["chrome"],
    "enabled": true,
    "last_run_at": "2026-03-21T00:00:00Z",
    "next_run_at": "2026-03-22T00:00:00Z",
    "created_at": "2026-03-20T10:00:00Z"
  }
]
```

#### Create Schedule

```
POST /schedules
```

**Request Body:**

```json
{
  "name": "Daily Smoke Tests",
  "cron_expression": "0 9 * * 1-5",
  "scenario_tags": ["smoke"],
  "scenario_ids": [],
  "environment_id": "uuid-of-env",
  "browsers": ["chrome", "firefox"],
  "enabled": true
}
```

**Common cron expressions:**

| Expression | Description |
|------------|-------------|
| `0 * * * *` | Every hour |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 * * *` | Every day at midnight |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 * * 0` | Every Sunday at midnight |

#### Get Schedule

```
GET /schedules/{schedule_id}
```

#### Update Schedule

```
PUT /schedules/{schedule_id}
```

#### Delete Schedule

```
DELETE /schedules/{schedule_id}
```

#### Toggle Schedule

```
POST /schedules/{schedule_id}/toggle
```

Enables or disables a schedule.

#### Run Schedule Now

```
POST /schedules/{schedule_id}/run-now
```

Manually triggers the scheduled run immediately.

#### Describe Cron Expression

```
GET /schedules/cron/describe?expression=0 9 * * 1-5
```

**Response:**

```json
{
  "expression": "0 9 * * 1-5",
  "description": "Weekdays at 9:00 AM",
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

### Custom Steps

#### List Custom Steps

```
GET /steps
GET /steps/custom
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `repo_id` | UUID | Filter by repository |

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "repo_id": "uuid-of-repo",
    "name": "login_with_credentials",
    "pattern": "I login with username \"{username}\" and password \"{password}\"",
    "code": "@when(parsers.parse('I login with username \"{username}\"...'))\ndef login(...)",
    "committed": true
  }
]
```

#### Create Custom Step

```
POST /steps
POST /steps/custom
```

**Request Body:**

```json
{
  "repo_id": "uuid-of-repo",
  "name": "login_step",
  "pattern": "I login with username \"{username}\" and password \"{password}\"",
  "code": "@when(parsers.parse('I login with username \"{username}\" and password \"{password}\"'))\ndef login_step(test_context, username: str, password: str):\n    test_context.page.fill('#username', username)\n    test_context.page.fill('#password', password)\n    test_context.page.click('button[type=\"submit\"]')"
}
```

#### Update Custom Step

```
PUT /steps/{step_id}
PUT /steps/custom/{step_id}
```

#### Save Step to Repository

```
POST /steps/custom/{step_id}/save-to-repo
```

Commits the custom step to its associated git repository.

#### Delete Custom Step

```
DELETE /steps/{step_id}
DELETE /steps/custom/{step_id}
```

---

### Browsers

#### List Available Browsers

```
GET /browsers
```

**Response:**

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
  ]
}
```

---

### Users

Admin-only endpoints for user management.

#### List Users

```
GET /users
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by name or email |

#### Get User

```
GET /users/{user_id}
```

#### Update User Role

```
PUT /users/{user_id}/role
```

**Request Body:**

```json
{
  "role": "admin"
}
```

Valid roles: `admin`, `user`

#### Toggle User Active Status

```
PUT /users/{user_id}/active
```

**Request Body:**

```json
{
  "is_active": false
}
```

---

### Interactive Test Sessions

For interactive/exploratory testing with a visible browser.

#### Start Test Session

```
POST /test-session/start
```

**Request Body:**

```json
{
  "scenario_id": "uuid-of-scenario",
  "environment_id": "uuid-of-env",
  "browser_type": "chromium"
}
```

**Response:**

```json
{
  "id": "session-uuid",
  "status": "active",
  "browser_type": "chromium",
  "environment_name": "staging",
  "environment_base_url": "https://staging.example.com",
  "scenario_name": "Login Test",
  "current_step_index": 0,
  "total_steps": 5,
  "started_at": "2026-03-21T10:00:00Z",
  "websocket_url": "/api/v1/test-session/session-uuid/ws"
}
```

#### Load Scenario into Session

```
POST /test-session/{session_id}/load-scenario
```

**Request Body:**

```json
{
  "scenario_id": "uuid-of-scenario"
}
```

Or with direct content:

```json
{
  "content": "Feature: Test\n  Scenario: ..."
}
```

#### Execute Step

```
POST /test-session/{session_id}/step
```

**Request Body:**

```json
{
  "step_index": 0
}
```

#### Skip Step

```
POST /test-session/{session_id}/skip
```

#### Take Screenshot

```
POST /test-session/{session_id}/screenshot
```

#### Navigate to URL

```
POST /test-session/{session_id}/navigate
```

**Request Body:**

```json
{
  "url": "/dashboard"
}
```

#### Run Custom Action

```
POST /test-session/{session_id}/action
```

**Request Body:**

```json
{
  "action": "click",
  "selector": "#submit-button",
  "value": ""
}
```

Actions: `click`, `fill`, `select`, etc.

#### Get Session Status

```
GET /test-session/{session_id}/status
```

#### Pause Session

```
POST /test-session/{session_id}/pause
```

#### Resume Session

```
POST /test-session/{session_id}/resume
```

#### End Session

```
DELETE /test-session/{session_id}
```

#### List Sessions

```
GET /test-sessions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `active_only` | bool | Only return active sessions (default: true) |

#### WebSocket Connection

```
WS /test-session/{session_id}/ws
```

Receives real-time updates during test execution.

---

### Seed Data

For demo and testing purposes.

#### Create Seed Data

```
POST /seed
```

Populates example data (environment, repository, custom steps, schedules).

#### Delete Seed Data

```
DELETE /seed
```

Removes all seed data.

#### Get Seed Status

```
GET /seed/status
```

Checks if seed data exists.

---

## Code Examples

### curl

**Trigger a test run:**

```bash
curl -X POST "https://sliples.example.com/api/v1/runs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_tags": ["smoke"],
    "environment": "staging",
    "browsers": ["chrome"]
  }'
```

**Check run status:**

```bash
curl "https://sliples.example.com/api/v1/runs/run-uuid/status" \
  -H "X-API-Key: your-api-key"
```

**Download HTML report:**

```bash
curl "https://sliples.example.com/api/v1/runs/run-uuid/report" \
  -H "X-API-Key: your-api-key" \
  -o report.html
```

### Python

```python
import requests
import time

API_URL = "https://sliples.example.com/api/v1"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Trigger a test run
response = requests.post(
    f"{API_URL}/runs",
    headers=headers,
    json={
        "scenario_tags": ["smoke"],
        "environment": "staging",
        "browsers": ["chrome"],
        "parallel": True
    }
)
run = response.json()
run_id = run["id"]
print(f"Started run: {run_id}")

# Poll for completion
while True:
    status_response = requests.get(
        f"{API_URL}/runs/{run_id}/status",
        headers=headers
    )
    status = status_response.json()
    print(f"Status: {status['status']}")

    if status["status"] in ["passed", "failed", "cancelled", "error"]:
        break

    time.sleep(5)

# Get detailed results
results = requests.get(
    f"{API_URL}/runs/{run_id}",
    headers=headers
).json()

print(f"Final status: {results['status']}")
for result in results.get("results", []):
    print(f"  {result['step_name']}: {result['status']}")

# Download report
report = requests.get(
    f"{API_URL}/runs/{run_id}/report",
    headers=headers
)
with open("report.html", "w") as f:
    f.write(report.text)
```

### JavaScript/TypeScript

```typescript
const API_URL = "https://sliples.example.com/api/v1";
const API_KEY = "your-api-key";

async function runTests() {
  // Trigger test run
  const runResponse = await fetch(`${API_URL}/runs`, {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scenario_tags: ["smoke"],
      environment: "staging",
      browsers: ["chrome"],
      parallel: true,
    }),
  });

  const run = await runResponse.json();
  console.log(`Started run: ${run.id}`);

  // Poll for completion
  let status = "queued";
  while (!["passed", "failed", "cancelled", "error"].includes(status)) {
    await new Promise((resolve) => setTimeout(resolve, 5000));

    const statusResponse = await fetch(`${API_URL}/runs/${run.id}/status`, {
      headers: { "X-API-Key": API_KEY },
    });
    const statusData = await statusResponse.json();
    status = statusData.status;
    console.log(`Status: ${status}`);
  }

  // Get results
  const resultsResponse = await fetch(`${API_URL}/runs/${run.id}`, {
    headers: { "X-API-Key": API_KEY },
  });
  const results = await resultsResponse.json();

  console.log(`Final status: ${results.status}`);
  results.results?.forEach((result: any) => {
    console.log(`  ${result.step_name}: ${result.status}`);
  });

  return results;
}

runTests().catch(console.error);
```

### Jenkins Pipeline (Groovy)

```groovy
pipeline {
    environment {
        SLIPLES_API_KEY = credentials('sliples-api-key')
        SLIPLES_API_URL = 'https://sliples.example.com/api/v1'
    }
    stages {
        stage('UI Tests') {
            steps {
                script {
                    // Trigger test run
                    def response = httpRequest(
                        url: "${SLIPLES_API_URL}/runs",
                        httpMode: 'POST',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        contentType: 'APPLICATION_JSON',
                        requestBody: '''{
                            "scenario_tags": ["smoke"],
                            "environment": "staging",
                            "browsers": ["chrome"]
                        }'''
                    )
                    def runId = readJSON(text: response.content).id
                    echo "Started run: ${runId}"

                    // Poll for completion
                    timeout(time: 30, unit: 'MINUTES') {
                        waitUntil {
                            def status = httpRequest(
                                url: "${SLIPLES_API_URL}/runs/${runId}/status",
                                customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]]
                            )
                            def result = readJSON(text: status.content)
                            echo "Status: ${result.status}"
                            return result.status in ['passed', 'failed', 'cancelled', 'error']
                        }
                    }

                    // Check final status
                    def finalStatus = httpRequest(
                        url: "${SLIPLES_API_URL}/runs/${runId}",
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]]
                    )
                    def result = readJSON(text: finalStatus.content)

                    if (result.status != 'passed') {
                        error "Tests failed with status: ${result.status}"
                    }
                }
            }
        }
    }
}
```

---

## OpenAPI Documentation

The complete OpenAPI specification is available at:

```
GET /docs      # Swagger UI
GET /redoc     # ReDoc
GET /openapi.json  # OpenAPI JSON
```
