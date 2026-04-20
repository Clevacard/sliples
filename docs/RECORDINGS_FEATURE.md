# Recording Sessions UI Feature

## Overview

The Recordings feature allows QA teams to review, annotate, and prepare UI event recordings for conversion to automated test scenarios. Users can:
- Browse and filter recorded sessions by name, URL, status, and date
- View detailed event sequences with element selectors and metadata
- Add human-readable labels to steps
- Mark steps for screenshots during playback
- Extract values into parametrized variables
- Add notes and context to individual steps

## Architecture

### Backend

**Models** (`backend/app/models/recording.py`):
- `RecordingSession` - Top-level container for a recording
- `RecordedEvent` - Individual UI event with user annotations

**New Fields on RecordedEvent**:
- `step_label` (Text) - User-defined label for the step
- `should_screenshot` (Boolean) - Mark this step for screenshot capture
- `parameters` (JSON) - Extracted parameters: `{"email": "USER_EMAIL"}`
- `notes` (Text) - Additional context about this step

**API Endpoints** (`backend/app/api/routes/recorder.py`):

Existing endpoints:
- `GET /recorder/sessions` - List all recording sessions
- `GET /recorder/sessions/{id}` - Get session details
- `GET /recorder/sessions/{id}/events` - Get all events for a session
- `DELETE /recorder/sessions/{id}` - Delete a session
- `POST /recorder/sessions` - Start recording (from snippet)
- `POST /recorder/sessions/{id}/events` - Submit event batch (from snippet)

New endpoint:
- `PATCH /recorder/sessions/{session_id}/events/{event_id}` - Update event annotations

**Database Migration** (`backend/alembic/versions/013_add_event_annotations.py`):
- Adds `step_label`, `should_screenshot`, `parameters`, `notes` columns to `recorded_events` table

### Frontend

**Store** (`frontend/src/store/recordings.ts`):
- Zustand store for recordings state management
- Methods: `fetchSessions()`, `fetchSessionDetails()`, `updateEvent()`, `deleteSession()`

**Pages**:
- `Recordings.tsx` - List page with filtering and deletion
- `RecordingDetails.tsx` - Detail page with expandable event viewer
- `EditEventModal.tsx` - Modal for editing event annotations

**API Client** (`frontend/src/api/client.ts`):
- TypeScript interfaces for `RecordingSession`, `RecordedEvent`, `EventMetadataUpdate`
- Functions: `getRecordingSessions()`, `getRecordingSession()`, `getRecordingEvents()`, `updateEventMetadata()`, `deleteRecordingSession()`

**Routes** (`frontend/src/App.tsx`):
- `/recordings` - List page
- `/recordings/:id` - Detail page

**Navigation** (`frontend/src/components/Layout.tsx`):
- Added "Recordings" menu item with "Interactive" badge

## Usage

### Viewing Recordings

1. Navigate to **Recordings** in the main navigation menu
2. Use filters to find sessions:
   - **Search** - Filter by name or URL
   - **Status** - Filter by recording/stopped/converted
3. Click **View** to see detailed events

### Annotating Steps

1. In the Recording Details page, click **Edit Annotations** on any step
2. Fill in:
   - **Step Label** - Human-readable name (e.g., "Enter email", "Click submit")
   - **Mark for screenshot** - Check to capture screenshot at this step
   - **Parameters** - Extract values into variables
     - Example: parameter `email` with variable `USER_EMAIL` becomes `${USER_EMAIL}`
   - **Notes** - Additional context
3. Click **Save Changes**

### Extracting Parameters

Use the Parameters section to parametrize hardcoded values:
- **Parameter**: The name of the extracted value (e.g., "username")
- **Variable**: The variable name to use in scenarios (e.g., "TEST_USER")
- Result: Value gets replaced with `${TEST_USER}` during replay

Example:
```
Parameter: email
Variable: QA_EMAIL
Result: user@example.com → ${QA_EMAIL}
```

## Data Flow

### Recording Phase
1. Snippet loaded on test website
2. User interacts with UI
3. Snippet captures events (clicks, inputs, navigation)
4. Events batched and sent to `/recorder/sessions/{id}/events`
5. Backend stores in `recorded_events` table

### Review Phase
1. User navigates to **Recordings** page
2. Frontend calls `GET /recorder/sessions` to list
3. Clicks on recording → `GET /recorder/sessions/{id}` + `GET /recorder/sessions/{id}/events`
4. Events displayed in expandable list

### Annotation Phase
1. User clicks **Edit Annotations** on an event
2. Modal opens with event details and forms
3. User fills in labels, screenshot flag, parameters, notes
4. On save, `PATCH /recorder/sessions/{id}/events/{event_id}` updates backend
5. UI refreshes to reflect changes

### Playback Phase (Future)
- Recorded events converted to Gherkin steps
- Screenshot markers used to capture screenshots
- Parameters substituted from environment
- Events replayed using Playwright

## Selector Strategies

Each event records multiple selector strategies for resilient playback:

1. **CSS Selector** - `.button.primary#submit`
2. **XPath** - `//*[@id="form"]/button[1]`
3. **data-testid** - Recommended for maintainability
4. **aria-label** - Accessibility-based selection
5. **Text Content** - Text node matching

During playback, if one selector fails, the next is tried.

## File Structure

```
Backend:
- models/recording.py - RecordingSession and RecordedEvent models
- api/routes/recorder.py - Recording endpoints
- alembic/versions/013_add_event_annotations.py - Migration

Frontend:
- store/recordings.ts - Zustand store
- pages/Recordings.tsx - List page
- pages/RecordingDetails.tsx - Detail page
- components/EditEventModal.tsx - Edit modal
- api/client.ts - API functions
```

## Event Types Captured

- `click` - Mouse click with coordinates
- `input` - Form field text input (passwords masked)
- `change` - Select/radio/checkbox changes
- `submit` - Form submission
- `keydown` - Keyboard events (special keys + modifiers)
- `navigation` - URL change or page load

## Future Enhancements

1. **Convert to Scenario** - Transform recording to .feature file
2. **Screenshot Capture** - Automatically take screenshots at marked steps
3. **Scenario Templates** - Reuse common interaction patterns
4. **Playback Simulation** - Preview how recording will replay
5. **Diff Viewer** - Compare current website to recording time
6. **Bulk Operations** - Edit multiple steps at once

## Troubleshooting

### Recording Not Appearing
- Check that recording was stopped via `SliplesRecorder.stop()`
- Verify API key is valid
- Check browser console for [Sliples] error messages

### Element Not Found During Playback
- Add `data-testid` to important elements
- Add descriptive `aria-label` attributes
- Avoid dynamically generated element IDs
- Use stable CSS classes

### Parameter Not Working
- Ensure parameter name matches variable usage
- Verify environment variable is set during playback
- Check parameter syntax: `${VARIABLE_NAME}`

## API Reference

### Get Recordings
```bash
GET /api/v1/recorder/sessions
```
Returns array of `RecordingSession` objects.

### Get Recording Details
```bash
GET /api/v1/recorder/sessions/{session_id}
```
Returns single `RecordingSession`.

### Get Events
```bash
GET /api/v1/recorder/sessions/{session_id}/events
```
Returns array of `RecordedEvent` objects.

### Update Event
```bash
PATCH /api/v1/recorder/sessions/{session_id}/events/{event_id}
Content-Type: application/json

{
  "step_label": "Enter email",
  "should_screenshot": true,
  "parameters": {
    "email": "USER_EMAIL"
  },
  "notes": "Test with company email only"
}
```

### Delete Recording
```bash
DELETE /api/v1/recorder/sessions/{session_id}
```
Deletes session and all events.

## Performance Considerations

- Events are paginated in the detail view (optional future enhancement)
- Filtering happens client-side (fine for typical session size <1000 events)
- Database migration indexed on `(session_id, sequence)` for fast lookups
- Old recordings auto-deleted after 12 months (existing Celery beat job)

## Security Notes

- Recording API endpoints require `X-API-Key` header
- JWT cookies used for UI authentication
- Passwords in event values masked as `***`
- Session data stored in PostgreSQL
- No PII in serialized events (user responsible for sanitization)
