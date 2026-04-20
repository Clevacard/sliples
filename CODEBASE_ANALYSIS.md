# Sliples Codebase Architecture Analysis

## Executive Summary

The Sliples codebase is a full-stack test automation platform with:
- **Backend**: FastAPI (Python) with SQLAlchemy ORM, Celery workers for async test execution, Playwright for browser automation
- **Frontend**: React with TypeScript, Zustand for state management, Tailwind CSS
- **Database**: PostgreSQL with UUID primary keys
- **Test Framework**: Gherkin (feature files), pytest-bdd compatible, with custom step support

**Key Finding**: Environment variables are already fully implemented at the database and frontend level, but are NOT currently being used in test step execution.

---

## 1. SCENARIO/FEATURE FILE PARSING & STORAGE

### 1.1 Parser Service
**File**: `/Users/ptrk/Agantis/sliples/backend/app/api/routes/parser.py`

The parser extracts and validates Gherkin steps from feature files:

```python
def extract_steps(content: str) -> list[tuple[int, str, str, str]]:
    """Extract steps from Gherkin content.
    
    Returns list of (line_number, keyword, step_text, full_line)
    """
    steps = []
    lines = content.split('\n')
    step_pattern = re.compile(r'^\s*(Given|When|Then|And|But)\s+(.+)$', re.IGNORECASE)
    
    for i, line in enumerate(lines, 1):
        match = step_pattern.match(line)
        if match:
            keyword = match.group(1)
            text = match.group(2).strip()
            steps.append((i, keyword, text, line.strip()))
    
    return steps
```

**Built-in Patterns**: 90+ predefined regex patterns for common BDD steps (navigation, clicking, assertions, etc.)

### 1.2 Scenario Model
**File**: `/Users/ptrk/Agantis/sliples/backend/app/models/scenario.py`

```python
class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("scenario_repos.id"), nullable=True)
    name = Column(String(255), nullable=False)
    feature_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)  # Full Gherkin content
    tags = Column(ARRAY(String), default=[])  # @smoke, @critical, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 1.3 Step Validation Flow
**Endpoint**: `POST /api/v1/parser/validate`

1. Extracts steps from feature content
2. Validates each step against:
   - **Custom steps** (user-defined patterns) - checked first (precedence)
   - **Built-in patterns** - 90+ standard BDD patterns
3. Returns detailed validation for each step including:
   - Line number, keyword, text
   - Match status, matched pattern, source (builtin/custom)

---

## 2. TEST STEP EXECUTION

### 2.1 Test Executor Service
**File**: `/Users/ptrk/Agantis/sliples/backend/app/services/test_executor.py` (968 lines)

#### GherkinStepRegistry Class
Registry of step handlers with built-in implementations:

```python
class GherkinStepRegistry:
    """Registry of Gherkin step definitions with their implementations."""
    
    def __init__(self, pages: Optional[dict[str, str]] = None):
        self._steps: dict[str, tuple[re.Pattern, Callable]] = {}
        self._pages = pages or {}  # page_name -> path mapping
        self._register_builtin_steps()
    
    def find_handler(self, step_text: str) -> Optional[tuple[Callable, tuple]]:
        """Find a handler for the given step text."""
        for pattern, (regex, handler) in self._steps.items():
            match = regex.fullmatch(step_text)
            if match:
                return handler, match.groups()
        return None
```

#### Built-in Step Implementations
- **Navigation**: Navigate to URLs/named pages, reload, back, forward
- **Clicking**: Click by test-id, role, text, CSS selector
- **Input**: Fill fields, clear, press keys, select options
- **Assertions**: Visibility, text content, URL, title, state
- **Waiting**: Wait for elements, page load
- **Utilities**: Screenshots, form submission

#### Custom Step Execution
**Lines 620-730**: Dynamic code execution via Python `exec()`

```python
async def _execute_custom_step_code(self, page, code: str, params: dict):
    """Execute custom step code.
    
    The custom step code is isolated in a function that receives:
    - page: The Playwright page object
    - Captured parameters from the step pattern
    """
    # Build parameter assignments
    param_assignments = '\n'.join(
        f'    {name} = __params__["{name}"]'
        for name in params.keys()
    )
    
    # Create isolated function
    full_code = f'''
async def __custom_step__(page, __params__):
{param_assignments}
{textwrap.indent(code, "    ")}
'''
    
    # Execute and call
    exec_globals = {}
    exec(full_code, exec_globals)
    await exec_globals['__custom_step__'](page, params)
```

### 2.2 Test Execution Flow
**File**: `/Users/ptrk/Agantis/sliples/backend/app/services/test_executor.py`

```python
async def run_test_execution(
    run_id: str,
    scenarios: list[dict],  # id, name, content
    browser: str,
    base_url: str,
    locale: str = "en-GB",
    timezone_id: str = "Europe/London",
    custom_steps: Optional[dict] = None,
    pages: Optional[dict[str, str]] = None,
    progress_callback: Optional[Callable] = None,
) -> TestExecutionResult:
    """
    Execute scenarios in a browser context.
    
    Returns TestExecutionResult with all step results.
    """
```

**Execution Steps**:
1. Create Playwright browser context with locale & timezone
2. Parse each scenario's Gherkin content
3. For each scenario:
   - Create a new page
   - For each step:
     - Extract captured parameters from pattern match
     - Find matching handler (custom or builtin)
     - Execute handler with page and parameters
     - Capture screenshot on failure
     - Track timing and status

---

## 3. ENVIRONMENT MODEL & VARIABLES

### 3.1 Environment Model
**File**: `/Users/ptrk/Agantis/sliples/backend/app/models/environment.py`

```python
class Environment(Base):
    """Test environment configuration."""
    
    __tablename__ = "environments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=False)
    locale = Column(String(20), default="en-GB")  # Browser locale
    timezone_id = Column(String(50), default="Europe/London")  # IANA timezone
    credentials_env = Column(String(100), nullable=True)
    variables = Column(JSON, default={})  # ✓ ALREADY EXISTS!
    retention_days = Column(Integer, default=365)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="environments")
    browser_configs = relationship("BrowserConfig", back_populates="environment")
    test_runs = relationship("TestRun", back_populates="environment")
```

**Key Fields**:
- `variables: dict` - JSON field storing key-value pairs
- `locale` - Browser locale for number/date formatting
- `timezone_id` - IANA timezone for date/time in browser
- `credentials_env` - Reference to environment variable

### 3.2 Environment API Routes
**File**: `/Users/ptrk/Agantis/sliples/backend/app/api/routes/environments.py`

#### Pydantic Models

```python
class EnvironmentCreate(BaseModel):
    name: str
    base_url: str
    locale: str = "en-GB"
    timezone_id: str = "Europe/London"
    credentials_env: Optional[str] = None
    variables: dict = {}  # ← Accepts variables on create
    retention_days: int = 365
    browser_configs: list[BrowserConfigCreate] = []

class EnvironmentUpdate(BaseModel):
    name: Optional[str] = None
    variables: Optional[dict] = None  # ← Can update variables
    # ... other fields
```

#### Endpoints

- `GET /api/v1/environments` - List all environments
- `POST /api/v1/environments` - Create environment with variables
- `PUT /api/v1/environments/{id}` - Update environment variables
- `GET /api/v1/environments/{id}` - Get environment with variables

---

## 4. FRONTEND IMPLEMENTATION

### 4.1 Environment Type Definition
**File**: `/Users/ptrk/Agantis/sliples/frontend/src/api/client.ts`

```typescript
export interface Environment {
  id: string
  project_id?: string
  name: string
  base_url: string
  locale?: string
  timezone_id?: string
  credentials_env?: string
  variables: Record<string, string>  // ← Variables as object
  retention_days: number
  created_at?: string
}

export interface EnvironmentCreate {
  name: string
  base_url: string
  locale?: string
  timezone_id?: string
  variables?: Record<string, string>
  retention_days?: number
}
```

### 4.2 Environment Form Component
**File**: `/Users/ptrk/Agantis/sliples/frontend/src/components/EnvironmentForm.tsx`

Uses `KeyValueEditor` component to manage variables:

```typescript
const [variables, setVariables] = useState<KeyValuePair[]>([])

// Form submission
const data = {
  name: name.trim(),
  base_url: baseUrl.trim(),
  variables: pairsToRecord(variables),  // Convert to Record<string, string>
  // ...
}

// Validation
const keys = variables.map((p) => p.key.trim()).filter(Boolean)
const uniqueKeys = new Set(keys)
if (keys.length !== uniqueKeys.size) {
  newErrors.variables = 'Duplicate variable keys are not allowed'
}
```

### 4.3 KeyValue Editor Component
**File**: `/Users/ptrk/Agantis/sliples/frontend/src/components/KeyValueEditor.tsx`

Features:
- Add/remove variable pairs
- Automatic masking of sensitive values (password, secret, token, api_key, credential, auth)
- Toggle visibility of sensitive values
- Validation for duplicate keys

```typescript
const DEFAULT_SENSITIVE_PATTERNS = [
  /password/i,
  /secret/i,
  /token/i,
  /api.?key/i,
  /credential/i,
  /auth/i,
]

function isSensitiveKey(key: string): boolean {
  return DEFAULT_SENSITIVE_PATTERNS.some((pattern) => pattern.test(key))
}

// Value stored as password input type when sensitive
<input
  type={isValueVisible ? 'text' : 'password'}
  // ...
/>
```

### 4.4 Environments Page
**File**: `/Users/ptrk/Agantis/sliples/frontend/src/pages/Environments.tsx`

Features:
- Display variable count per environment
- Expandable cards showing all variables
- Automatic masking of sensitive values in display

```typescript
const getVariableCount = (env: Environment): number => {
  return Object.keys(env.variables || {}).length
}

// Display
{variableCount > 0 && (
  <span className="px-2 py-0.5 text-xs font-medium bg-gray-700">
    {variableCount} variable{variableCount !== 1 ? 's' : ''}
  </span>
)}

// Expanded view
{variables.map(([key, value]) => {
  const sensitive = isSensitiveKey(key)
  return (
    <div key={key}>
      <span className="text-primary-400">{key}</span>
      <span className="text-gray-300">
        {sensitive ? maskValue(value) : value}
      </span>
    </div>
  )
})}
```

### 4.5 Environments Store
**File**: `/Users/ptrk/Agantis/sliples/frontend/src/store/environments.ts`

Zustand store managing environment state:

```typescript
interface EnvironmentsState {
  environments: Environment[]
  selectedEnvironment: Environment | null
  isLoading: boolean
  error: string | null
  
  fetchEnvironments: () => Promise<void>
  createEnvironment: (data: EnvironmentCreate) => Promise<Environment>
  updateEnvironment: (id: string, data: EnvironmentUpdate) => Promise<Environment>
  deleteEnvironment: (id: string) => Promise<void>
  selectEnvironment: (environment: Environment | null) => void
}
```

---

## 5. CUSTOM STEPS

### 5.1 Custom Step Model
**File**: `/Users/ptrk/Agantis/sliples/backend/app/models/custom_step.py`

```python
class CustomStep(Base):
    """User-defined Gherkin step definition."""
    
    __tablename__ = "custom_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("scenario_repos.id"), nullable=True)
    name = Column(String(255), nullable=False)  # Human-readable name
    pattern = Column(String(500), nullable=False)  # Regex pattern for matching
    code = Column(Text, nullable=False)  # Python implementation
    committed = Column(Boolean, default=False)  # Whether saved to repo
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### 5.2 Custom Steps API Routes
**File**: `/Users/ptrk/Agantis/sliples/backend/app/api/routes/steps.py`

Endpoints:
- `GET /api/v1/steps` - List all custom steps
- `POST /api/v1/steps` - Create custom step
- `PUT /api/v1/steps/{id}` - Update custom step
- `DELETE /api/v1/steps/{id}` - Delete custom step
- `POST /api/v1/steps/{id}/save-to-repo` - Commit to git

#### Create Custom Step

```python
@router.post("/steps", response_model=StepResponse, status_code=201)
async def create_custom_step(
    step: StepCreate,
    db: Session = Depends(get_db),
):
    """Create a new custom step definition."""
    # Check for duplicate pattern within project
    existing = db.query(CustomStep).filter(
        CustomStep.pattern == step.pattern,
        CustomStep.project_id == project.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Pattern already exists")
    
    db_step = CustomStep(
        project_id=project.id,
        name=step.name,
        pattern=step.pattern,
        code=step.get_code(),
    )
    db.add(db_step)
    db.commit()
    return db_step
```

### 5.3 Custom Step Flow (End-to-End)

**Creation**:
1. User defines pattern and Python code in CustomSteps page
2. Frontend sends POST /steps with pattern and code
3. Backend validates pattern is valid regex
4. Stores in custom_steps table
5. Marked as uncommitted (not saved to repo)

**Parsing**:
1. Parser loads all custom steps for project
2. When validating Gherkin, custom patterns checked FIRST (precedence)
3. First matching pattern wins

**Execution**:
1. Test executor loads custom steps from database
2. During step execution:
   - Finds matching handler (custom or builtin)
   - For custom steps: extracts captured groups from regex match
   - Passes captured groups as parameters to custom code
   - Code executed via Python exec() with isolated namespace
   - page object and parameters available to code

---

## 6. INTERACTIVE EXECUTOR (TEST MODE)

### 6.1 Interactive Executor Service
**File**: `/Users/ptrk/Agantis/sliples/backend/app/services/interactive_executor.py`

Manages browser sessions for human-driven testing:

```python
class InteractiveExecutor:
    """Manages interactive browser sessions for human testers."""
    
    @classmethod
    async def create_session(
        cls,
        session_id: str,
        browser_type: str = "chromium",
        base_url: str = "",
        headless: bool = False,
        pages: Optional[dict[str, str]] = None,
        locale: str = "en-GB",
        timezone_id: str = "Europe/London",
    ) -> "InteractiveSession":
        """Create a new interactive session."""
```

Used in `/test-session/start` endpoint for live test mode.

---

## 7. TEST EXECUTION FLOW (END-TO-END)

### 7.1 Test Run Trigger
**File**: `/Users/ptrk/Agantis/sliples/backend/app/api/routes/runs.py`

```python
class TestRunCreate(BaseModel):
    scenario_tags: list[str] = []
    scenario_ids: list[UUID] = []
    environment: str  # Environment name (resolved to Environment object)
    browsers: list[str] = ["chrome"]
    parallel: bool = True

@router.post("/runs")
async def create_run(run: TestRunCreate, db: Session, ...):
    # Find environment by name
    env = db.query(Environment).filter(Environment.name == run.environment).first()
    
    # Create TestRun record
    db_run = TestRun(
        scenario_ids=scenario_ids,
        environment_id=env.id,  # ← Environment with variables
        browser=browser,
        status=RunStatus.QUEUED,
    )
    
    # Queue Celery task
    task = execute_test_run.delay(str(db_run.id))
```

### 7.2 Celery Task Execution
**File**: `/Users/ptrk/Agantis/sliples/backend/app/workers/tasks.py`

```python
@celery_app.task(bind=True, max_retries=3)
def execute_test_run(self, run_id: str):
    """Execute a test run."""
    db = SessionLocal()
    
    # Fetch the test run
    run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
    
    # Get environment
    environment = run.environment  # ← Contains variables!
    base_url = environment.base_url
    
    # Load scenarios
    scenarios = db.query(Scenario).filter(Scenario.id.in_(run.scenario_ids)).all()
    
    # Load custom steps
    custom_steps = {}
    custom_step_records = db.query(CustomStep).all()
    for step in custom_step_records:
        custom_steps[step.pattern] = step.code
    
    # Load pages
    pages = load_pages_for_environment(db, environment.project_id, environment.id)
    
    # Execute tests
    execution_result = await run_test_execution(
        run_id=run_id,
        scenarios=scenario_data,
        browser=run.browser,
        base_url=base_url,
        locale=environment.locale or "en-GB",
        timezone_id=environment.timezone_id or "Europe/London",
        custom_steps=custom_steps,
        pages=pages,
        progress_callback=update_progress,
    )
```

**⚠️ KEY FINDING**: The `environment.variables` dict is loaded but NOT passed to test executor!

### 7.3 Test Results Storage
**File**: `/Users/ptrk/Agantis/sliples/backend/app/models/test_run.py`

```python
class TestResult(Base):
    """Result of a single test step."""
    
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id"))
    scenario_id = Column(UUID(as_uuid=True), nullable=True)
    scenario_name = Column(String(255), nullable=True)
    step_name = Column(String(500), nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING)
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    screenshot_url = Column(String(500), nullable=True)
```

---

## 8. PAGES & NAMED NAVIGATION

### 8.1 Page Model
**File**: `/Users/ptrk/Agantis/sliples/backend/app/models/page.py`

```python
class Page(Base):
    """Named page with URL path mapping."""
    
    __tablename__ = "pages"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String(100), nullable=False)  # "Login", "Dashboard"
    path = Column(String(500), nullable=False)  # "/login", "/dashboard"
    description = Column(Text, nullable=True)

class PageEnvironmentOverride(Base):
    """Override page path for a specific environment."""
    
    __tablename__ = "page_environment_overrides"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"))
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id"))
    path = Column(String(500), nullable=False)  # Override path per environment
```

**Usage in Steps**: 
- `When I navigate to the "Login" page` → resolves to page path
- Different paths per environment via overrides

---

## 9. VARIABLE/PARAMETER HANDLING IN STEPS

### 9.1 Builtin Steps - Named Page Resolution

```python
async def _step_navigate(self, page, url_or_page: str):
    """Navigate to URL or named page."""
    # Check if this is a named page
    resolved_path = self.resolve_page(url_or_page)
    if resolved_path:
        url = resolved_path
    else:
        url = url_or_page
    
    # Build full URL
    if not url.startswith(("http://", "https://")):
        base_url = getattr(page, "_base_url", "")
        url = f"{base_url.rstrip('/')}{url}"
    
    await page.goto(url, wait_until="domcontentloaded")
```

### 9.2 Custom Steps - Parameter Capture

```python
# Regex pattern extracts parameters:
# Pattern: r'I fill "([^"]*)" with "([^"]*)"'
# Step: 'I fill "username" with "john@example.com"'
# Captured: ("username", "john@example.com")

# Parameters passed to custom code:
async def _execute_custom_step_code(self, page, code: str, params: dict):
    """Execute custom step code with captured parameters."""
    param_assignments = '\n'.join(
        f'    {name} = __params__["{name}"]'
        for name in params.keys()
    )
    
    # User's custom code can use: field, value (captured from pattern)
```

### 9.3 Browser Context Configuration

```python
async def create_context(
    self,
    base_url: str,
    locale: str = "en-GB",
    timezone_id: str = "Europe/London"
):
    """Create browser context with locale and timezone."""
    context_kwargs = {
        "base_url": base_url,
        "locale": locale,
        "timezone_id": timezone_id,
    }
    self._context = await self._browser.new_context(**context_kwargs)
    page = await self._context.new_page()
    page._base_url = base_url  # Store for navigation resolution
```

---

## 10. EXISTING CONCEPTS FOUND

### ✓ Variables Field
- **Location**: `Environment.variables` (JSON column)
- **Storage**: Dictionary of key-value pairs
- **Status**: FULLY IMPLEMENTED in database and frontend
- **Usage**: NOT YET integrated into test execution

### ✓ Locale & Timezone
- **Location**: `Environment.locale`, `Environment.timezone_id`
- **Status**: FULLY IMPLEMENTED and used in test execution
- **Implementation**: Passed to Playwright browser context

### ✓ Parameter Capture in Custom Steps
- **Location**: `/Users/ptrk/Agantis/sliples/backend/app/services/test_executor.py` line 825
- **Status**: FULLY IMPLEMENTED for custom steps via regex groups
- **Example**: Pattern `r'I fill "([^"]*)" with "([^"]*)"'` captures 2 parameters

### ✓ Pages & Named Navigation
- **Location**: `/Users/ptrk/Agantis/sliples/backend/app/models/page.py`
- **Status**: FULLY IMPLEMENTED with environment-specific overrides
- **Flow**: Scenario → Step matches page name → Resolves to path → Appends to base_url

### ✓ Custom Step Execution
- **Location**: `/Users/ptrk/Agantis/sliples/backend/app/services/test_executor.py`
- **Status**: FULLY IMPLEMENTED with isolated Python execution
- **Flow**: Pattern match → Capture parameters → Create isolated async function → exec()

### ✓ Project-scoped Resources
- **Scenarios**: scoped to project
- **Custom Steps**: scoped to project
- **Environments**: scoped to project
- **Pages**: scoped to project

---

## KEY FILES SUMMARY TABLE

| Purpose | File Path | Lines |
|---------|-----------|-------|
| Environment Model | `backend/app/models/environment.py` | 48 |
| Scenario Model | `backend/app/models/scenario.py` | 49 |
| Custom Step Model | `backend/app/models/custom_step.py` | 30 |
| Test Run Model | `backend/app/models/test_run.py` | 79 |
| Page Model | `backend/app/models/page.py` | 80 |
| Parser Routes | `backend/app/api/routes/parser.py` | 260 |
| Environment Routes | `backend/app/api/routes/environments.py` | 392 |
| Custom Steps Routes | `backend/app/api/routes/steps.py` | 198 |
| Test Run Routes | `backend/app/api/routes/runs.py` | 400+ |
| Test Session Routes | `backend/app/api/routes/test_session.py` | 300+ |
| Test Executor | `backend/app/services/test_executor.py` | 968 |
| Interactive Executor | `backend/app/services/interactive_executor.py` | 300+ |
| Celery Tasks | `backend/app/workers/tasks.py` | 250+ |
| Environment Frontend Type | `frontend/src/api/client.ts` | 20 (lines) |
| Environment Form | `frontend/src/components/EnvironmentForm.tsx` | 305 |
| KeyValue Editor | `frontend/src/components/KeyValueEditor.tsx` | 168 |
| Environments Page | `frontend/src/pages/Environments.tsx` | 354 |
| Environments Store | `frontend/src/store/environments.ts` | 126 |

---

## ARCHITECTURE DIAGRAM

```
┌─ Frontend (React) ─────────────────────────────────────────┐
│  Pages.Environments                                         │
│    ├─ Display environments with variable count            │
│    ├─ EnvironmentForm (create/edit)                       │
│    │    └─ KeyValueEditor (manage variables)              │
│    └─ Store: useEnvironmentsStore (Zustand)               │
│         └─ API calls: createEnvironment, updateEnvironment│
└─────────────────────────────────────────────────────────────┘
                         ↓ HTTP
┌─ Backend API (FastAPI) ────────────────────────────────────┐
│                                                              │
│  /api/v1/environments                                       │
│    ├─ GET  → List with variables                           │
│    ├─ POST → Create with variables dict                    │
│    ├─ PUT  → Update variables                              │
│    └─ GET /{id} → Fetch environment                        │
│                                                              │
│  /api/v1/runs                                               │
│    ├─ GET  → List test runs                                │
│    └─ POST → Create & trigger run → Celery task           │
│                                                              │
│  /api/v1/parser/validate                                    │
│    └─ POST → Validate Gherkin steps                        │
│                                                              │
│  /api/v1/steps                                              │
│    ├─ GET  → List custom steps                             │
│    ├─ POST → Create custom step                            │
│    ├─ PUT  → Update custom step                            │
│    └─ DELETE → Delete custom step                          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─ Database (PostgreSQL) ────────────────────────────────────┐
│                                                              │
│ environments                                                 │
│   ├─ id UUID PK                                             │
│   ├─ name varchar                                           │
│   ├─ base_url varchar                                       │
│   ├─ locale varchar                                         │
│   ├─ timezone_id varchar                                    │
│   ├─ variables JSON ← KEY FIELD                             │
│   └─ retention_days int                                     │
│                                                              │
│ scenarios                                                    │
│   ├─ id UUID PK                                             │
│   ├─ name varchar                                           │
│   ├─ feature_path varchar                                   │
│   ├─ content text                                           │
│   └─ tags ARRAY                                             │
│                                                              │
│ custom_steps                                                │
│   ├─ id UUID PK                                             │
│   ├─ pattern varchar                                        │
│   └─ code text                                              │
│                                                              │
│ test_runs                                                    │
│   ├─ id UUID PK                                             │
│   ├─ environment_id FK                                      │
│   ├─ scenario_ids ARRAY(UUID)                              │
│   ├─ status enum                                            │
│   └─ browser varchar                                        │
│                                                              │
│ pages                                                        │
│   ├─ id UUID PK                                             │
│   ├─ name varchar                                           │
│   └─ path varchar                                           │
│                                                              │
│ page_environment_overrides                                  │
│   ├─ page_id FK                                             │
│   ├─ environment_id FK                                      │
│   └─ path varchar                                           │
└─────────────────────────────────────────────────────────────┘
                    ↓ (Celery Task)
┌─ Test Executor ────────────────────────────────────────────┐
│                                                              │
│ execute_test_run(run_id)                                    │
│   ├─ Load TestRun                                           │
│   ├─ Load Environment (with variables JSON)                 │
│   ├─ Load Scenarios                                         │
│   ├─ Load Custom Steps                                      │
│   ├─ Load Pages                                             │
│   │                                                         │
│   └─ run_test_execution(                                    │
│        scenarios, base_url, locale, timezone_id,            │
│        custom_steps, pages                                  │
│        [⚠️ variables NOT passed]                             │
│      )                                                      │
│       ├─ Create Playwright browser                          │
│       ├─ Create context(locale, timezone_id)               │
│       ├─ For each scenario:                                 │
│       │   ├─ Parse Gherkin steps                            │
│       │   └─ For each step:                                 │
│       │       ├─ Find handler (custom or builtin)           │
│       │       ├─ Extract captured params                    │
│       │       ├─ Execute handler(page, params)              │
│       │       └─ Capture screenshot/result                  │
│       │                                                     │
│       └─ Return TestExecutionResult                         │
│                                                             │
│   └─ Store results in test_results table                    │
└─────────────────────────────────────────────────────────────┘
```

---

## NEXT STEPS FOR VARIABLES INTEGRATION

To fully leverage environment variables in test execution:

1. **Pass variables to executor**
   - Modify `execute_test_run()` to pass `environment.variables`
   - Pass to `run_test_execution()` function

2. **Make available to custom steps**
   - Inject variables into custom step execution context
   - Available as `__env_variables__` dict in custom code

3. **Allow builtin steps to use variables**
   - Support `$VAR_NAME` syntax in step parameters
   - Substitute before execution

4. **Document variable usage**
   - Add help text about using variables in steps
   - Show examples in custom step editor

5. **Add variable validation**
   - Warn when scenario uses undefined variables
   - Validate variable syntax in parser

