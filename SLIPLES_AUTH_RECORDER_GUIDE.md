# Sliples Project: Complete Auth & Recording API Exploration

**Date:** 2026-05-27  
**Project Location:** `/Users/ptrk/Agantis/sliples`

---

## 1. AUTHENTICATION SYSTEM

### 1.1 Auth Endpoints (Backend)
**File:** `/Users/ptrk/Agantis/sliples/backend/app/api/routes/auth.py`

#### Google OAuth2 Flow
- **`GET /auth/google/login`**
  - Initiates Google OAuth2 login
  - Params: `redirect` (bool, default=true) — redirects to Google or returns JSON
  - Response: `GoogleLoginResponse` with `authorization_url` and `state`
  - Redirects to Google OAuth consent screen

- **`GET /auth/google/callback`**
  - Handles OAuth callback from Google
  - Params: `code`, `state`, `error`, `error_description`
  - Flow:
    1. Exchanges auth code for Google tokens
    2. Fetches user info from Google
    3. Verifies workspace domain (if configured)
    4. Creates or updates User in DB
    5. Creates JWT token
    6. Sets httpOnly cookie `access_token` (SameSite=Lax)
    7. Redirects to frontend dashboard or error page
  - Cookies Set: `access_token` (expires in `jwt_expiry_hours`)

- **`GET /auth/me`**
  - Requires: JWT auth (cookie or Bearer header)
  - Response: `UserResponse` with user metadata
  ```json
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Full Name",
    "picture_url": "https://...",
    "workspace_domain": "example.com",
    "role": "admin" | "user",
    "is_active": true,
    "created_at": "ISO8601",
    "last_login": "ISO8601"
  }
  ```

- **`GET /auth/token`**
  - Requires: JWT auth
  - Response: `TokenResponse` — refreshed JWT
  ```json
  {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 86400
  }
  ```

- **`POST /auth/logout`**
  - Clears `access_token` cookie

#### API Key Management
- **`POST /auth/keys`** (Create)
  - Requires: JWT or API key
  - Body: `{ name: string, environment_ids?: UUID[], project_id?: UUID }`
  - Response: `ApiKeyCreatedResponse` with full key (only returned once!)
  ```json
  {
    "id": "uuid",
    "project_id": "uuid",
    "name": "my-key",
    "key": "a1b2c3d4e5f6...64chars",
    "key_prefix": "a1b2c3d4",
    "created_at": "ISO8601",
    "active": true
  }
  ```

- **`GET /auth/keys`**
  - Requires: JWT or API key
  - Response: List of `ApiKeyResponse` (masked)

- **`DELETE /auth/keys/{key_id}`**
  - Soft deletes (sets active=false)

### 1.2 Token & Session Model

**User Model** (`backend/app/models/user.py`)
```python
id: UUID (PK)
email: str (unique, indexed)
name: str
picture_url: str | None
google_id: str (unique, indexed) — Google OAuth sub claim
workspace_domain: str
is_active: bool (default=true)
role: enum(admin, user)
created_at: datetime
last_login: datetime | None
```

**JWT Token Payload** (`backend/app/core/security.py`)
```json
{
  "sub": "user_id_as_string",
  "email": "user@example.com",
  "exp": "timestamp_seconds",
  "iat": "timestamp_seconds"
}
```
- Algorithm: HS256 (configurable)
- Secret: `JWT_SECRET_KEY` (env var)
- Expiry: `JWT_EXPIRY_HOURS` (env var, default likely 24h)

**Token Validation Flow**
1. Extract from cookie `access_token` OR Bearer header
2. Verify signature with `JWT_SECRET_KEY`
3. Check expiry (`exp` claim)
4. Look up User by `sub` claim (user_id) in DB
5. Verify user is active
6. Return User object

### 1.3 Token Issuance & Storage

**Issuance:**
- Called after successful OAuth callback or token refresh
- Function: `create_access_token(user_id: UUID, email: str) -> TokenResponse`
- Expiry calculated: `datetime.utcnow() + timedelta(hours=jwt_expiry_hours)`

**Storage:**
- **httpOnly Cookie** (preferred for web): Set on OAuth callback response
  - Name: `access_token`
  - HttpOnly: true (not accessible from JS)
  - Secure: true if frontend_url starts with `https://`
  - SameSite: Lax
  - MaxAge: `jwt_expiry_hours * 3600` seconds
  - Path: `/`

- **No server session table** — stateless JWT

---

## 2. RECORDING SESSIONS API

### 2.1 Session Management Endpoints
**File:** `/Users/ptrk/Agantis/sliples/backend/app/api/routes/recorder.py`

#### GET Endpoints (List & Retrieve)

- **`GET /recorder/sessions`** ✓
  - Requires: JWT or API key
  - Params: Optional project filter via `verify_project_access`
  - Response: `list[RecordingSessionResponse]`
  ```json
  {
    "id": "uuid",
    "project_id": "uuid",
    "name": "Homepage Recording",
    "url": "https://example.com",
    "status": "recording" | "stopped" | "converted",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1920,
    "viewport_height": 1080,
    "domain": "example.com",
    "client_ip": "192.168.1.1",
    "created_at": "ISO8601",
    "stopped_at": "ISO8601 | null",
    "event_count": 42
  }
  ```
  - Order: By `created_at` DESC

- **`GET /recorder/sessions/{session_id}`** ✓
  - Requires: JWT or API key
  - Response: Single `RecordingSessionResponse`

- **`GET /recorder/sessions/{session_id}/events`** ✓
  - Requires: JWT or API key
  - Response: `list[RecordedEventResponse]` ordered by timestamp + sequence
  ```json
  {
    "id": "uuid",
    "sequence": 1,
    "timestamp": "ISO8601",
    "event_type": "click" | "input" | "select" | "navigation" | "submit" | "focus" | "blur" | "scroll" | "keydown",
    "selector_css": ".button-primary",
    "selector_xpath": "//button[@id='submit']",
    "selector_text": "Sign In",
    "selector_test_id": "submit-btn",
    "selector_aria": "Submit Form",
    "tag_name": "button",
    "element_id": "submit-btn",
    "label_text": "Sign In",
    "value": "form_input_value",
    "url": "https://example.com/login",
    "coordinates": { "x": 150, "y": 75 },
    "key_info": {
      "key": "Enter",
      "code": "Enter",
      "ctrl": false,
      "alt": false,
      "shift": false,
      "meta": false
    },
    "extra_data": { "custom": "metadata" },
    "step_label": "Click Submit Button",
    "should_screenshot": true,
    "parameters": { "field": "varName" },
    "notes": "User annotation"
  }
  ```

#### POST/PATCH/DELETE Endpoints

- **`POST /recorder/sessions`**
  - Requires: Domain-based auth OR API key (scoped to project)
  - Body: `RecordingStartRequest`
  ```json
  {
    "name": "Session Name",
    "url": "https://example.com",
    "user_agent": "Optional",
    "viewport_width": 1920,
    "viewport_height": 1080
  }
  ```
  - Response: `RecordingStartResponse`
  ```json
  {
    "session_id": "uuid",
    "name": "Session Name",
    "status": "recording"
  }
  ```

- **`POST /recorder/sessions/{session_id}/events`**
  - Requires: Domain-based auth OR API key
  - Body: `EventsBatchRequest`
  ```json
  {
    "events": [
      {
        "sequence": 1,
        "timestamp": "ISO8601",
        "event_type": "click",
        "selector_css": "...",
        "tag_name": "button",
        "coordinates": { "x": 100, "y": 50 },
        ...
      }
    ]
  }
  ```
  - Response: `{ "recorded": 5 }`

- **`POST /recorder/sessions/{session_id}/stop`**
  - Requires: Domain OR API key auth
  - Sets `status = "stopped"`, `stopped_at = datetime.utcnow()`
  - Response: `RecordingSessionResponse`

- **`PATCH /recorder/sessions/{session_id}`** (Rename)
  - Requires: JWT or API key
  - Body: `SessionRenameRequest`
  ```json
  { "name": "New Name" }
  ```
  - Response: `RecordingSessionResponse`

- **`PATCH /recorder/sessions/{session_id}/events/{event_id}`**
  - Requires: JWT or API key
  - Body: `EventMetadataUpdate`
  ```json
  {
    "step_label": "User-defined label",
    "should_screenshot": true,
    "parameters": { "field": "var" },
    "notes": "Annotation"
  }
  ```
  - Response: Updated `RecordedEventResponse`

- **`DELETE /recorder/sessions/{session_id}`**
  - Requires: JWT or API key
  - Cascades to all related events

#### Export Endpoint

- **`POST /recorder/sessions/export`** (AI-optimized format)
  - Requires: JWT or API key
  - Body: `SessionExportRequest`
  ```json
  { "session_ids": ["uuid1", "uuid2"] }
  ```
  - Response: Compact JSON for LLM consumption
  ```json
  {
    "format": "sliples-session-export-v1",
    "exported_at": "ISO8601",
    "session_count": 2,
    "sessions": [
      {
        "id": "uuid",
        "name": "Session Name",
        "url": "https://example.com",
        "domain": "example.com",
        "user_agent": "Mozilla/5.0...",
        "viewport": "1920x1080",
        "started": "ISO8601",
        "stopped": "ISO8601",
        "events": [
          {
            "seq": 1,
            "t": "ISO8601",
            "type": "click",
            "target": "[data-testid=button]",
            "pos": { "x": 100, "y": 50 },
            "value": "text",
            "key": {...}
          }
        ]
      }
    ]
  }
  ```

### 2.2 Recording Session Model
**File:** `backend/app/models/recording.py`

**RecordingSession**
```python
id: UUID (PK)
project_id: UUID (FK to projects.id) — nullable
name: str(255)
url: str — starting URL
status: enum(recording, stopped, converted)
user_agent: str | None
viewport_width: int | None
viewport_height: int | None
domain: str(255) | None — extracted from Origin header
client_ip: str(45) | None
created_at: datetime
stopped_at: datetime | None
```

**RecordedEvent**
```python
id: UUID (PK)
session_id: UUID (FK to recording_sessions.id)
sequence: int — order of events
timestamp: datetime
event_type: str(50)

# Selectors (multiple strategies for resilient playback)
selector_css: str | None
selector_xpath: str | None
selector_text: str | None
selector_test_id: str | None
selector_aria: str | None

# Element metadata
tag_name: str | None
element_id: str | None
element_classes: str | None — JSON array
element_name: str | None — form field name
element_type: str | None — input type
element_role: str | None — ARIA role
label_text: str | None
placeholder: str | None

# Event data
value: str | None
url: str | None — current page URL
coordinates: JSON | None — {x, y}
key_info: JSON | None

# User annotations (added during review)
step_label: str | None
should_screenshot: bool (default=false)
parameters: JSON | None — {"field": "varName"}
notes: str | None
```

---

## 3. FRONTEND AUTH FLOW

### 3.1 Auth Store (Zustand)
**File:** `frontend/src/store/auth.ts`

**State Interface:**
```typescript
interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: () => void
  handleCallback: (code: string) => Promise<void>
  logout: () => Promise<void>
  fetchCurrentUser: () => Promise<void>
  clearError: () => void
  setLoading: (loading: boolean) => void
}
```

**User Model:**
```typescript
interface User {
  id: string
  email: string
  name: string
  picture_url: string | null
  role: 'admin' | 'user' | 'viewer'
}
```

**Persistence:**
- Uses Zustand `persist` middleware
- Storage key: `sliples-auth`
- Persists: `user`, `isAuthenticated`
- Does NOT persist: `isLoading`, `error`

### 3.2 Auth API Client
**File:** `frontend/src/api/auth.ts`

```typescript
// Get Google OAuth URL
export function getGoogleAuthUrl(): string
  // Returns: `${API_URL}/api/v1/auth/google/login`

// Exchange code for session
export async function handleOAuthCallback(code: string): Promise<User>
  // POST /auth/google/callback with { code }

// Get current user
export async function getCurrentUser(): Promise<User>
  // GET /auth/me

// Logout
export async function logout(): Promise<void>
  // POST /auth/logout
```

### 3.3 Login Page Flow
**File:** `frontend/src/pages/Login.tsx`

1. **Page Load:**
   - Checks `isAuthenticated` from store
   - If authenticated & loaded → redirect to `/dashboard`
   - If not authenticated → show login UI

2. **User Clicks "Sign in with Google":**
   - Calls `useAuthStore().login()`
   - Redirects to `/api/v1/auth/google/login`
   - Google OAuth flow begins

3. **After Google Authorization:**
   - Google redirects to `/api/v1/auth/google/callback?code=...&state=...`
   - Backend creates JWT, sets httpOnly cookie, redirects to `/`
   - Frontend automatically sent to dashboard (no code parameter needed)

### 3.4 API Client Configuration
**File:** `frontend/src/api/client.ts`

```typescript
export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true  // Include cookies (httpOnly auth token)
})

// Adds project context header
api.interceptors.request.use((config) => {
  const currentProjectId = localStorage.getItem('sliples_current_project_id')
  if (currentProjectId) {
    config.headers['X-Project-Id'] = currentProjectId
  }
  return config
})

// Extracts error messages from backend
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      error.message = error.response.data.detail
    }
    return Promise.reject(error)
  }
)
```

**Key Points:**
- `withCredentials: true` → sends httpOnly cookies automatically
- API key auth is NOT used in web UI (only for CI/CD via curl/scripts)
- Project context passed via `X-Project-Id` header

---

## 4. SECURITY & TOKEN VALIDATION

### 4.1 Security Module
**File:** `backend/app/core/security.py`

**Token Verification:**
```python
def verify_access_token(token: str) -> Optional[TokenData]:
  # JWT decode with HS256
  # Validates: signature, expiry, required claims (sub, email)
  # Returns TokenData or None if invalid
```

**Request Token Extraction:**
```python
def get_token_from_request(request: Request) -> Optional[str]:
  # Priority:
  # 1. Cookie: request.cookies.get("access_token")
  # 2. Header: Authorization: Bearer <token>
```

**Dependency Injectors:**
```python
async def get_current_user(request, db) -> User:
  # Validates token, returns User or 401

async def get_current_active_user(current_user) -> User:
  # Checks is_active, returns User or 403

async def get_current_admin_user(current_user) -> User:
  # Checks role == admin, returns User or 403
```

### 4.2 Authorization Levels

1. **`Depends(get_current_user)`** — Any authenticated user
2. **`Depends(get_current_active_user)`** — Authenticated + active user
3. **`Depends(get_current_admin_user)`** — Admin user only
4. **`Depends(get_api_key)`** — API key (for backend/CI)
5. **`Depends(get_api_key_or_user)`** — Either JWT or API key
6. **`Depends(verify_project_access)`** — Scoped to project + has access

---

## 5. PROJECT STRUCTURE & MCP FILES

**No MCP or Claude integration files found** in:
- `./.claude/` (does not exist)
- Project root
- Backend/frontend directories

**Existing Documentation:**
- `/CODEBASE_ANALYSIS.md` (32KB)
- `/CODEBASE_FINDINGS.txt` (27KB)
- `/EXPLORATION_SUMMARY.md` (7KB)
- `/README_CODEBASE_DOCS.md` (8KB)

---

## 6. SUMMARY TABLE

| Aspect | Details |
|--------|---------|
| **Auth Type** | Google Workspace SSO (OAuth2) |
| **Token Type** | JWT (HS256) |
| **Token Storage** | httpOnly cookie + optional Bearer header |
| **Token Expiry** | Configurable (env: `JWT_EXPIRY_HOURS`) |
| **Session Storage** | Stateless (JWT) — no server session table |
| **Login Endpoint** | `GET /auth/google/login` |
| **Callback Endpoint** | `GET /auth/google/callback` |
| **Current User Endpoint** | `GET /auth/me` |
| **Logout Endpoint** | `POST /auth/logout` |
| **Recording Sessions List** | `GET /recorder/sessions` |
| **Session Details** | `GET /recorder/sessions/{session_id}` |
| **Session Events** | `GET /recorder/sessions/{session_id}/events` |
| **Start Recording** | `POST /recorder/sessions` |
| **Record Events Batch** | `POST /recorder/sessions/{session_id}/events` |
| **Stop Recording** | `POST /recorder/sessions/{session_id}/stop` |
| **Export Sessions** | `POST /recorder/sessions/export` |

---

## 7. KEY FILE PATHS

**Backend:**
- Auth routes: `backend/app/api/routes/auth.py`
- Recording routes: `backend/app/api/routes/recorder.py`
- Security/JWT: `backend/app/core/security.py`
- Models (User): `backend/app/models/user.py`
- Models (Recording): `backend/app/models/recording.py`
- Models (API Key): `backend/app/models/api_key.py`
- Google OAuth service: `backend/app/services/google_auth.py`

**Frontend:**
- Auth store: `frontend/src/store/auth.ts`
- Auth API: `frontend/src/api/auth.ts`
- API client: `frontend/src/api/client.ts`
- Login page: `frontend/src/pages/Login.tsx`

---

**Exploration Complete.** All endpoints, models, and auth flows documented with response shapes and required parameters.
