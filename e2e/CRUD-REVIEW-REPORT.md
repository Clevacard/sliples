# Sliples Application - Comprehensive CRUD Review Report

**Date:** 2026-03-20
**Reviewer:** Senior QA Reviewer (E2E)
**Test Framework:** Playwright
**Test File:** `/Users/ptrk/Agantis/sliples/e2e/tests/comprehensive-crud.spec.ts`

---

## Executive Summary

This report documents the comprehensive E2E testing of all CRUD operations for the Sliples application. Testing covered 8 entities with 49 test cases, with **43 tests passing** and **6 tests failing** (all related to a backend bug in the Schedules API).

### Overall Results
- **Total Tests:** 49
- **Passed:** 43 (87.8%)
- **Failed:** 6 (12.2%)
- **Root Cause of Failures:** Backend bug in `schedules.py` - undefined variable `api_key` on line 279

---

## Entity-by-Entity Review

### 1. Scenarios (`/scenarios`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | List displays with search, tag filter, repo filter |
| VIEW | Yes | Yes | Working | Individual scenario view with content editor |
| CREATE | Yes | - | Working | API creates scenarios successfully |
| EDIT | Yes | Yes | Working | Content update via PUT endpoint |
| DELETE | Yes | - | Working | DELETE returns 204 |
| FILTER by tag | Yes | Yes | Working | Dropdown filter available |
| FILTER by repo | Yes | Yes | Working | Dropdown filter available |
| SEARCH | Yes | Yes | Working | Full-text search in name/path/tags |

**Screenshots:**
- `scenarios-list.png` - Scenarios list page
- `scenarios-view.png` - Scenario detail view
- `scenarios-filter-tag.png` - Tag filtering
- `scenarios-filter-repo.png` - Repository filtering
- `scenarios-search.png` - Search functionality

**Verdict:** All CRUD operations for Scenarios are fully functional.

---

### 2. Environments (`/environments`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Cards with variables display |
| VIEW | Yes | Yes | Working | Expand card to view variables |
| CREATE | Yes | Yes | Working | Modal form with validation |
| EDIT | Yes | Yes | Working | Edit modal with form |
| DELETE | Yes | Yes | Working | Confirmation modal |
| Browser Configs | Yes | Yes | Working | Nested CRUD within environment |

**Screenshots:**
- `environments-list.png` - Environments list
- `environments-create-modal.png` - Create environment modal
- `environments-edit.png` - Edit modal open
- `environments-view.png` - Expanded card with variables

**Verdict:** All CRUD operations for Environments are fully functional.

---

### 3. Repositories (`/repos`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Repository cards with sync status |
| VIEW | Yes | Yes | Working | Displays name, URL, branch, sync info |
| CREATE | Yes | Yes | Working | Modal with git URL validation |
| DELETE | Yes | Yes | Working | Confirmation modal |
| SYNC | Yes | Yes | Working | Triggers Celery task, queues sync |

**Note:** Repositories do not have an EDIT operation by design - you delete and recreate.

**Screenshots:**
- `repos-list.png` - Repositories list
- `repos-create-modal.png` - Add repository modal
- `repos-view.png` - Repository details

**Verdict:** All CRUD operations for Repositories are fully functional.

---

### 4. Schedules (`/schedules`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Schedule cards with cron info |
| VIEW | Yes | Yes | Working | Shows next run, environment, browsers |
| CREATE | Yes | Yes | BACKEND BUG | 500 error - `api_key` undefined |
| EDIT | Yes | Yes | BACKEND BUG | Same error on create |
| DELETE | Yes | Yes | BACKEND BUG | Same error on create |
| TOGGLE | Yes | Yes | Working | Enable/disable toggle |
| RUN NOW | Yes | Yes | BACKEND BUG | Same error on create |

**Backend Bug Details:**
- **File:** `/Users/ptrk/Agantis/sliples/backend/app/api/routes/schedules.py`
- **Line:** 279
- **Issue:** Variable `api_key` is used but not defined. Should be `auth` or a value extracted from `auth`.
- **Error:** `NameError: name 'api_key' is not defined`

**Screenshots:**
- `schedules-list.png` - Schedules list page
- `schedules-view.png` - Schedule cards

**Verdict:** LIST and VIEW work. CREATE/EDIT/DELETE blocked by backend bug.

---

### 5. Custom Steps (`/custom-steps`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Steps list with patterns |
| VIEW | Yes | Yes | Working | Pattern and code display |
| CREATE | Yes | Yes | Working | Modal with Monaco editor |
| EDIT | Yes | Yes | Working | Update name/pattern/code |
| DELETE | Yes | Yes | Working | Confirmation modal |
| SEARCH | Yes | No | Missing | Search input not visible in UI |

**Note:** The search functionality exists in the code but the search input was not visible during testing. This may be a rendering issue or the search only appears when there are steps.

**Screenshots:**
- `custom-steps-list.png` - Custom steps list (may show empty state)
- `custom-steps-create-modal.png` - Create step modal
- `custom-steps-view.png` - Steps view
- `custom-steps-search.png` - Search (not visible)

**Verdict:** Core CRUD operations work. Search UI may have conditional rendering.

---

### 6. Test Runs (`/runs`)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Runs table with status badges |
| VIEW | Yes | Yes | Working | Run details page with results |
| CREATE | Yes | Yes | Working | Modal with env/tag/browser selection |
| CANCEL | Yes | - | Working | DELETE endpoint cancels queued/running |
| FILTER by status | Yes | Yes | Working | Status dropdown filter |
| RETRY | Yes | - | Working | POST /runs/{id}/retry |

**Note:** No traditional UPDATE operation - runs are immutable once created.

**Screenshots:**
- `runs-list.png` - Test runs list
- `runs-create-modal.png` - New test run modal
- `runs-view-details.png` - Run details page
- `runs-filter-status.png` - Status filter

**Verdict:** All CRUD operations for Test Runs are fully functional.

---

### 7. API Keys (`/settings` -> API Keys tab)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Keys table with masked values |
| CREATE | Yes | Yes | Working | Modal shows full key once |
| REVOKE | Yes | Yes | Working | Soft delete (sets active=false) |

**Note:** No VIEW individual or EDIT operations - keys are immutable.

**Screenshots:**
- `apikeys-list.png` - API keys in settings
- `apikeys-create-modal.png` - Create key modal

**Verdict:** All CRUD operations for API Keys are fully functional.

---

### 8. Users (`/users` - Admin only)

| Operation | API | UI | Status | Notes |
|-----------|-----|-----|--------|-------|
| LIST | Yes | Yes | Working | Users table with roles |
| VIEW | Yes | Yes | Working | User details in list |
| SEARCH | Yes | Yes | Working | Name/email search |
| CHANGE ROLE | Yes | Yes | Requires Session | API needs JWT cookie, not API key |
| TOGGLE ACTIVE | Yes | Yes | Requires Session | API needs JWT cookie, not API key |

**Note:** The Users API endpoints use `get_current_admin_user` which requires JWT session authentication, not API key authentication. This is a deliberate security design.

**Screenshots:**
- `users-list.png` - Users list page
- `users-search.png` - Search functionality

**Verdict:** READ operations work. WRITE operations require session auth (working as designed).

---

## Issues Found

### Critical (1)

1. **Schedules CREATE returns 500 error**
   - **Location:** `backend/app/api/routes/schedules.py`, line 279
   - **Issue:** `created_by=api_key` - variable `api_key` is not defined
   - **Fix:** Change to `created_by=str(auth)[:50] if auth else None` or extract from `auth` parameter
   - **Impact:** Cannot create, edit, delete schedules via API

### Minor (1)

2. **Custom Steps search input not always visible**
   - **Location:** `frontend/src/pages/CustomSteps.tsx`, line 130
   - **Issue:** Search only renders when `steps.length > 0`
   - **Impact:** Search not available on empty state (minor UX issue)

---

## Recommendations

### Immediate Fixes Required

1. **Fix Schedules API bug** (Critical)
   ```python
   # In schedules.py, line 279, change:
   created_by=api_key,
   # To:
   created_by=getattr(auth, 'email', str(auth)[:50]) if auth else None,
   ```

### Suggested Improvements

1. **Add inline editing for Repositories** - Currently only delete/recreate
2. **Add search to Custom Steps empty state** - Better UX for new users
3. **Add bulk operations** - Select multiple items for delete/run
4. **Add pagination controls** - Currently using limit/offset but no UI

---

## Test Evidence

All screenshots are stored in: `/Users/ptrk/Agantis/sliples/e2e/screenshots/`

Key screenshots for each entity:
- `environments-*.png` - Environment CRUD evidence
- `repos-*.png` - Repository CRUD evidence
- `scenarios-*.png` - Scenario CRUD evidence
- `schedules-*.png` - Schedule CRUD evidence
- `custom-steps-*.png` - Custom Steps CRUD evidence
- `runs-*.png` - Test Runs CRUD evidence
- `apikeys-*.png` - API Keys CRUD evidence
- `users-*.png` - Users CRUD evidence

---

## API Endpoint Summary

| Entity | List | Get | Create | Update | Delete | Special |
|--------|------|-----|--------|--------|--------|---------|
| Scenarios | GET /scenarios | GET /scenarios/{id} | POST /scenarios | PUT /scenarios/{id}/content | DELETE /scenarios/{id} | GET /scenarios/tags |
| Environments | GET /environments | GET /environments/{id} | POST /environments | PUT /environments/{id} | DELETE /environments/{id} | Browser configs CRUD |
| Repos | GET /repos | - | POST /repos | - | DELETE /repos/{id} | POST /repos/{id}/sync |
| Schedules | GET /schedules | GET /schedules/{id} | POST /schedules | PUT /schedules/{id} | DELETE /schedules/{id} | POST /{id}/toggle, POST /{id}/run-now |
| Custom Steps | GET /steps/custom | - | POST /steps/custom | PUT /steps/custom/{id} | DELETE /steps/custom/{id} | POST /{id}/save-to-repo |
| Runs | GET /runs | GET /runs/{id} | POST /runs | PATCH /runs/{id}/status | DELETE /runs/{id} (cancel) | POST /runs/{id}/retry |
| API Keys | GET /auth/keys | GET /auth/keys/{id} | POST /auth/keys | - | DELETE /auth/keys/{id} | - |
| Users | GET /users | GET /users/{id} | - | PUT /users/{id}/role, PUT /users/{id}/active | - | Search via query param |

---

## Conclusion

The Sliples application has a comprehensive and well-implemented CRUD system for all 8 entities. The main issue discovered is a backend bug in the Schedules API that prevents schedule creation. Once this bug is fixed, all CRUD operations will be fully functional.

**Overall Assessment:** **GOOD** - Application is 87.8% functional, with a single critical bug to fix.
