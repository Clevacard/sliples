# Start Recording UI Feature

## Overview

Added a "Start Recording" button and modal to the Recordings page that allows users to:
1. Generate project-scoped API keys
2. Create a new recording session with name and URL
3. Retrieve the JavaScript snippet code to embed in their website
4. View the session ID for reference

## Components Added

### `StartRecordingModal.tsx`
A three-step modal that guides users through the recording setup process:

**Step 1: Generate API Key**
- Input field for API key name
- Button to generate a new project-scoped API key
- Displays confirmation with key prefix after generation

**Step 2: Recording Details**
- Input for recording name (e.g., "Login flow", "Checkout process")
- Input for target website URL
- Auto-populated user agent and viewport dimensions
- Starts the recording session via the API

**Step 3: Snippet Code**
- Displays the complete JavaScript snippet to embed
- Copy button to quickly copy code to clipboard
- Shows generated session ID and status
- Instructions for stopping the recording

### Updated `Recordings.tsx`
- Added "+ Start Recording" button in the header
- Integrated `StartRecordingModal` component
- Modal state management

## User Flow

1. User clicks "+ Start Recording" button on Recordings page
2. Modal opens to Step 1
3. User enters a name for the API key (default: `recorder-YYYY-MM-DD`)
4. Clicks "Generate API Key" - API key is created and displayed
5. Modal advances with Step 2 fields enabled
6. User enters:
   - Recording name (e.g., "User signup flow")
   - Target website URL (e.g., https://example.com)
7. Clicks "Start Recording"
8. API creates a new recording session
9. Modal shows Step 3 with:
   - Complete snippet code ready to copy
   - Session ID for reference
   - Instructions to call `SliplesRecorder.stop()` when done
10. User copies the snippet and pastes it into their website's `<head>`
11. User interacts with the website to record UI events
12. User calls `SliplesRecorder.stop()` in browser console to stop recording
13. User can view and annotate the recorded session in the Recordings page

## API Endpoints Used

### Generate API Key
```
POST /api/v1/auth/keys
Headers: 
  Content-Type: application/json
Body:
  {
    "name": "recorder-2026-04-20",
    "project_id": "uuid"  // optional, from current project
  }
Response:
  {
    "id": "uuid",
    "key": "64-character-hex-string",  // Full key, only returned once
    "key_prefix": "first8chars",
    "name": "recorder-2026-04-20",
    "created_at": "2026-04-20T...",
    "active": true
  }
```

### Start Recording Session
```
POST /api/v1/recorder/sessions
Headers:
  Content-Type: application/json
  X-API-Key: <generated-key>
Body:
  {
    "name": "Login flow",
    "url": "https://example.com",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1920,
    "viewport_height": 1080
  }
Response:
  {
    "session_id": "uuid",
    "name": "Login flow",
    "status": "recording"
  }
```

## Generated Snippet

The modal generates code like:
```html
<!-- Sliples Recorder Snippet -->
<script src="https://sliples.agantis.in/api/v1/recorder/snippet.js?api_key=...&endpoint=...&project_id=..."></script>
<script>
  SliplesRecorder.init({
    sessionId: 'uuid',
    endpoint: 'https://sliples.agantis.in',
    apiKey: 'key'
  });

  // When done recording, call:
  // SliplesRecorder.stop();
</script>
```

## Implementation Details

### Modal State Management
- `step`: Tracks current step ('form' | 'snippet' | 'started')
- `recordingName`, `recordingUrl`: User inputs for recording details
- `keyName`: User input for API key name
- `isLoading`: Loading state during API calls
- `error`: Error message display
- `generatedKey`: Stores the generated API key response
- `startedRecording`: Stores the started recording session info
- `snippetCode`: Generated snippet code for display

### Error Handling
- Validates required fields before API calls
- Displays error messages in red banner
- Disables buttons during loading
- Allows users to try again without losing data

### UX Features
- Step-based flow is clear and linear
- Copy button for easy snippet copying
- Pre-filled defaults (API key name, user agent, viewport)
- Success confirmations at each step
- Instructions for next steps clearly displayed

## Deployment

- Built with TypeScript and React
- Uses existing Modal component structure
- Integrates with existing authentication (JWT + API key)
- Platform: linux/amd64 (cross-compiled for OpenShift)
- Deploy: `oc rollout restart deployment/sliples-frontend`

## Testing

Manual testing checklist:
- [ ] Click "+ Start Recording" button
- [ ] Modal opens with Step 1
- [ ] Enter API key name and generate key
- [ ] Verify key is displayed with prefix
- [ ] Fill in recording name and URL
- [ ] Click "Start Recording"
- [ ] Verify snippet code is displayed
- [ ] Verify copy button works
- [ ] Close modal and verify Recordings list
- [ ] Verify new recording appears with "recording" status

## Future Enhancements

- [ ] Display list of recent API keys used
- [ ] Option to reuse existing API keys
- [ ] Live preview of snippet code
- [ ] Browser detection and pre-filled viewport
- [ ] Direct snippet injection for testing
- [ ] Pause/resume recording capability
