# Sliples User Guide

A comprehensive guide to using the Sliples Web UI Automation Testing Platform.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Managing Environments](#2-managing-environments)
3. [Managing Repositories](#3-managing-repositories)
4. [Writing Test Scenarios](#4-writing-test-scenarios)
5. [Running Tests](#5-running-tests)
6. [Interactive Testing Mode](#6-interactive-testing-mode)
7. [Scheduling Tests](#7-scheduling-tests)
8. [Settings and Administration](#8-settings-and-administration)
9. [CI/CD Integration](#9-cicd-integration)

---

## 1. Getting Started

### 1.1 Logging In (Google SSO)

Sliples uses Google Single Sign-On (SSO) for authentication. To log in:

1. Navigate to the Sliples application URL
2. Click the **Sign in with Google** button
3. Select your Google Workspace account
4. After successful authentication, you will be redirected to the Dashboard

If you receive an "unauthorized" error, contact your administrator to ensure your account has been granted access to Sliples.

### 1.2 Dashboard Overview

The Dashboard is your central hub for monitoring test activity. It displays:

**System Health Status**
- Overall system status (healthy/unhealthy)
- Database connection status
- Redis connection status

**Key Metrics**
- **Total Scenarios**: Number of test scenarios available
- **Pass Rate**: Percentage of tests passing in recent runs
- **Last 24h Runs**: Test runs executed in the last 24 hours
- **Failed Tests**: Number of currently failing tests

**Pass/Fail Trend Chart**
A visual representation of test results over the last 7 days, showing passed (green) and failed (red) tests stacked by day.

**Recent Test Runs**
A table showing the most recent test executions with their status, browser, creation time, and duration.

**Quick Actions**
- **Sync Repos**: Pull the latest test scenarios from all connected Git repositories
- **Run All Tests**: Start a new test run with all available scenarios

### 1.3 Navigation

The main navigation menu provides access to all Sliples features:

| Menu Item | Description |
|-----------|-------------|
| Dashboard | Overview of test activity and system health |
| Scenarios | Browse and search test scenarios |
| Test Runs | View, create, and manage test executions |
| Repositories | Manage Git repositories containing test scenarios |
| Environments | Configure test environments (dev, staging, prod) |
| Schedules | Set up automated test runs |
| Custom Steps | Create custom Gherkin step definitions |
| Test Mode | Interactive step-by-step test execution |
| Settings | Profile, API keys, and system configuration |

---

## 2. Managing Environments

Environments define where your tests run. Each environment has its own base URL, variables, and configuration.

### 2.1 Creating Environments (dev, staging, prod)

1. Navigate to **Environments** from the main menu
2. Click **Add Environment**
3. Fill in the required fields:
   - **Name**: A descriptive name (e.g., "Production", "Staging", "Development")
   - **Base URL**: The root URL for the application under test (e.g., `https://staging.example.com`)
   - **Retention Days**: How long to keep test results (default: 365 days)
4. Click **Save**

**Example Environments:**

| Name | Base URL | Purpose |
|------|----------|---------|
| Development | `http://localhost:3000` | Local testing during development |
| Staging | `https://staging.myapp.com` | Pre-production validation |
| Production | `https://www.myapp.com` | Production smoke tests |

### 2.2 Setting Base URLs

The base URL is the starting point for all navigation in your tests. When a test navigates to `/login`, it will go to `{base_url}/login`.

**Important considerations:**
- Include the protocol (`http://` or `https://`)
- Do not include a trailing slash
- For local development, use the appropriate port

### 2.3 Environment Variables

Environment variables allow you to store configuration that varies between environments. Common use cases include:

- Test credentials (usernames, passwords)
- API endpoints
- Feature flags
- Timeout values

**Adding Variables:**

1. Click **Edit** on an existing environment (or create a new one)
2. In the Variables section, add key-value pairs:
   ```
   TEST_USERNAME = testuser@example.com
   TEST_PASSWORD = secretpassword123
   API_TIMEOUT = 30
   ENABLE_FEATURE_X = true
   ```
3. Click **Save**

**Security Note:** Variables containing sensitive keywords (password, secret, token, api_key, credential, auth) are automatically masked in the UI display with asterisks.

### 2.4 Retention Settings

Each environment can have its own data retention policy:

- **Retention Days**: Number of days to keep test results, screenshots, and reports
- After the retention period, data is automatically deleted by the daily cleanup job
- Default retention is 365 days (12 months)
- Deleted data includes:
  - Test run results
  - Screenshots and artifacts from deleted runs
  - Log files

---

## 3. Managing Repositories

Sliples pulls test scenarios from Git repositories. You can connect multiple repositories to organize tests by project or team.

### 3.1 Connecting Git Repositories

1. Navigate to **Repositories** from the main menu
2. Click **Add Repository**
3. Enter the repository details:
   - **Name**: A friendly name for the repository (e.g., "E-commerce Tests")
   - **Git URL**: The SSH or HTTPS URL to clone the repository
     - SSH: `git@github.com:org/repo.git`
     - HTTPS: `https://github.com/org/repo.git`
   - **Branch**: The branch to sync (default: `main`)
4. Click **Add Repository**

**Note:** For SSH URLs, ensure the Sliples server has the appropriate SSH keys configured to access the repository.

### 3.2 Repository Sync

After adding a repository, sync it to import the test scenarios:

1. Click the **Sync** button next to the repository
2. Sliples will clone/pull the repository and scan for `.feature` files
3. All discovered scenarios will appear in the Scenarios page
4. The sync status and last sync time are displayed on the repository card

**Sync All Repos:** Click the **Sync All Repos** button on the Dashboard or Scenarios page to update all repositories at once.

**Sync Information Displayed:**
- Last synced timestamp (e.g., "5 minutes ago", "2 hours ago")
- Branch name
- Sync path (location where files are stored)
- Scenario count

### 3.3 Understanding .feature Files

Sliples uses Gherkin `.feature` files for test scenarios. These files should be placed anywhere in your repository - Sliples will scan recursively.

**Repository Structure Example:**
```
my-tests/
  features/
    login.feature
    checkout.feature
    user-management/
      create-user.feature
      delete-user.feature
  custom_steps/
    my_custom_steps.py
```

After syncing, the Scenarios page will show scenarios grouped by feature file:
- `features/login.feature` (2 scenarios)
- `features/checkout.feature` (5 scenarios)
- `features/user-management/create-user.feature` (3 scenarios)
- `features/user-management/delete-user.feature` (2 scenarios)

**Feature File Requirements:**
- File extension must be `.feature`
- Must contain valid Gherkin syntax
- Can include tags for organization and filtering

---

## 4. Writing Test Scenarios

### 4.1 Gherkin Syntax Basics

Gherkin is a plain-English language for describing test scenarios. Each feature file contains one or more scenarios.

**Basic Structure:**
```gherkin
Feature: User Login
  As a registered user
  I want to log into my account
  So that I can access my dashboard

  Scenario: Successful login with valid credentials
    Given I navigate to "/login"
    When I enter "testuser@example.com" into the "email" field
    And I enter "password123" into the "password" field
    And I click the "Sign In" button
    Then I should see "Welcome back"
    And I should be on the "/dashboard" page
```

**Key Elements:**
- **Feature**: Describes what you are testing (one per file)
- **Scenario**: A specific test case
- **Given**: Sets up the initial state (preconditions)
- **When**: Describes the action being taken
- **Then**: Describes the expected outcome
- **And/But**: Continues the previous step type

**Scenario Outline (Data-Driven Tests):**
```gherkin
Scenario Outline: Login with different user roles
  Given I navigate to "/login"
  When I enter "<email>" into the "email" field
  And I enter "<password>" into the "password" field
  And I click the "Sign In" button
  Then I should see "<welcome_message>"

  Examples:
    | email              | password    | welcome_message  |
    | admin@example.com  | admin123    | Welcome, Admin   |
    | user@example.com   | user123     | Welcome, User    |
```

### 4.2 Available Step Definitions (Given/When/Then)

Sliples provides built-in step definitions for common web testing actions:

#### Navigation Steps

```gherkin
# Navigate to named pages or URLs
Given I am on the "{page_name}" page
Given I navigate to "{url}"
When I navigate to "{url}"

# Click elements
When I click the "{element}" button
When I click on "{text}"
When I click the link "{text}"

# Browser navigation
When I go back
When I go forward
When I refresh the page
```

#### Form Interaction Steps

```gherkin
# Text input
When I enter "{value}" into the "{field}" field
When I type "{value}" into the "{field}" field
When I clear the "{field}" field

# Dropdowns and select boxes
When I select "{option}" from "{dropdown}"

# Checkboxes and radio buttons
When I check the "{checkbox}" checkbox
When I uncheck the "{checkbox}" checkbox
```

#### Assertion Steps

```gherkin
# Text visibility
Then I should see "{text}"
Then I should not see "{text}"

# Element visibility
Then the "{element}" should be visible
Then the "{element}" should not be visible

# Element state
Then the "{element}" should be enabled
Then the "{element}" should be disabled

# Page state
Then I should be on the "{page_name}" page
Then the page title should be "{title}"
Then the page title should contain "{text}"
Then the URL should contain "{text}"
```

#### Wait Steps

```gherkin
When I wait for {seconds} seconds
When I wait for the "{element}" to be visible
When I wait for the "{element}" to disappear
When I wait for the page to load
```

#### Screenshot Steps

```gherkin
Then I take a screenshot named "{name}"
```

### 4.3 Using Tags for Organization

Tags help organize and filter scenarios. Add tags with the `@` symbol before features or scenarios.

**Common Tag Patterns:**
```gherkin
@smoke @critical
Feature: Critical User Flows

  @login @positive
  Scenario: Successful login
    Given I navigate to "/login"
    ...

  @login @negative
  Scenario: Login with invalid password
    Given I navigate to "/login"
    ...

@regression @checkout
Feature: Checkout Process
  ...
```

**Recommended Tag Conventions:**

| Tag | Purpose |
|-----|---------|
| `@smoke` | Quick sanity tests (5-10 minutes) |
| `@regression` | Full regression suite |
| `@critical` | Business-critical functionality |
| `@wip` | Work in progress (exclude from CI) |
| `@slow` | Long-running tests |
| `@flaky` | Known unstable tests |
| `@api` | API-related tests |
| `@ui` | UI-only tests |
| `@login`, `@checkout`, `@search` | Feature areas |

### 4.4 Creating Custom Steps

When built-in steps are not sufficient, create custom step definitions:

1. Navigate to **Custom Steps** from the main menu
2. Click **Create Step**
3. Fill in the step details:
   - **Name**: A descriptive name (e.g., "Wait for loading spinner to disappear")
   - **Pattern**: The Gherkin pattern with placeholders (e.g., `I wait for the loading spinner to disappear`)
   - **Description**: Optional explanation of what the step does
   - **Code**: Python implementation using Playwright

**Example Custom Step:**
```python
# Pattern: I wait for the loading spinner to disappear

async def step_impl(context):
    page = context.page
    # Wait for spinner to be hidden
    await page.wait_for_selector('.loading-spinner', state='hidden', timeout=30000)
```

**Using Placeholders in Patterns:**
```gherkin
# Pattern: I select the {nth} item from the results

async def step_impl(context, nth):
    page = context.page
    items = await page.query_selector_all('.result-item')
    index = int(nth.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')) - 1
    await items[index].click()
```

**Advanced Custom Step with Environment Variables:**
```python
# Pattern: I login with stored credentials

async def step_impl(context):
    page = context.page
    username = context.variables.get('TEST_USERNAME', 'default@example.com')
    password = context.variables.get('TEST_PASSWORD', 'default123')

    await page.fill('[data-testid="email"]', username)
    await page.fill('[data-testid="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')
```

---

## 5. Running Tests

### 5.1 Starting a Test Run

1. Navigate to **Test Runs** from the main menu
2. Click **New Test Run**
3. Configure the test run:
   - **Environment** (required): Select the target environment
   - **Tags**: Filter scenarios by tags (optional - leave empty to run all)
   - **Browsers**: Select one or more browsers (Chromium, Firefox, WebKit)
4. Click **Start Test Run**

You will be redirected to the Run Details page to monitor progress.

### 5.2 Selecting Scenarios by Tag

When creating a test run, you can filter which scenarios to include:

- **No tags selected**: All scenarios run
- **Single tag**: Only scenarios with that tag run
- **Multiple tags**: Scenarios with ANY of the selected tags run

**Example:** Selecting `@smoke` and `@login` will run all scenarios tagged with either `@smoke` OR `@login`.

**Tips for Tag Selection:**
- Use `@smoke` for quick validation after deployments
- Use `@regression` for comprehensive overnight testing
- Use feature-specific tags (`@checkout`, `@user-management`) for focused testing

### 5.3 Choosing Browsers

Sliples supports multiple browser engines through Playwright:

| Browser | Engine | Best For |
|---------|--------|----------|
| Chromium | Chromium | Chrome/Edge testing, most web apps |
| Firefox | Firefox | Firefox-specific testing, cross-browser validation |
| WebKit | WebKit | Safari/iOS testing, Apple device simulation |

**Multi-browser Runs:** Select multiple browsers to run the same scenarios on each browser in parallel. This is useful for cross-browser compatibility testing.

### 5.4 Viewing Results

The Run Details page shows comprehensive test execution information:

**Header Information:**
- Run ID (unique identifier)
- Overall status badge (passed/failed/running/queued)
- Trigger source (manual, scheduled, CI/CD)

**Summary Cards:**
- Browser and version used
- Total execution duration
- Passed step count (green)
- Failed step count (red)
- Target environment

**Progress Bar:** For running tests, shows completion percentage with real-time updates via WebSocket or polling.

**Test Steps List:** Each step displays:
- Step number and name
- Scenario name (if applicable)
- Pass/fail status with colored indicators
- Execution duration in milliseconds
- Screenshot button (click to view)
- Error message (expandable for failed steps)

**Actions:**
- **Pause/Resume Refresh**: Toggle auto-refresh during running tests
- **Re-run**: Start a new test run with the same configuration
- **View Report**: Open the HTML report in a new tab or download it

### 5.5 Re-running Failed Tests

To re-run a completed test:

1. Open the Run Details page for a completed (passed or failed) run
2. Click the **Re-run** button in the top-right corner
3. A new test run starts with the same configuration
4. You are redirected to the new run's details page

This is useful for:
- Verifying that a flaky test now passes
- Re-running after a bug fix
- Confirming intermittent issues

---

## 6. Interactive Testing Mode

Interactive Testing Mode allows you to run tests step-by-step with live browser feedback, perfect for debugging and test development.

### 6.1 Starting a Session

1. Navigate to **Test Mode** from the main menu
2. Configure the session:
   - **Environment** (required): Where to run the tests
   - **Scenario** (optional): Pre-load a specific scenario
   - **Browser**: Choose Chromium, Firefox, or WebKit
3. Click **Start Test Session**

A browser instance launches, and you see a split-screen view:
- **Left Panel**: Session controls and step executor
- **Right Panel**: Live browser preview with toolbar

### 6.2 Step-by-Step Execution

With a scenario loaded, the left panel shows all steps. You can:

- **Execute Next Step**: Run the current step and advance to the next
- **Skip Step**: Skip the current step without executing and move to the next
- **Run All**: Execute all remaining steps automatically (stops on failure)

**Step Status Indicators:**
- Pending (gray): Not yet executed
- Running (yellow/spinning): Currently executing
- Passed (green): Successfully completed
- Failed (red): Execution failed
- Skipped (gray with dash): Manually skipped

After each step:
- The browser preview updates with a fresh screenshot
- Step results show pass/fail status and duration
- Failed steps display error messages inline

### 6.3 Custom Actions

While in an active session, you can perform ad-hoc actions beyond the loaded scenario:

**Navigate to URL:**
1. Click the globe icon in the preview toolbar
2. Enter a full URL or relative path (e.g., `/dashboard` or `https://example.com`)
3. Click **Navigate**

**Run Custom Action:**
1. Click the pencil icon in the preview toolbar
2. Select an action type:
   - **Click**: Click an element
   - **Fill Input**: Enter text into an input field
   - **Select Option**: Choose from a dropdown
   - **Check/Uncheck Checkbox**: Toggle a checkbox
   - **Hover**: Hover over an element
   - **Press Key**: Simulate keyboard input (Enter, Tab, Escape, etc.)
   - **Type Text**: Type text into the focused element
   - **Wait**: Pause for a specified number of seconds
3. Enter the CSS selector (e.g., `#submit-btn`, `.login-form input[name="email"]`)
4. Enter a value if required
5. Click **Run Action**

**Take Screenshot:**
Click the camera icon to capture the current browser state. Screenshots are added to the gallery.

**Screenshot Gallery:**
Click the gallery icon to view all screenshots captured during the session. Click any thumbnail to view full-size.

### 6.4 Debugging Tips

**Element Inspection:**
- Use custom hover actions to trigger tooltips or state changes
- Take screenshots at various states to understand UI behavior
- Use wait actions to pause and observe transitions

**Switching Scenarios:**
Use the scenario dropdown to load a different scenario into the active session without restarting the browser. This preserves browser state (cookies, localStorage, etc.).

**Console Output:**
The bottom panel shows browser console logs in real-time:
- Normal logs (gray)
- Warnings (yellow)
- Errors (red)

Clear logs with the "Clear" button to focus on new output.

**Session Controls:**
- **Pause**: Temporarily pause the session (browser remains open)
- **Resume**: Continue a paused session
- **End Session**: Close the browser and return to session setup

---

## 7. Scheduling Tests

Automate your test runs with schedules using cron expressions.

### 7.1 Creating Schedules with Cron

1. Navigate to **Schedules** from the main menu
2. Click **Add Schedule**
3. Configure the schedule:
   - **Name**: Descriptive name (e.g., "Nightly Regression Suite")
   - **Cron Expression**: When to run (see examples below)
   - **Environment**: Target environment
   - **Scenario Tags**: Filter scenarios (optional - empty runs all)
   - **Browsers**: Target browsers
   - **Enabled**: Toggle to activate/deactivate
4. Click **Save**

**Cron Expression Format:** `minute hour day-of-month month day-of-week`

| Schedule | Cron Expression | Description |
|----------|-----------------|-------------|
| Every day at midnight | `0 0 * * *` | Runs at 00:00 daily |
| Every day at 6 AM | `0 6 * * *` | Runs at 06:00 daily |
| Every hour | `0 * * * *` | Runs at the start of every hour |
| Every 30 minutes | `*/30 * * * *` | Runs at :00 and :30 |
| Every Monday at 9 AM | `0 9 * * 1` | Runs at 09:00 on Mondays |
| Every weekday at 8 AM | `0 8 * * 1-5` | Runs at 08:00 Monday-Friday |
| Twice daily | `0 6,18 * * *` | Runs at 06:00 and 18:00 |
| First day of month | `0 0 1 * *` | Runs at midnight on the 1st |
| Every Sunday at midnight | `0 0 * * 0` | Weekly Sunday runs |

### 7.2 Managing Schedules

Each schedule card displays:
- Schedule name and enabled/disabled status
- Cron description in human-readable format (e.g., "Every day at 6:00 AM")
- Raw cron expression
- Target environment and browsers
- Scenario tags (if filtered)
- Next scheduled run time (with relative time like "in 2 hours")
- Last run time (with relative time like "5 hours ago")

**Available Actions:**
- **Toggle Switch**: Enable/disable the schedule without deleting
- **Play Button**: Trigger the schedule immediately (manual run)
- **Edit Button**: Modify schedule configuration
- **Delete Button**: Remove the schedule permanently

### 7.3 Viewing Schedule History

To see past runs triggered by a schedule:

1. Navigate to **Test Runs**
2. Look for runs with the trigger source showing the schedule name
3. Filter by date range to see historical executions

Scheduled runs behave identically to manual runs - you can view details, screenshots, and reports the same way.

---

## 8. Settings and Administration

### 8.1 API Key Management

API keys enable programmatic access to Sliples for CI/CD integration.

**Generating a New API Key:**
1. Navigate to **Settings** > **API Keys** tab
2. Click **Generate New Key**
3. Enter a name for the key (e.g., "Jenkins CI", "GitHub Actions", "Production Pipeline")
4. Click **Create**
5. **Important**: Copy the key immediately - it will only be displayed once

**API Key Display:**
- Active keys are listed with masked values (e.g., `slk_****...****`)
- Last used timestamp shows when the key was last authenticated
- Creation date for tracking key age

**Managing API Keys:**
- **View**: See all active API keys (values masked)
- **Revoke**: Delete keys that are no longer needed or compromised

**Security Best Practices:**
- Create separate keys for each CI/CD system or environment
- Rotate keys periodically (e.g., every 90 days)
- Revoke keys immediately if compromised
- Never commit API keys to source control
- Store keys in CI/CD secret management systems

### 8.2 User Roles (Admin vs User)

Sliples supports two user roles:

| Role | Capabilities |
|------|--------------|
| **Admin** | Full access including: manage API keys, view system configuration, manage all resources |
| **User** | Standard access: run tests, view results, manage scenarios, environments, and schedules |

**Role Assignment:**
- Roles are managed through SSO configuration
- The first user to log in typically becomes an admin
- Contact your administrator to request role changes

**Role Indicator:**
Your current role is displayed in Settings > Profile with a colored badge.

### 8.3 System Configuration

The **System** tab in Settings displays read-only system configuration:

**Email Configuration:**
- SMTP Host and Port
- From Address
- TLS Enabled status
- Configuration status (Configured/Not Configured)

**Storage Configuration (S3/MinIO):**
- Endpoint URL
- Bucket name
- Region
- Access key (masked)
- Configuration status

**Data Retention:**
- Default retention period (typically 365 days)
- Cleanup schedule (typically daily at midnight)
- Last cleanup timestamp
- Items deleted during cleanup:
  - Test run results older than retention period
  - Screenshots and artifacts from deleted runs
  - Log files older than retention period

**Note:** System configuration is managed via environment variables by system administrators. Changes require server-side configuration updates.

### 8.4 User Preferences

The **Preferences** tab allows personal customization:

**Appearance:**
- Theme selection (Dark/Light)
- Note: Light theme is planned for a future release; Dark theme is currently active

**Notifications:**
- **Email on failure**: Receive email when test runs fail
- **Email on success**: Receive email when test runs pass
- **Browser notifications**: Desktop notifications for test status updates

**Data and Privacy:**
- Preferences are stored locally in your browser
- Test data and API keys are stored securely on the server
- Data is automatically deleted according to retention policy

---

## 9. CI/CD Integration

### 9.1 Using API Keys

All API requests require authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" \
  https://sliples.example.com/api/v1/health
```

**Required Header:**
- Header Name: `X-API-Key`
- Header Value: Your generated API key

**Error Responses:**
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Key doesn't have permission for the requested action

### 9.2 Triggering Runs from CI

**Start a Test Run:**
```bash
curl -X POST \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_tags": ["smoke"],
    "environment": "staging",
    "browsers": ["chromium"]
  }' \
  https://sliples.example.com/api/v1/runs
```

**Request Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `environment` | string | Yes | Environment name to run against |
| `scenario_tags` | array | No | Filter scenarios by tags (empty = all) |
| `browsers` | array | No | Target browsers (default: ["chromium"]) |

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "environment_id": "...",
  "environment_name": "staging",
  "browser": "chromium",
  "created_at": "2026-03-21T10:30:00Z"
}
```

### 9.3 Checking Results

**Poll for Completion:**
```bash
curl -H "X-API-Key: your-api-key-here" \
  https://sliples.example.com/api/v1/runs/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "passed",
  "passed_count": 15,
  "failed_count": 0,
  "browser": "chromium",
  "browser_version": "122.0",
  "created_at": "2026-03-21T10:30:00Z",
  "finished_at": "2026-03-21T10:31:15Z",
  "results": [...]
}
```

**Status Values:**

| Status | Description | Final? |
|--------|-------------|--------|
| `queued` | Waiting for a worker to pick up | No |
| `running` | Tests currently executing | No |
| `passed` | All tests passed | Yes |
| `failed` | One or more tests failed | Yes |
| `cancelled` | Run was cancelled | Yes |

**Downloading the Report:**
```bash
curl -H "X-API-Key: your-api-key-here" \
  https://sliples.example.com/api/v1/runs/550e8400-e29b-41d4-a716-446655440000/report \
  -o test-report.html
```

### 9.4 Complete CI/CD Examples

#### Jenkins Pipeline

```groovy
pipeline {
    environment {
        SLIPLES_API_KEY = credentials('sliples-api-key')
        SLIPLES_URL = 'https://sliples.example.com'
    }

    stages {
        stage('Deploy to Staging') {
            steps {
                // Your deployment steps here
                sh 'deploy-to-staging.sh'
            }
        }

        stage('Run UI Tests') {
            steps {
                script {
                    // Trigger test run
                    def response = httpRequest(
                        url: "${SLIPLES_URL}/api/v1/runs",
                        httpMode: 'POST',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        contentType: 'APPLICATION_JSON',
                        requestBody: '''{
                            "scenario_tags": ["smoke"],
                            "environment": "staging",
                            "browsers": ["chromium"]
                        }'''
                    )
                    def runId = readJSON(text: response.content).id
                    echo "Started test run: ${runId}"

                    // Poll for completion (max 30 minutes)
                    timeout(time: 30, unit: 'MINUTES') {
                        waitUntil {
                            def status = httpRequest(
                                url: "${SLIPLES_URL}/api/v1/runs/${runId}",
                                customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]]
                            )
                            def result = readJSON(text: status.content)
                            echo "Current status: ${result.status}"

                            if (result.status == 'failed') {
                                error "UI tests failed! View results: ${SLIPLES_URL}/runs/${runId}"
                            }

                            return result.status == 'passed'
                        }
                    }

                    echo "All UI tests passed!"
                }
            }
        }
    }

    post {
        always {
            echo "Test results available at: ${SLIPLES_URL}/runs"
        }
        failure {
            echo "Pipeline failed. Check Sliples for detailed test results."
        }
    }
}
```

#### GitHub Actions

```yaml
name: UI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ui-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Sliples Test Run
        id: trigger
        run: |
          RESPONSE=$(curl -s -X POST \
            -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "scenario_tags": ["smoke"],
              "environment": "staging",
              "browsers": ["chromium"]
            }' \
            ${{ secrets.SLIPLES_URL }}/api/v1/runs)

          echo "Response: $RESPONSE"
          RUN_ID=$(echo $RESPONSE | jq -r '.id')
          echo "run_id=$RUN_ID" >> $GITHUB_OUTPUT
          echo "Started test run: $RUN_ID"

      - name: Wait for Test Completion
        run: |
          RUN_ID=${{ steps.trigger.outputs.run_id }}
          MAX_ATTEMPTS=60
          ATTEMPT=0

          while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
            RESPONSE=$(curl -s \
              -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
              ${{ secrets.SLIPLES_URL }}/api/v1/runs/$RUN_ID)

            STATUS=$(echo $RESPONSE | jq -r '.status')
            echo "Attempt $ATTEMPT: Status = $STATUS"

            if [ "$STATUS" = "passed" ]; then
              echo "All tests passed!"
              exit 0
            elif [ "$STATUS" = "failed" ]; then
              FAILED_COUNT=$(echo $RESPONSE | jq -r '.failed_count')
              echo "Tests failed! $FAILED_COUNT failures."
              echo "View results: ${{ secrets.SLIPLES_URL }}/runs/$RUN_ID"
              exit 1
            elif [ "$STATUS" = "cancelled" ]; then
              echo "Test run was cancelled"
              exit 1
            fi

            ATTEMPT=$((ATTEMPT + 1))
            sleep 30
          done

          echo "Timeout waiting for test completion"
          exit 1

      - name: Download Test Report
        if: always()
        continue-on-error: true
        run: |
          curl -s \
            -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
            ${{ secrets.SLIPLES_URL }}/api/v1/runs/${{ steps.trigger.outputs.run_id }}/report \
            -o test-report.html

      - name: Upload Test Report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: sliples-test-report
          path: test-report.html
          retention-days: 30
```

#### GitLab CI

```yaml
stages:
  - deploy
  - test

variables:
  SLIPLES_URL: "https://sliples.example.com"

deploy_staging:
  stage: deploy
  script:
    - ./deploy-to-staging.sh

ui_tests:
  stage: test
  needs: [deploy_staging]
  script:
    - |
      # Trigger test run
      RESPONSE=$(curl -s -X POST \
        -H "X-API-Key: ${SLIPLES_API_KEY}" \
        -H "Content-Type: application/json" \
        -d '{"scenario_tags": ["smoke"], "environment": "staging", "browsers": ["chromium"]}' \
        ${SLIPLES_URL}/api/v1/runs)

      RUN_ID=$(echo $RESPONSE | jq -r '.id')
      echo "Started test run: $RUN_ID"

      # Poll for completion
      for i in $(seq 1 60); do
        STATUS=$(curl -s \
          -H "X-API-Key: ${SLIPLES_API_KEY}" \
          ${SLIPLES_URL}/api/v1/runs/${RUN_ID} | jq -r '.status')

        echo "Status: $STATUS"

        if [ "$STATUS" = "passed" ]; then
          echo "Tests passed!"
          exit 0
        elif [ "$STATUS" = "failed" ]; then
          echo "Tests failed! See: ${SLIPLES_URL}/runs/${RUN_ID}"
          exit 1
        fi

        sleep 30
      done

      echo "Timeout"
      exit 1
  artifacts:
    when: always
    reports:
      junit: test-results.xml
```

---

## Appendix: Troubleshooting

### Common Issues

**Tests stuck in "queued" status:**
- Check that Celery workers are running
- Verify Redis connection is healthy
- Check worker logs for errors

**Browser connection errors:**
- Verify browser containers are running
- Check network connectivity between workers and browsers
- Restart browser containers if needed

**Screenshots not loading:**
- Verify S3/MinIO is accessible
- Check storage credentials in environment configuration
- Ensure bucket exists and has correct permissions

**Repository sync fails:**
- Verify Git URL is correct and accessible
- Check SSH keys or HTTPS credentials
- Verify branch name exists

**API authentication errors:**
- Confirm API key is correct and active
- Check header format: `X-API-Key: your-key`
- Verify key hasn't been revoked

---

## Appendix: API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | System health check |
| `/api/v1/runs` | GET | List test runs |
| `/api/v1/runs` | POST | Create a new test run |
| `/api/v1/runs/{id}` | GET | Get run details |
| `/api/v1/runs/{id}/report` | GET | Download HTML report |
| `/api/v1/scenarios` | GET | List scenarios |
| `/api/v1/environments` | GET | List environments |
| `/api/v1/repos` | GET | List repositories |
| `/api/v1/repos/{id}/sync` | POST | Sync a repository |

Full API documentation is available at `/docs` (Swagger UI) on your Sliples instance.

---

*Document Version: 1.0*
*Last Updated: 2026-03-21*
