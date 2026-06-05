# Sliples Project Documentation Index

## Quick Start

Welcome! You've just explored the **Sliples** project's authentication system and recording API. Here's where to find everything:

---

## 📚 Documentation Files

### 1. **SLIPLES_AUTH_RECORDER_GUIDE.md** (Comprehensive Reference)
   - **Complete** authentication system breakdown
   - All auth endpoints with signatures
   - Token & session models
   - Recording sessions API (all GET/POST/PATCH/DELETE endpoints)
   - RecordedEvent model with all 25+ fields
   - Frontend auth flow (React + Zustand)
   - Security & token validation logic
   - **Best for:** Understanding architecture and complete endpoint reference

### 2. **SLIPLES_API_EXAMPLES.md** (Practical Usage)
   - 19 curl examples covering:
     - OAuth2 login flow
     - Token management
     - API key creation & management
     - Recording sessions (list, create, record events)
     - Session export for AI/LLM
     - Error responses
   - **Best for:** Testing endpoints and CI/CD integration

### 3. **SLIPLES_DOCUMENTATION_INDEX.md** (This File)
   - Navigation guide for all docs
   - Quick reference table
   - Key findings summary
   - **Best for:** Finding what you need quickly

---

## 🗂️ Project Structure

```
sliples/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   │   ├── auth.py                 ← Google OAuth2, JWT, API keys
│   │   │   └── recorder.py             ← Recording sessions & events
│   │   ├── models/
│   │   │   ├── user.py                 ← User (UUID, email, role, etc.)
│   │   │   ├── api_key.py              ← API Key (bcrypt hashed)
│   │   │   └── recording.py            ← RecordingSession, RecordedEvent
│   │   ├── core/
│   │   │   └── security.py             ← JWT validation & token creation
│   │   └── services/
│   │       └── google_auth.py          ← OAuth2 helpers
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── store/
│   │   │   └── auth.ts                 ← Zustand store (persist to localStorage)
│   │   ├── api/
│   │   │   ├── auth.ts                 ← Auth API calls
│   │   │   └── client.ts               ← Axios config (withCredentials)
│   │   └── pages/
│   │       └── Login.tsx               ← Login UI
│   └── ...
│
├── SLIPLES_AUTH_RECORDER_GUIDE.md      ← Full reference (THIS SESSION)
├── SLIPLES_API_EXAMPLES.md             ← Curl examples (THIS SESSION)
├── SLIPLES_DOCUMENTATION_INDEX.md      ← This file
└── ...existing docs/
    ├── CODEBASE_ANALYSIS.md
    ├── CODEBASE_FINDINGS.txt
    └── EXPLORATION_SUMMARY.md
```

---

## 🔑 Key Findings Summary

### Authentication
| Item | Details |
|------|---------|
| **Auth Method** | Google Workspace SSO (OAuth2) |
| **Token Type** | JWT (HS256, stateless) |
| **Token Storage** | httpOnly cookie `access_token` + Bearer header support |
| **Token Expiry** | Configurable: `JWT_EXPIRY_HOURS` env var |
| **No Session Table** | Entirely stateless (JWT-based) |
| **First User** | Becomes admin automatically |

### Recording Sessions
| Item | Details |
|------|---------|
| **Models** | RecordingSession + RecordedEvent |
| **Key Fields** | 25+ fields across two models |
| **Selector Strategies** | 5 types: CSS, XPath, text, test-id, aria-label |
| **Event Types** | 9 types: click, input, select, navigation, submit, focus, blur, scroll, keydown |
| **Auth Methods** | Domain-based (Origin header) + API key |
| **Export Format** | Compact JSON optimized for LLMs |

### API Endpoints
| Category | Count | Examples |
|----------|-------|----------|
| **Auth** | 8 | login, callback, me, token, logout, keys (CRUD) |
| **Recording** | 9 GET | List sessions, get session, get events, export |
| **Recording** | 6 POST/PATCH/DELETE | Start, record events, stop, rename, annotate, delete |
| **Domain Mgmt** | 4 | List, add, update, delete allowed domains |

---

## 💡 Top 5 Most Important Files

1. **backend/app/api/routes/auth.py** (470 lines)
   - All OAuth2, JWT, and API key logic
   - Token creation and validation

2. **backend/app/core/security.py** (215 lines)
   - JWT verification function
   - Token extraction (cookie vs header)
   - Dependency injectors for auth levels

3. **backend/app/api/routes/recorder.py** (750+ lines)
   - All recording session endpoints
   - Event batch recording
   - Session export

4. **frontend/src/store/auth.ts** (127 lines)
   - Zustand state management
   - Persistence to localStorage

5. **frontend/src/pages/Login.tsx** (111 lines)
   - OAuth2 flow trigger
   - Error handling

---

## 🚀 Common Tasks

### I want to...

**...understand how authentication works**
→ Read: `SLIPLES_AUTH_RECORDER_GUIDE.md` § 1 (Authentication System)

**...test an API endpoint manually**
→ See: `SLIPLES_API_EXAMPLES.md` (19 curl examples)

**...find the User model definition**
→ Look: `backend/app/models/user.py` (41 lines)

**...see all recording endpoints**
→ Search: `SLIPLES_AUTH_RECORDER_GUIDE.md` § 2.1

**...understand token validation flow**
→ Read: `SLIPLES_AUTH_RECORDER_GUIDE.md` § 4.1

**...add a new auth endpoint**
→ Edit: `backend/app/api/routes/auth.py`

**...add a new recording endpoint**
→ Edit: `backend/app/api/routes/recorder.py`

**...understand event structure**
→ Read: `SLIPLES_AUTH_RECORDER_GUIDE.md` § 2.2 (RecordedEvent model)

**...test recording API from CI/CD**
→ See: `SLIPLES_API_EXAMPLES.md` § "Using API Keys (CI/CD)"

**...debug authentication issues**
→ Check: `backend/app/core/security.py` (token extraction & verification)

---

## 🔍 Quick Reference Tables

### Auth Endpoints
```
GET  /auth/google/login         → Start OAuth2 flow
GET  /auth/google/callback      → Handle OAuth2 callback
GET  /auth/me                   → Current user info
GET  /auth/token                → Refresh/get JWT
POST /auth/logout               → Clear cookie
POST /auth/keys                 → Create API key
GET  /auth/keys                 → List API keys
DEL  /auth/keys/{id}            → Revoke API key
```

### Recording Endpoints
```
GET  /recorder/sessions                      → List all
GET  /recorder/sessions/{id}                 → Get one
GET  /recorder/sessions/{id}/events          → Get events
POST /recorder/sessions                      → Start
POST /recorder/sessions/{id}/events          → Record events
POST /recorder/sessions/{id}/stop            → Stop
PATCH /recorder/sessions/{id}                → Rename
PATCH /recorder/sessions/{id}/events/{eid}   → Annotate event
DEL  /recorder/sessions/{id}                 → Delete
POST /recorder/sessions/export               → Export (AI format)
```

### User Model Fields
```
id               UUID (PK)
email            str (unique, indexed)
name             str
picture_url      str | None
google_id        str (unique, from Google OAuth)
workspace_domain str
is_active        bool
role             enum(admin, user)
created_at       datetime
last_login       datetime | None
```

### RecordedEvent Fields (25+)
```
Core:         id, session_id, sequence, timestamp, event_type
Selectors:    selector_css, selector_xpath, selector_text,
              selector_test_id, selector_aria
Metadata:     tag_name, element_id, element_classes, element_name,
              element_type, element_role, label_text, placeholder
Data:         value, url, coordinates, key_info, extra_data
Annotations:  step_label, should_screenshot, parameters, notes
```

---

## ✅ No MCP/Integration Files Found

The project does **not** currently have:
- `.claude/` directory
- `.mcp` configuration files
- Claude-specific integration files

**Implication:** You can create these if needed for Claude Code integration.

---

## 📖 Reading Path (Recommended Order)

1. **First:** This file (SLIPLES_DOCUMENTATION_INDEX.md)
   - ~5 min read
   - Understand structure

2. **Then:** SLIPLES_AUTH_RECORDER_GUIDE.md § 1-2 (Auth + Recording endpoints)
   - ~15 min read
   - Know what's available

3. **Deep Dive:** SLIPLES_AUTH_RECORDER_GUIDE.md § 3-4 (Frontend + Security)
   - ~10 min read
   - Understand auth flow

4. **Practical:** SLIPLES_API_EXAMPLES.md
   - Reference as needed
   - Copy/paste curl commands

5. **Source:** Visit actual files for:
   - auth.py (endpoints)
   - security.py (token logic)
   - recorder.py (recording logic)

---

## 🎯 Exploration Summary

✅ **Auth System:** Google Workspace SSO (OAuth2) → JWT (stateless) → httpOnly cookie
✅ **Recording API:** 3 GET endpoints (list, details, events) + 6 mutation endpoints
✅ **Frontend:** React + Axios + Zustand (persist auth state)
✅ **Models:** User (email, role), RecordingSession (metadata), RecordedEvent (25+ fields)
✅ **Security:** JWT HS256, token extraction (cookie priority), active user check
✅ **No MCP Files:** Project ready for Claude integration if desired

---

**Created:** 2026-05-27  
**Session:** Sliples Auth & Recording API Exploration  
**Files Analyzed:** 20+ backend/frontend files  
**Endpoints Documented:** 17 total (auth + recording)  
**Models Mapped:** 3 (User, RecordingSession, RecordedEvent)  

For detailed implementation, refer to the comprehensive guide and examples files.
