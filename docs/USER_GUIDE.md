# Sliples User Guide

A comprehensive guide to using the Sliples Web UI Automation Testing Platform.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Test Scenarios](#creating-test-scenarios)
3. [Running Tests via UI](#running-tests-via-ui)
4. [Running Tests via API (CI/CD)](#running-tests-via-api-cicd)
5. [Understanding Test Results](#understanding-test-results)
6. [Custom Step Definitions](#custom-step-definitions)
7. [Environment Configuration](#environment-configuration)
8. [Scheduled Test Runs](#scheduled-test-runs)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Local Development Setup

1. **Prerequisites:**
   - Docker and Docker Compose
   - Git

2. **Clone and start the platform:**

   ```bash
   git clone https://github.com/your-org/sliples.git
   cd sliples
   docker compose up -d
   ```

3. **Wait for services to be healthy:**

   ```bash
   docker compose ps
   ```

   All services should show as "healthy" or "running".

4. **Access the platform:**
   - **Frontend:** http://localhost:5173
   - **API:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs
   - **MinIO Console:** http://localhost:9001 (credentials: sliples/sliples_dev)

5. **Verify installation:**

   ```bash
   curl http://localhost:8000/api/v1/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "redis": "connected"
   }
   ```

### First-Time Setup

1. **Login:** Navigate to the frontend and login using Google Workspace SSO. The first user automatically becomes an admin.

2. **Create an API Key:** Go to Settings > API Keys and create your first key for CI/CD integration.

3. **Add a Repository:** Go to Repos and add your test scenario repository.

4. **Create an Environment:** Go to Environments and configure your test environment (base URL, credentials, etc.).

5. **Sync Scenarios:** Click "Sync All" to import your .feature files.

---

## Creating Test Scenarios

### Gherkin Syntax Basics

Sliples uses Gherkin syntax for test scenarios. Create `.feature` files in your repository:

```gherkin
Feature: User Authentication
  As a user
  I want to be able to login
  So that I can access my dashboard

  @smoke @login
  Scenario: Successful login with valid credentials
    Given I am on the "login" page
    When I enter "testuser@example.com" into the "email" field
    And I enter "password123" into the "password" field
    And I click the "Sign In" button
    Then I should see "Welcome back"
    And I should be on the "dashboard" page

  @regression @login
  Scenario: Failed login with invalid password
    Given I am on the "login" page
    When I enter "testuser@example.com" into the "email" field
    And I enter "wrongpassword" into the "password" field
    And I click the "Sign In" button
    Then I should see "Invalid credentials"
```

### Built-in Step Definitions

Sliples provides a library of built-in step definitions:

#### Navigation Steps

```gherkin
# Navigate to named pages
Given I am on the "home" page
Given I am on the "login" page
Given I am on the "dashboard" page

# Navigate to URLs
Given I navigate to "/custom/path"
When I navigate to "https://external-site.com"

# Click elements
When I click the "Submit" button
When I click on "Sign In"
When I click the link "Learn More"

# Browser navigation
When I go back
When I go forward
When I refresh the page

# URL assertions
Then I should be on the "dashboard" page
Then the URL should contain "success"
```

#### Form Interaction Steps

```gherkin
# Text input
When I enter "john@example.com" into the "email" field
When I type "password" into the "password" field
When I clear the "search" field

# Dropdowns
When I select "Option A" from "dropdown"

# Checkboxes
When I check the "terms" checkbox
When I uncheck the "newsletter" checkbox

# Form submission
When I submit the form

# Field assertions
Then the "email" field should have value "john@example.com"
Then the "search" field should be empty
```

#### Assertion Steps

```gherkin
# Text visibility
Then I should see "Welcome"
Then I should not see "Error"

# Element visibility
Then the "submit-button" should be visible
Then the "error-message" should not be visible

# Element state
Then the "submit-button" should be enabled
Then the "delete-button" should be disabled

# Page title
Then the page title should be "Dashboard - MyApp"
Then the page title should contain "Dashboard"

# Element content
Then the "header" should contain "Welcome"

# Element count
Then there should be 5 "product-card" elements
```

#### Wait Steps

```gherkin
When I wait for 2 seconds
When I wait for the "loading-spinner" to be visible
When I wait for the "loading-spinner" to disappear
When I wait for the page to load
```

#### Utility Steps

```gherkin
# Screenshots
Then I take a screenshot named "login-page"

# Variables
Given I have a variable "userId" with value "12345"
When I set variable "count" to "10"
Then the variable "userId" should equal "12345"

# Viewport
Given the browser viewport is 1920x1080

# Keyboard
When I press the "Enter" key

# Scrolling
When I scroll to the bottom
When I scroll to the top
```

### Using Tags

Tags help organize and filter scenarios:

```gherkin
@smoke
Feature: Critical Path Tests

  @login @priority-high
  Scenario: User login
    ...

  @checkout @priority-high
  Scenario: Complete purchase
    ...
```

Common tag conventions:
- `@smoke` - Quick sanity tests
- `@regression` - Full regression suite
- `@wip` - Work in progress
- `@skip` - Skip this test
- `@priority-high`, `@priority-low`
- `@login`, `@checkout`, `@search` - Feature areas

### Using the Scenario Editor

1. Navigate to **Scenarios** in the sidebar
2. Click on a scenario to view it
3. Click **Edit** to open the Monaco editor
4. Make changes with syntax highlighting
5. Click **Save** to update the scenario
6. Optionally commit changes back to the repository

---

## Running Tests via UI

### Quick Run from Dashboard

1. Go to the **Dashboard**
2. Click **Run All Tests** to execute all scenarios
3. Or click **Sync Repos** first to get the latest scenarios

### Running Specific Scenarios

1. Go to **Scenarios**
2. Filter by tag, repository, or search term
3. Select scenarios to run
4. Click **Run Selected**
5. Choose environment and browser
6. Click **Start Run**

### Running from Test Runs Page

1. Go to **Test Runs**
2. Click **New Run**
3. Configure:
   - **Environment:** Select target environment
   - **Tags:** Filter scenarios by tags (leave empty for all)
   - **Browsers:** Select one or more browsers
   - **Parallel:** Enable for faster execution
4. Click **Start**

### Monitoring Run Progress

1. The run appears in the Test Runs list
2. Status updates: Queued > Running > Passed/Failed
3. Click on a run to see real-time progress
4. View step-by-step execution with screenshots

---

## Running Tests via API (CI/CD)

### Getting an API Key

1. Go to **Settings** > **API Keys**
2. Click **Create New Key**
3. Enter a name (e.g., "Jenkins Pipeline")
4. Optionally restrict to specific environments
5. **Copy and save the key** - it won't be shown again

### Basic API Usage

```bash
# Trigger a test run
curl -X POST "https://sliples.example.com/api/v1/runs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_tags": ["smoke"],
    "environment": "staging",
    "browsers": ["chrome"]
  }'
```

### Complete CI/CD Example (GitHub Actions)

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
      - name: Trigger Sliples Tests
        id: trigger
        run: |
          RESPONSE=$(curl -s -X POST "${{ secrets.SLIPLES_URL }}/api/v1/runs" \
            -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{
              "scenario_tags": ["smoke"],
              "environment": "staging",
              "browsers": ["chrome"]
            }')
          RUN_ID=$(echo $RESPONSE | jq -r '.id')
          echo "run_id=$RUN_ID" >> $GITHUB_OUTPUT

      - name: Wait for Results
        run: |
          RUN_ID="${{ steps.trigger.outputs.run_id }}"
          while true; do
            STATUS=$(curl -s "${{ secrets.SLIPLES_URL }}/api/v1/runs/$RUN_ID/status" \
              -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
              | jq -r '.status')
            echo "Status: $STATUS"
            if [[ "$STATUS" == "passed" || "$STATUS" == "failed" ]]; then
              break
            fi
            sleep 10
          done
          if [[ "$STATUS" != "passed" ]]; then
            echo "Tests failed!"
            exit 1
          fi

      - name: Download Report
        if: always()
        run: |
          curl -s "${{ secrets.SLIPLES_URL }}/api/v1/runs/${{ steps.trigger.outputs.run_id }}/report" \
            -H "X-API-Key: ${{ secrets.SLIPLES_API_KEY }}" \
            -o test-report.html

      - name: Upload Report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-report
          path: test-report.html
```

### Jenkins Pipeline

```groovy
pipeline {
    environment {
        SLIPLES_API_KEY = credentials('sliples-api-key')
        SLIPLES_URL = 'https://sliples.example.com/api/v1'
    }
    stages {
        stage('UI Tests') {
            steps {
                script {
                    def response = httpRequest(
                        url: "${SLIPLES_URL}/runs",
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

                    timeout(time: 30, unit: 'MINUTES') {
                        waitUntil {
                            def status = httpRequest(
                                url: "${SLIPLES_URL}/runs/${runId}/status",
                                customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]]
                            )
                            def result = readJSON(text: status.content)
                            return result.status in ['passed', 'failed']
                        }
                    }
                }
            }
        }
    }
}
```

---

## Understanding Test Results

### Run Status Values

| Status | Description |
|--------|-------------|
| `queued` | Run is waiting to be picked up by a worker |
| `running` | Tests are currently executing |
| `passed` | All tests passed |
| `failed` | One or more tests failed |
| `cancelled` | Run was manually cancelled |
| `error` | System error during execution |

### Run Details Page

The Run Details page shows:

1. **Summary:** Overall status, duration, triggered by
2. **Step Results:** Each step with:
   - Status (passed/failed/skipped)
   - Duration
   - Error message (if failed)
   - Screenshot
3. **Screenshots:** Click to view full-size
4. **HTML Report:** Download pytest-html style report

### Understanding Failures

When a test fails:

1. Check the **error message** for the failed step
2. View the **screenshot** at the point of failure
3. Look at the **previous step screenshot** to understand the state
4. Check if it's:
   - **Flaky test:** Inconsistent pass/fail (timing issues)
   - **Real bug:** Consistent failure
   - **Test issue:** Incorrect selector or assertion

### Retrying Failed Runs

1. Go to the failed run's details
2. Click **Retry**
3. A new run starts with the same configuration

---

## Custom Step Definitions

### When to Create Custom Steps

Create custom steps when:
- Built-in steps don't cover your use case
- You have repeated complex actions
- You need domain-specific language

### Creating Custom Steps via UI

1. Go to **Custom Steps**
2. Click **New Step**
3. Fill in:
   - **Name:** Descriptive name (e.g., `login_with_credentials`)
   - **Pattern:** Gherkin pattern (e.g., `I login as "{role}"`)
   - **Code:** Python implementation
4. Click **Save**

### Custom Step Code Structure

```python
@when(parsers.parse('I login as "{role}"'))
def login_as_role(test_context, role: str):
    """Login as a specific role."""
    credentials = {
        "admin": ("admin@example.com", "admin123"),
        "user": ("user@example.com", "user123"),
    }
    email, password = credentials.get(role, ("test@example.com", "test123"))

    test_context.page.fill('[data-testid="email"]', email)
    test_context.page.fill('[data-testid="password"]', password)
    test_context.page.click('button[type="submit"]')
    test_context.page.wait_for_load_state("networkidle")
```

### Available in Custom Steps

The `test_context` object provides:
- `test_context.page` - Playwright page object
- `test_context.base_url` - Environment base URL
- `test_context.variables` - Test variables dict
- `test_context.screenshots` - List of screenshot paths

### Committing Steps to Repository

1. Go to **Custom Steps**
2. Find your step
3. Click **Save to Repo**
4. The step is committed to the associated repository

---

## Environment Configuration

### Creating an Environment

1. Go to **Environments**
2. Click **New Environment**
3. Configure:
   - **Name:** Unique identifier (e.g., `staging`, `production`)
   - **Base URL:** Target application URL
   - **Variables:** Key-value pairs available in tests
   - **Retention Days:** How long to keep test results
   - **Browser Configs:** Which browsers and versions

### Environment Variables

Environment variables are accessible in custom steps:

```python
@when(parsers.parse('I set the feature flag'))
def set_feature_flag(test_context):
    flag_value = test_context.variables.get("FEATURE_FLAG", "false")
    # Use flag_value in your test
```

### Browser Configuration

Configure browsers per environment:

```json
{
  "browser": "chrome",
  "version": "latest",
  "channel": "stable"
}
```

**Browser options:** `chrome`, `chromium`, `firefox`, `webkit`, `edge`
**Channel options:** `stable`, `beta`, `dev`, `canary`

### Credentials Management

Store sensitive credentials in environment variables:

1. Set `credentials_env` in the environment config
2. The runner will load credentials from environment variables
3. Never hardcode credentials in test scenarios

---

## Scheduled Test Runs

### Creating a Schedule

1. Go to **Schedules**
2. Click **New Schedule**
3. Configure:
   - **Name:** Descriptive name
   - **Cron Expression:** When to run (see below)
   - **Tags:** Which scenarios to run
   - **Environment:** Target environment
   - **Browsers:** Which browsers

### Cron Expression Examples

| Expression | Description |
|------------|-------------|
| `0 * * * *` | Every hour |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 * * *` | Every day at midnight |
| `0 9 * * 1-5` | Weekdays at 9:00 AM |
| `0 0 * * 0` | Every Sunday at midnight |
| `0 9,17 * * 1-5` | Weekdays at 9 AM and 5 PM |
| `0 0 1 * *` | First day of each month |

### Managing Schedules

- **Toggle:** Enable/disable without deleting
- **Run Now:** Trigger immediately
- **View History:** See past runs from this schedule

---

## Troubleshooting

### Common Issues

#### Tests Not Starting

**Symptoms:** Runs stay in "queued" status

**Solutions:**
1. Check Celery worker is running: `docker compose logs worker`
2. Check Redis connection: `docker compose exec redis redis-cli ping`
3. Restart the worker: `docker compose restart worker`

#### Browser Connection Errors

**Symptoms:** "Failed to connect to browser" errors

**Solutions:**
1. Check browser container is running: `docker compose ps browser-chrome`
2. Verify the browser URL in environment config
3. Restart browser container: `docker compose restart browser-chrome`

#### Screenshots Not Loading

**Symptoms:** Screenshots show as broken images

**Solutions:**
1. Check MinIO is running: `docker compose ps minio`
2. Verify S3 credentials in environment variables
3. Check MinIO console for bucket existence

#### Sync Not Working

**Symptoms:** Scenarios not appearing after sync

**Solutions:**
1. Check repository URL is accessible
2. Verify branch name is correct
3. Check sync_path points to correct directory
4. Look at worker logs: `docker compose logs worker`

#### Authentication Errors

**Symptoms:** 401 Unauthorized responses

**Solutions:**
1. Verify API key is correct and active
2. Check API key hasn't expired
3. Ensure header is correct: `X-API-Key: your-key`

### Debugging Tips

1. **Check logs:**
   ```bash
   docker compose logs backend
   docker compose logs worker
   docker compose logs frontend
   ```

2. **Access database:**
   ```bash
   docker compose exec postgres psql -U sliples -d sliples
   ```

3. **Check Redis:**
   ```bash
   docker compose exec redis redis-cli
   > KEYS *
   ```

4. **Interactive testing:**
   Use the Test Mode page to step through scenarios interactively with a visible browser.

### Getting Help

1. Check the API documentation: `/docs`
2. Review error messages in run details
3. Check worker logs for detailed errors
4. Use the interactive test session to debug scenarios

---

## Best Practices

### Writing Good Scenarios

1. **Keep scenarios focused:** Test one thing at a time
2. **Use descriptive names:** Clear what the test does
3. **Tag appropriately:** Enable filtering and organization
4. **Avoid hardcoded values:** Use variables and environment config
5. **Add wait steps:** Handle async operations explicitly

### Organizing Test Suites

1. **Group by feature:** `login.feature`, `checkout.feature`
2. **Use tags consistently:** `@smoke`, `@regression`, `@feature-name`
3. **Separate concerns:** UI tests vs. API tests
4. **Prioritize:** Run critical tests first

### CI/CD Integration

1. **Fail fast:** Run smoke tests first
2. **Parallel execution:** Enable for faster feedback
3. **Handle failures gracefully:** Download reports, notify team
4. **Clean up:** Don't leave browsers running
5. **Retry flaky tests:** Once, not indefinitely

### Performance

1. **Use parallel execution:** For large test suites
2. **Optimize waits:** Use explicit waits, not sleep
3. **Minimize screenshots:** Only on failure by default
4. **Clean old runs:** Configure appropriate retention
