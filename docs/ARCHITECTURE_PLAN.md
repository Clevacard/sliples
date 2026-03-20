# Sliples - Web UI Automation Testing Platform

## Architecture Plan v1.0

---

## 1. Executive Summary

**Sliples** is a containerized Web UI automation testing platform that enables teams to write tests in plain English (Gherkin), execute them across multiple browsers, and integrate with CI/CD pipelines via REST API.

### Key Capabilities
- Gherkin-style test scenarios (git-friendly `.feature` files)
- Multi-browser support (Chrome, Firefox, extensible)
- Multi-environment execution (test/staging/prod)
- REST API with API key authentication
- HTML reports stored in PostgreSQL, screenshots in S3
- Email notifications on test completion
- 10 concurrent test scenarios capacity

---

## 2. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Backend API** | Python 3.12 + FastAPI | Fast async API, Python ecosystem |
| **Frontend** | React 18 + TypeScript + Vite | Modern, fast builds |
| **Test Runner** | Playwright + pytest-bdd | Modern browser automation, native Gherkin |
| **Browser Grid** | Playwright containers | Lighter than Selenium, built-in browser management |
| **Database** | PostgreSQL 16 | Reliable, JSON support for flexible schemas |
| **Object Storage** | S3 (MinIO for local dev) | Screenshots, artifacts |
| **Job Queue** | Redis + Celery | Distributed task execution |
| **Container Runtime** | Docker / Podman | Local dev + OpenShift compatibility |
| **Orchestration** | Docker Compose (dev) / OpenShift (prod) | Flexibility |

---

## 3. System Architecture

```
                                    +------------------+
                                    |   CI/CD Systems  |
                                    |  (Jenkins, etc.) |
                                    +--------+---------+
                                             |
                                             | REST API (API Key Auth)
                                             v
+------------------+              +----------+-----------+
|                  |   WebSocket  |                      |
|  React Frontend  +<------------>+   FastAPI Backend    |
|  (Test Editor,   |              |   - Test Orchestrator|
|   Dashboard,     |              |   - Report Generator |
|   Reports)       |              |   - Email Service    |
+------------------+              +----------+-----------+
                                             |
                        +--------------------+--------------------+
                        |                    |                    |
                        v                    v                    v
               +--------+-------+   +--------+-------+   +--------+-------+
               |     Redis      |   |   PostgreSQL   |   |   S3 / MinIO   |
               |  (Job Queue)   |   |   (Reports,    |   |  (Screenshots) |
               |                |   |    Configs)    |   |                |
               +----------------+   +----------------+   +----------------+
                        |
                        v
               +--------+-------+
               |  Celery Workers |
               |  (Test Runners) |
               +--------+-------+
                        |
        +---------------+---------------+
        |               |               |
        v               v               v
+-------+------+ +------+-------+ +-----+--------+
| Playwright   | | Playwright   | | Playwright   |
| Chrome       | | Firefox      | | (Future)     |
| Container    | | Container    | | Container    |
+--------------+ +--------------+ +--------------+
```

---

## 4. Component Details

### 4.1 Backend API (FastAPI)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/validate` | Validate API key |
| `GET` | `/api/v1/scenarios` | List all scenarios |
| `POST` | `/api/v1/scenarios/sync` | Sync scenarios from git repo |
| `GET` | `/api/v1/scenarios/{id}` | Get scenario details |
| `POST` | `/api/v1/runs` | Trigger test run (parallel execution) |
| `GET` | `/api/v1/runs` | List test runs |
| `GET` | `/api/v1/runs/{id}` | Get run status/results |
| `DELETE` | `/api/v1/runs/{id}` | Cancel running test |
| `GET` | `/api/v1/runs/{id}/report` | Get HTML report (pytest-html style) |
| `GET` | `/api/v1/environments` | List environments |
| `POST` | `/api/v1/environments` | Create environment config |
| `PUT` | `/api/v1/environments/{id}` | Update environment |
| `GET` | `/api/v1/repos` | List configured scenario repos |
| `POST` | `/api/v1/repos` | Add scenario repo |
| `POST` | `/api/v1/repos/{id}/sync` | Sync scenarios from specific repo |
| `POST` | `/api/v1/repos/sync-all` | Sync all repos |
| `GET` | `/api/v1/steps/custom` | List custom step definitions |
| `POST` | `/api/v1/steps/custom` | Create/update custom step |
| `POST` | `/api/v1/steps/custom/{id}/save-to-repo` | Commit step to repo |
| `GET` | `/api/v1/browsers` | List available browsers/versions |
| `GET` | `/api/v1/health` | Health check |

**Authentication:**
- API keys stored hashed in PostgreSQL
- Header: `X-API-Key: <key>`
- Keys scoped to environments (optional)

### 4.2 Frontend (React)

**Pages:**
1. **Dashboard** - Overview of recent runs, pass/fail rates
2. **Scenarios** - Browse scenarios by repo, filter by tags
3. **Scenario Editor** - Monaco editor with Gherkin syntax highlighting
4. **Custom Steps** - Monaco editor for Python step definitions, save to repo
5. **Test Runs** - List/filter runs, trigger new runs (parallel)
6. **Run Details** - Step-by-step results, screenshots, logs (pytest-html style)
7. **Environments** - Manage test/staging/prod configs, browser versions
8. **Repos** - Manage scenario git repositories, trigger sync
9. **Settings** - API keys, email config, S3 settings, retention policy

### 4.3 Test Runner (Celery Worker)

**Responsibilities:**
- Parse `.feature` files with pytest-bdd
- Execute steps against configured browser
- Capture screenshots on each step and on failure
- Upload screenshots to S3
- Report results back to API
- Support parallel scenario execution (up to 10)

**Step Definitions Library:**
```gherkin
# Navigation
Given I am on the "{page_name}" page
Given I navigate to "{url}"
When I click the "{element}" button
When I click on "{text}"

# Forms
When I enter "{value}" into the "{field}" field
When I select "{option}" from "{dropdown}"
When I check the "{checkbox}" checkbox

# Assertions
Then I should see "{text}"
Then the "{element}" should be visible
Then I should be on the "{page_name}" page
Then the page title should be "{title}"

# Waits
When I wait for {seconds} seconds
When I wait for the "{element}" to be visible

# Screenshots
Then I take a screenshot named "{name}"
```

### 4.4 Browser Grid

**Option A: Playwright Containers (Recommended)**
- `mcr.microsoft.com/playwright:v1.42.0-jammy`
- Connect via Playwright's remote browser protocol
- Lighter weight, faster startup

**Option B: Selenium Grid (Future)**
- For Safari, legacy browser support
- Can run alongside Playwright

### 4.5 Data Models

```
┌─────────────────────┐     ┌─────────────────────┐
│ ScenarioRepo        │     │ Scenario            │
├─────────────────────┤     ├─────────────────────┤
│ id: UUID            │     │ id: UUID            │
│ name: str           │     │ repo_id: UUID (FK)  │
│ git_url: str        │     │ name: str           │
│ branch: str         │     │ feature_path: str   │
│ sync_path: str      │     │ tags: str[]         │
│ last_synced: datetime     │ created_at: datetime│
│ created_at: datetime│     │ updated_at: datetime│
└─────────────────────┘     └─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ Environment         │     │ BrowserConfig       │
├─────────────────────┤     ├─────────────────────┤
│ id: UUID            │     │ id: UUID            │
│ name: str           │     │ environment_id: UUID│
│ base_url: str       │     │ browser: str        │
│ credentials_env: str│     │ version: str        │ # "latest" or pinned
│ variables: JSON     │     │ channel: str        │ # stable/beta/dev
│ retention_days: int │     └─────────────────────┘
│ created_at: datetime│
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ TestRun             │     │ TestResult          │
├─────────────────────┤     ├─────────────────────┤
│ id: UUID            │     │ id: UUID            │
│ scenario_ids: UUID[]│     │ test_run_id: UUID   │
│ environment_id: UUID│     │ scenario_id: UUID   │
│ status: enum        │     │ step_name: str      │
│ browser: str        │     │ status: enum        │
│ browser_version: str│     │ duration_ms: int    │
│ triggered_by: str   │     │ error_message: str  │
│ parallel: bool      │     │ screenshot_url: str │
│ started_at: datetime│     │ created_at: datetime│
│ finished_at: datetime     └─────────────────────┘
│ report_html: text   │
│ email_sent: bool    │
│ expires_at: datetime│     # For 12-month retention
└─────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐
│ ApiKey              │     │ CustomStep          │
├─────────────────────┤     ├─────────────────────┤
│ id: UUID            │     │ id: UUID            │
│ name: str           │     │ repo_id: UUID (FK)  │
│ key_hash: str       │     │ name: str           │
│ environment_ids: [] │     │ pattern: str        │ # Gherkin pattern
│ created_at: datetime│     │ code: text          │ # Python impl
│ last_used_at: datetime    │ committed: bool     │
│ active: bool        │     │ created_at: datetime│
└─────────────────────┘     └─────────────────────┘
```

---

## 5. Directory Structure

```
sliples/
├── docker-compose.yml           # Local development
├── docker-compose.override.yml  # Local overrides
├── Makefile                     # Common commands
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/                 # DB migrations
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── scenarios.py
│   │   │   │   ├── runs.py
│   │   │   │   ├── environments.py
│   │   │   │   └── health.py
│   │   │   ├── deps.py          # Dependencies
│   │   │   └── auth.py          # API key auth
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── test_runner.py
│   │   │   ├── report_generator.py   # pytest-html style
│   │   │   ├── email_service.py
│   │   │   ├── s3_service.py
│   │   │   ├── git_sync_service.py   # Multi-repo scenario sync
│   │   │   └── retention_service.py  # 12-month cleanup
│   │   └── workers/
│   │       ├── celery_app.py
│   │       ├── tasks.py
│   │       └── scheduled.py          # Celery beat tasks (retention)
│   └── tests/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api/                 # API client
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ScenarioEditor.tsx
│   │   │   ├── TestRuns.tsx
│   │   │   ├── RunDetails.tsx
│   │   │   ├── Environments.tsx
│   │   │   └── Settings.tsx
│   │   └── hooks/
│   └── tests/
│
├── runner/                      # Test runner worker
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── steps/                   # Built-in Gherkin step definitions
│   │   ├── navigation.py
│   │   ├── forms.py
│   │   ├── assertions.py
│   │   └── common.py
│   ├── custom_steps/            # User-defined steps (synced from repos)
│   └── conftest.py
│
├── scenarios/                   # Multi-repo test scenarios (git-synced)
│   ├── repo-a/                  # Cloned from external repo A
│   │   ├── login.feature
│   │   └── custom_steps/        # Repo-specific custom steps
│   ├── repo-b/                  # Cloned from external repo B
│   │   └── api-tests.feature
│   └── sliples/                 # Internal acceptance tests
│       └── sliples-acceptance.feature
│
├── openshift/                   # OpenShift manifests
│   ├── namespace.yaml
│   ├── backend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── route.yaml
│   ├── frontend/
│   ├── runner/
│   ├── postgres/
│   ├── redis/
│   └── secrets/
│
└── docs/
    ├── ARCHITECTURE_PLAN.md
    ├── API.md
    └── DEPLOYMENT.md
```

---

## 6. Configuration & Credentials

### Environment Variables (Backend)

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/sliples

# Redis
REDIS_URL=redis://host:6379/0

# S3
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=sliples-screenshots
S3_ACCESS_KEY=${S3_ACCESS_KEY}
S3_SECRET_KEY=${S3_SECRET_KEY}

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=${SMTP_USER}
SMTP_PASSWORD=${SMTP_PASSWORD}
EMAIL_FROM=sliples@example.com

# App
SECRET_KEY=${SECRET_KEY}
ALLOWED_ORIGINS=https://sliples.example.com
```

### Test Environment Credentials (per environment)

```bash
# Injected into runner containers per environment
TEST_USERNAME=${TEST_ENV_USERNAME}
TEST_PASSWORD=${TEST_ENV_PASSWORD}
# ... additional credentials as needed
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project scaffolding (backend, frontend, runner)
- [ ] Docker Compose setup
- [ ] PostgreSQL schema + migrations
- [ ] Basic FastAPI with health endpoint
- [ ] React app skeleton with routing

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 1 - Foundation (tag: `@phase1`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC1.1 | Health endpoint returns 200 with healthy status | `AC1.1 - Backend health endpoint returns healthy status` |
| AC1.2 | Health includes database connectivity status | `AC1.2 - Health endpoint includes database connectivity status` |
| AC1.3 | Health includes Redis connectivity status | `AC1.3 - Health endpoint includes Redis connectivity status` |
| AC1.4 | Frontend loads without JavaScript errors | `AC1.4 - Frontend application loads without errors` |
| AC1.5 | Frontend routing works for all main pages | `AC1.5 - Frontend routing works for all main pages` |
| AC1.6 | Database migrations complete successfully | `AC1.6 - Database migrations run successfully` |
| AC1.7 | All Docker containers are running | `AC1.7 - All Docker containers are running` |

**Definition of Done:** All AC1.x scenarios pass when executed against the deployed instance.

### Phase 2: Core API (Week 2-3)
- [ ] API key authentication
- [ ] Environment CRUD endpoints
- [ ] Scenario sync from filesystem
- [ ] Test run trigger endpoint
- [ ] Celery + Redis setup

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 2 - Core API (tag: `@phase2`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC2.1 | Valid API key authenticates successfully | `AC2.1 - Valid API key authenticates successfully` |
| AC2.2 | Invalid API key is rejected with 401 | `AC2.2 - Invalid API key is rejected` |
| AC2.3 | Missing API key returns 401 | `AC2.3 - Missing API key is rejected` |
| AC2.4 | Environment can be created via POST | `AC2.4 - Create a new environment` |
| AC2.5 | Environments can be listed via GET | `AC2.5 - List all environments` |
| AC2.6 | Environment can be updated via PUT | `AC2.6 - Update an existing environment` |
| AC2.7 | Scenarios can be listed via GET | `AC2.7 - List all test scenarios` |
| AC2.8 | Scenarios sync from filesystem | `AC2.8 - Sync scenarios from filesystem` |
| AC2.9 | Test run can be triggered via POST | `AC2.9 - Trigger a test run via API` |
| AC2.10 | Celery worker processes queued tasks | `AC2.10 - Celery worker is processing tasks` |

**Definition of Done:** All AC2.x scenarios pass when executed against the deployed instance.

### Phase 3: Test Runner (Week 3-4)
- [ ] Playwright integration
- [ ] Basic step definitions
- [ ] Screenshot capture to S3/MinIO
- [ ] Test result reporting
- [ ] Multi-browser support

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 3 - Test Runner (tag: `@phase3`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC3.1 | Simple navigation test executes successfully | `AC3.1 - Simple navigation test executes successfully` |
| AC3.2 | Screenshots are captured on test failure | `AC3.2 - Screenshots are captured on test failure` |
| AC3.3 | Screenshots are uploaded to S3/MinIO | `AC3.3 - Screenshots are uploaded to S3/MinIO` |
| AC3.4 | Tests can run on Chrome browser | `AC3.4 - Tests can run on Chrome browser` |
| AC3.5 | Tests can run on Firefox browser | `AC3.5 - Tests can run on Firefox browser` |
| AC3.6 | Navigation step definitions work | `AC3.6 - Navigation step definitions work correctly` |
| AC3.7 | Form interaction steps work | `AC3.7 - Form interaction step definitions work correctly` |
| AC3.8 | Test results include step-level detail | `AC3.8 - Test results are stored with step-level detail` |
| AC3.9 | Multiple scenarios can run in parallel | `AC3.9 - Multiple scenarios can run in parallel` |

**Definition of Done:** All AC3.x scenarios pass when executed against the deployed instance.

### Phase 4: Frontend (Week 4-5)
- [ ] Dashboard with run history
- [ ] Scenario editor (Monaco)
- [ ] Test run management
- [ ] Report viewer with screenshots
- [ ] Environment configuration

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 4 - Frontend (tag: `@phase4`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC4.1 | Dashboard displays recent test runs | `AC4.1 - Dashboard displays recent test runs` |
| AC4.2 | Dashboard shows pass/fail statistics | `AC4.2 - Dashboard shows pass/fail statistics` |
| AC4.3 | Scenario editor loads with syntax highlighting | `AC4.3 - Scenario editor loads with syntax highlighting` |
| AC4.4 | Scenario editor saves changes | `AC4.4 - Scenario editor saves changes` |
| AC4.5 | Test runs page allows triggering new runs | `AC4.5 - Test runs page allows triggering new runs` |
| AC4.6 | Test runs can be filtered and searched | `AC4.6 - Test runs can be filtered and searched` |
| AC4.7 | Run details shows step-by-step results | `AC4.7 - Run details page shows step-by-step results` |
| AC4.8 | Run details displays screenshots | `AC4.8 - Run details page displays screenshots` |
| AC4.9 | Environments page allows CRUD operations | `AC4.9 - Environments page allows CRUD operations` |
| AC4.10 | Settings page allows API key management | `AC4.10 - Settings page allows API key management` |

**Definition of Done:** All AC4.x scenarios pass when executed against the deployed instance.

### Phase 5: Notifications & Reports (Week 5-6)
- [ ] HTML report generation
- [ ] Email notifications
- [ ] WebSocket for live updates

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 5 - Notifications & Reports (tag: `@phase5`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC5.1 | HTML report is generated for completed runs | `AC5.1 - HTML report is generated for completed runs` |
| AC5.2 | HTML report includes embedded screenshots | `AC5.2 - HTML report includes embedded screenshots` |
| AC5.3 | HTML report can be downloaded from UI | `AC5.3 - HTML report can be downloaded from UI` |
| AC5.4 | Email notification sent on test completion | `AC5.4 - Email notification is sent on test completion` |
| AC5.5 | Email includes failure details | `AC5.5 - Email notification includes failure details` |
| AC5.6 | WebSocket provides real-time updates | `AC5.6 - WebSocket provides real-time run updates` |
| AC5.7 | UI updates in real-time during execution | `AC5.7 - UI updates in real-time during test execution` |
| AC5.8 | Reports are stored in PostgreSQL | `AC5.8 - Reports are stored in PostgreSQL` |

**Definition of Done:** All AC5.x scenarios pass when executed against the deployed instance.

### Phase 6: OpenShift Deployment (Week 6-7)
- [ ] OpenShift manifests
- [ ] Secrets management
- [ ] Route configuration
- [ ] Scaling configuration
- [ ] CI/CD pipeline integration

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 6 - OpenShift Deployment (tag: `@phase6`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC6.1 | OpenShift manifests are valid YAML | `AC6.1 - OpenShift manifests are valid` |
| AC6.2 | All deployments running in OpenShift | `AC6.2 - All deployments are running in OpenShift` |
| AC6.3 | Secrets are properly configured | `AC6.3 - Secrets are properly configured` |
| AC6.4 | Routes are accessible externally via HTTPS | `AC6.4 - Routes are accessible externally` |
| AC6.5 | Worker pods can scale horizontally | `AC6.5 - Worker pods can scale horizontally` |
| AC6.6 | PostgreSQL data persists across restarts | `AC6.6 - PostgreSQL data persists across restarts` |
| AC6.7 | CI/CD pipeline can trigger tests via API | `AC6.7 - CI/CD pipeline can trigger tests via API` |
| AC6.8 | Resource limits are properly configured | `AC6.8 - Resource limits are properly configured` |

**Definition of Done:** All AC6.x scenarios pass when executed against the OpenShift deployment.

### Phase 7: Polish & Documentation (Week 7-8)
- [ ] API documentation (OpenAPI)
- [ ] User guide
- [ ] Performance testing
- [ ] Security review

#### Acceptance Criteria
See `scenarios/sliples-acceptance.feature` - Epic: Phase 7 - Polish & Documentation (tag: `@phase7`)

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC7.1 | OpenAPI documentation is available | `AC7.1 - OpenAPI documentation is available` |
| AC7.2 | Swagger UI is accessible and functional | `AC7.2 - Swagger UI is accessible` |
| AC7.3 | User guide documentation exists | `AC7.3 - User guide documentation exists` |
| AC7.4 | System handles 10 concurrent scenarios | `AC7.4 - System handles 10 concurrent test scenarios` |
| AC7.5 | API response times are acceptable | `AC7.5 - API response times are acceptable` |
| AC7.6 | Security headers are properly configured | `AC7.6 - Security headers are properly configured` |
| AC7.7 | Input validation prevents injection | `AC7.7 - Input validation prevents injection attacks` |
| AC7.8 | Error messages are user-friendly | `AC7.8 - Error messages are user-friendly` |

**Definition of Done:** All AC7.x scenarios pass when executed against the deployed instance.

### Dogfooding: Self-Test Validation

As a meta-validation, Sliples should be able to test itself using its own acceptance criteria:

| ID | Criterion | Gherkin Scenario |
|----|-----------|------------------|
| AC-DOG-1 | Sliples can load its own acceptance tests | `AC-DOG-1 - Sliples can load its own acceptance tests` |
| AC-DOG-2 | Sliples can execute tests against itself | `AC-DOG-2 - Sliples can execute tests against itself` |
| AC-DOG-3 | Sliples UI tests pass when run by Sliples | `AC-DOG-3 - Sliples UI tests pass when run by Sliples` |
| AC-DOG-4 | Full regression suite runs nightly | `AC-DOG-4 - Full regression suite can run nightly` |
| AC-DOG-5 | PR validation uses Sliples | `AC-DOG-5 - PR validation uses Sliples to test changes` |

**Ultimate Definition of Done:** Sliples can successfully execute all acceptance tests against itself, generating reports and notifications as specified.

---

## 8. OpenShift Deployment Architecture

```
Namespace: sliples
├── Deployments
│   ├── sliples-backend (2 replicas)
│   ├── sliples-frontend (2 replicas)
│   ├── sliples-worker (3 replicas, scalable)
│   ├── sliples-postgres (1 replica, PVC)
│   └── sliples-redis (1 replica)
│
├── Services
│   ├── sliples-backend-svc
│   ├── sliples-frontend-svc
│   ├── sliples-postgres-svc
│   └── sliples-redis-svc
│
├── Routes
│   ├── sliples.apps.example.com (frontend)
│   └── api.sliples.apps.example.com (backend)
│
├── Secrets
│   ├── sliples-db-credentials
│   ├── sliples-s3-credentials
│   ├── sliples-smtp-credentials
│   └── sliples-test-env-credentials
│
├── ConfigMaps
│   ├── sliples-backend-config
│   └── sliples-runner-config
│
└── PersistentVolumeClaims
    └── sliples-postgres-pvc (10Gi)
```

---

## 9. API Integration Example

### Jenkins Pipeline

```groovy
pipeline {
    environment {
        SLIPLES_API_KEY = credentials('sliples-api-key')
        SLIPLES_API_URL = 'https://api.sliples.apps.example.com'
    }
    stages {
        stage('UI Tests') {
            steps {
                script {
                    // Trigger test run
                    def response = httpRequest(
                        url: "${SLIPLES_API_URL}/api/v1/runs",
                        httpMode: 'POST',
                        customHeaders: [[name: 'X-API-Key', value: SLIPLES_API_KEY]],
                        contentType: 'APPLICATION_JSON',
                        requestBody: '''{
                            "scenario_tags": ["smoke"],
                            "environment": "staging",
                            "browsers": ["chrome", "firefox"]
                        }'''
                    )
                    def runId = readJSON(text: response.content).id

                    // Poll for completion
                    timeout(time: 30, unit: 'MINUTES') {
                        waitUntil {
                            def status = httpRequest(
                                url: "${SLIPLES_API_URL}/api/v1/runs/${runId}",
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

## 10. Security Considerations

1. **API Keys** - Hashed with bcrypt, rotatable, scopeable
2. **Secrets** - All credentials via OpenShift secrets, never in code
3. **Network** - Internal services not exposed, only routes
4. **Browser Isolation** - Each test runs in isolated container
5. **Input Validation** - Strict Pydantic schemas
6. **CORS** - Restricted to known origins
7. **Rate Limiting** - API rate limits per key

---

## 11. Design Decisions (Resolved)

| # | Question | Decision |
|---|----------|----------|
| 1 | **Git Integration** | Scenarios pulled from multiple external repos into separate folders per repo |
| 2 | **Data Retention** | Auto-delete test runs and reports after 12 months |
| 3 | **Browser Versions** | Use latest by default, allow pinning specific versions per environment |
| 4 | **Custom Steps** | Allow custom step definitions via UI editor, offer to save to repo |
| 5 | **Parallel Execution** | Maximum parallelization - run scenarios concurrently up to worker capacity |
| 6 | **Report Format** | pytest-html style reports |

### Implementation Details

**Multi-Repo Scenario Sync:**
```
scenarios/
├── repo-a/           # Cloned from git@github.com:org/repo-a.git
│   ├── login.feature
│   └── checkout.feature
├── repo-b/           # Cloned from git@github.com:org/repo-b.git
│   └── api-tests.feature
└── sliples/          # Internal acceptance tests
    └── sliples-acceptance.feature
```

**Data Retention Policy:**
- Celery beat scheduled job runs daily
- Deletes test runs older than 12 months
- Deletes orphaned screenshots from S3
- Configurable retention period per environment (optional)

**Browser Version Configuration:**
```json
{
  "browser": "chrome",
  "version": "latest",        // or "122.0.6261.94"
  "channel": "stable"         // stable, beta, dev
}
```

**Custom Step Definitions:**
- UI provides Monaco editor for Python step definitions
- Validates syntax before saving
- Offers to commit to configured scenarios repo
- Steps stored in `custom_steps/` directory per repo

---

## 12. Approval Status

| Item | Status |
|------|--------|
| Technology stack | Pending |
| Component architecture | Pending |
| Directory structure | Pending |
| API design | Pending |
| Implementation phases | Pending |
| OpenShift architecture | Pending |
| Design decisions | Pending |

**Awaiting approval to begin implementation.**

---

*Document Version: 1.1*
*Created: 2026-03-20*
*Updated: 2026-03-20 - Resolved open questions*
