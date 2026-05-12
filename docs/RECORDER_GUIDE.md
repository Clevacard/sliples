# Sliples UI Recorder Guide

The Sliples Recorder captures UI interactions from websites and converts them into automatable test scenarios. Record user actions and replay them in headless browsers for automated testing.

## Quick Start

### Option 1: Browser Console via Bookmarklet (Recommended)

**If CSP allows script tags (no fetch blocking):**

Create a browser bookmarklet and click it on your website:

```javascript
javascript:(function(){
  const script = document.createElement('script');
  script.src = 'https://sliples.agantis.in/sliples-recorder.js';
  document.head.appendChild(script);
  script.onload = () => {
    const apiKey = prompt('Enter API Key:');
    if (apiKey) {
      window.SliplesRecorder.configure({ apiKey });
      window.SliplesRecorder.start(prompt('Recording name:') || 'Test');
    }
  };
})();
```

**If website has strict CSP (fetch/eval blocked):**

1. Download `https://sliples.agantis.in/sliples-recorder.js` locally
2. Host it on your own domain or server
3. Replace the URL in the bookmarklet with your local URL

This avoids CSP violations since it loads from your own domain.

**Console method (if neither CSP blocks):**

```javascript
// Load the recorder
fetch('https://sliples.agantis.in/api/v1/recorder/snippet.js?api_key=YOUR_API_KEY')
  .then(r => r.text())
  .then(eval);

// Start recording
SliplesRecorder.start('My Test Recording');

// ... interact with the website ...

// Stop and upload
SliplesRecorder.stop();
```

Note: If you see errors in console from "newrelic.js", that's just the browser's error reporting. The snippet still loads. If fetch fails with CSP error, use the bookmarklet or local approach above.

### Option 2: Direct Script Tag (For Your Own Website)

If you control the website code, add to your HTML:

```html
<script src="https://sliples.agantis.in/sliples-recorder.js"></script>
<script>
  // Configure recorder
  SliplesRecorder.configure({
    apiKey: 'YOUR_API_KEY',
    endpoint: 'https://sliples.agantis.in/api/v1',
    projectId: 'YOUR_PROJECT_ID' // optional
  });
</script>
```

Then in the console:

```javascript
SliplesRecorder.start('Login Test');
// ... interact with page ...
SliplesRecorder.stop();
```

**For local development or testing environments:**

Download the snippet locally and host on your own domain to avoid CSP issues:

```html
<script src="/js/sliples-recorder.js"></script>
<!-- or from your local server -->
```

### Option 3: Local Development Setup

For testing on localhost or internal environments:

1. Download the snippet:
   ```bash
   wget https://sliples.agantis.in/sliples-recorder.js -O ./public/sliples-recorder.js
   ```

2. Add to your test HTML:
   ```html
   <script src="/sliples-recorder.js"></script>
   <script>
     SliplesRecorder.configure({
       apiKey: 'YOUR_API_KEY',
       endpoint: 'https://sliples.agantis.in/api/v1'
     });
   </script>
   ```

3. Start recording from console:
   ```javascript
   SliplesRecorder.start('My Test');
   ```

This avoids all CSP issues since everything is served from your own server.

### Option 4: Allowed domains
In dev console:
`fetch('https://sliples.agantis.in/api/v1/recorder/snippet.js?mode=domain&endpoint=https://sliples.agantis.in/api/v1')
  .then(r => r.text())
  .then(eval);`

  or add a snippet:
  
`<script>https://sliples.agantis.in/api/v1/recorder/snippet.js?mode=domain&endpoint=https://sliples.agantis.in/api/v1</script>`
  

## Configuration

### Basic Usage

```javascript
SliplesRecorder.configure({
  apiKey: 'your-api-key-here',
  endpoint: 'https://sliples.agantis.in/api/v1',
  projectId: 'optional-project-uuid' // if set, recordings are associated with this project
});

SliplesRecorder.start('Recording Name');
// interact with page
SliplesRecorder.stop();
```

### Starting a Recording

```javascript
SliplesRecorder.start('Login Flow Test');
```

The recording name is optional and will be auto-generated if omitted (e.g., "Recording 04/14/2026 14:30:45").

### Stopping a Recording

```javascript
SliplesRecorder.stop();
```

Returns an object with recording metadata:
```javascript
{
  id: "session-uuid",
  name: "Login Flow Test",
  status: "stopped",
  event_count: 42,
  created_at: "2026-04-14T01:00:00Z",
  stopped_at: "2026-04-14T01:02:15Z"
}
```

### Checking Recording Status

```javascript
if (SliplesRecorder.isRecording) {
  console.log('Recording active, session:', SliplesRecorder.sessionId);
}
```

## What Gets Recorded

The recorder captures:

### Events
- **click** - Mouse clicks with coordinates and element selectors
- **input** - Form field text input (passwords are masked as `***`)
- **change** - Select/radio/checkbox changes
- **submit** - Form submissions
- **keydown** - Special keys: Enter, Tab, Escape, Backspace, Delete + modifier keys (Ctrl, Alt, Shift, Cmd)
- **navigation** - URL changes and page reloads

### Element Selectors (Multiple Strategies)
For robust playback, each interaction records multiple selector strategies:
- **CSS selector** - `.button.primary` or `#submit-btn`
- **XPath** - `//*[@id="form"]/button[1]`
- **Text content** - For label-based lookup
- **data-testid** - `data-testid="login-submit"` attribute
- **aria-label** - Accessibility labels

### Element Metadata
- Tag name, ID, classes
- Form field name and type
- Associated label text
- Placeholder text
- ARIA role

### Page Context
- Current URL
- Browser user agent
- Viewport width/height
- Viewport dimensions at recording time

## Event Batching

Events are batched and sent to the server every 3 seconds automatically. You don't need to do anything—the recorder handles this in the background.

## API Key

Get your API key from the Sliples dashboard:

1. Go to **Projects** → Your Project
2. Navigate to **Settings** → **API Keys**
3. Click **+ New API Key**
4. Copy the key (only shown once!)
5. Use it with the recorder

## Common Scenarios

### Testing a Login Flow

```javascript
// Load recorder
fetch('https://sliples.agantis.in/api/v1/recorder/snippet.js?api_key=YOUR_KEY')
  .then(r => r.text()).then(eval);

// Start recording
SliplesRecorder.start('Login Flow');

// User actions in browser:
// 1. Type username
// 2. Type password
// 3. Click "Sign In"
// 4. Wait for redirect

// Stop when done
SliplesRecorder.stop();
```

### Recording Multi-Page Flow

```javascript
SliplesRecorder.start('Complete User Journey');

// Page 1: Login
// ... type credentials and submit ...

// Page 2: Dashboard (automatically captured as navigation event)
// ... click on settings ...

// Page 3: Settings
// ... change preferences ...

SliplesRecorder.stop();

// The full multi-page journey is now recorded!
```

### Testing in Different Environments

```javascript
// Configure for staging
SliplesRecorder.configure({
  apiKey: 'your-api-key',
  endpoint: 'https://sliples-staging.agantis.in/api/v1'
});

SliplesRecorder.start('Staging Test');
```

## Troubleshooting

### CSP (Content Security Policy) Blocks Recording

**Error:** `Fetch API cannot load ... Refused to connect because it violates the document's Content Security Policy`

**Why:** The website you're recording has strict CSP that blocks external script loads or fetches.

**Solutions:**

1. **Use a bookmarklet with local file** (Best for external websites):
   - Download `https://sliples.agantis.in/sliples-recorder.js` 
   - Host it locally on your own domain
   - Use that URL in the bookmarklet instead

2. **Add Sliples to CSP whitelist** (For testing environments):
   ```html
   <meta http-equiv="Content-Security-Policy" content="
     script-src 'self' https://sliples.agantis.in/;
     connect-src 'self' https://sliples.agantis.in/
   ">
   ```

3. **Local development** (Recommended for development):
   - Include the snippet from your own server
   - No CSP issues, faster loading

### NewRelic Script Warning in Console

**Error:** `newrelic.js:1504 Fetch API cannot load ...`

**Why:** This is just how the browser reports the error location—the website has NewRelic monitoring, and the error surfaces through it. Not actually a NewRelic problem.

**Fix:** Use one of the CSP solutions above to prevent the fetch from being blocked in the first place.

### "Invalid API Key" Error

```javascript
// Make sure your API key is valid and hasn't been revoked
// Check it in the Sliples dashboard
SliplesRecorder.configure({ apiKey: 'YOUR_ACTUAL_KEY' });
```

### Recording Not Sending Events

Check the browser console for errors:
```javascript
// Open DevTools → Console tab
// Look for [Sliples] messages
// Check Network tab to see if requests are being sent
```

### Elements Not Being Found During Playback

The recorder uses multiple selector strategies. If one fails, others are tried:
1. CSS selector
2. XPath
3. data-testid attribute
4. aria-label
5. Text content matching

If an element has none of these, it may fail during playback. Solutions:
- Add `data-testid="unique-id"` to important elements
- Add descriptive `aria-label` attributes
- Keep element IDs stable

### Password Fields Are Masked

Passwords are intentionally recorded as `***` for security. During playback, you'll need to provide actual credentials separately.

### Recording Stops Unexpectedly

Common causes:
- Network connection dropped (check Network tab in DevTools)
- API key was revoked
- Session expired

Resume by calling `SliplesRecorder.start()` again.

## Advanced: Direct API Usage

You can also interact with the API directly:

### Start a Recording

```bash
curl -X POST https://sliples.agantis.in/api/v1/recorder/sessions \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test",
    "url": "https://example.com",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1280,
    "viewport_height": 720
  }'
```

### Submit Events

```bash
curl -X POST https://sliples.agantis.in/api/v1/recorder/sessions/SESSION_ID/events \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "sequence": 0,
        "timestamp": "2026-04-14T01:00:00.000Z",
        "event_type": "click",
        "selector_css": ".button.primary",
        "url": "https://example.com",
        "coordinates": {"x": 100, "y": 50}
      }
    ]
  }'
```

### List Recordings

```bash
curl -X GET https://sliples.agantis.in/api/v1/recorder/sessions \
  -H "X-API-Key: YOUR_KEY"
```

### Get Recording Details

```bash
curl -X GET https://sliples.agantis.in/api/v1/recorder/sessions/SESSION_ID/events \
  -H "X-API-Key: YOUR_KEY"
```

## Privacy & Security

- **Passwords are masked** as `***` and never sent to the server
- **Sensitive data** - Avoid recording with real API keys or tokens visible
- **Local storage** - Events are queued locally and sent every 3 seconds
- **HTTPS only** - Always use HTTPS URLs for security
- **API key protection** - Treat your API key like a password

## Tips for Better Recordings

1. **Use data-testid** on important elements
   ```html
   <button data-testid="login-submit">Sign In</button>
   ```

2. **Add aria-labels** for accessibility (and better element identification)
   ```html
   <input aria-label="Email address" type="email" />
   ```

3. **Keep IDs stable** - Avoid dynamically generated IDs
   ```html
   <!-- ✓ Good -->
   <button id="submit-btn">Submit</button>
   
   <!-- ✗ Avoid -->
   <button id="btn_12345_xyz">Submit</button>
   ```

4. **Record at realistic speed** - Don't rush through interactions
   - Give pages time to load
   - Wait for animations
   - Let form validation happen

5. **Test your recordings** - Run them in the test environment to verify they work

## Getting Help

- Check the [Sliples Documentation](https://docs.sliples.agantis.in)
- View recorded events in the Sliples dashboard
- Check browser console for [Sliples] debug messages
- Contact support at support@agantis.in
