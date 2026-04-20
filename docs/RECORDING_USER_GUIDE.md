# UI Recording User Guide

This guide walks you through recording, reviewing, and annotating UI interactions for conversion to automated test scenarios.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Step-by-Step Instructions](#step-by-step-instructions)
3. [Recording Best Practices](#recording-best-practices)
4. [Reviewing Recordings](#reviewing-recordings)
5. [Annotating Steps](#annotating-steps)
6. [Troubleshooting](#troubleshooting)

## Quick Start

The recording workflow consists of three phases:

1. **Record** - Capture UI interactions using the Sliples recorder snippet
2. **Review** - View the recorded events in the Sliples UI
3. **Annotate** - Label steps, mark screenshots, and parametrize values

## Step-by-Step Instructions

### Phase 1: Starting a Recording

#### 1.1 Open the Recordings Page

1. Log in to Sliples at https://sliples.agantis.in
2. Click **Recordings** in the left sidebar
3. Click the **+ Start Recording** button in the top-right corner

#### 1.2 Generate an API Key

In the modal that opens, you'll see **Step 1: Generate API Key**

1. Review the default API key name (e.g., `recorder-2026-04-20`)
2. (Optional) Change the name to something more descriptive (e.g., `recorder-login-flow`)
3. Click **Generate API Key**

**Important:** The full API key is now displayed in a code block. **Save this key securely** - you won't see it again! Click **Copy** to save it to your clipboard.

#### 1.3 Enter Recording Details

Once the key is generated, **Step 2: Recording Details** appears.

1. **Recording Name** - Enter a descriptive name for this recording session
   - Examples: "User login flow", "Checkout process", "Password reset"
   - This helps you identify the recording later

2. **Website URL** - Enter the URL where you'll record interactions
   - Example: `https://example.com`
   - Make sure the website is accessible in your current browser

3. Click **Start Recording**

The system creates a new recording session and generates the embed code.

#### 1.4 Embed the Snippet

**Step 3: Add Snippet to Website** shows the JavaScript code to embed.

1. **Copy the code** using the Copy button
2. Open your website's HTML source code or admin panel
3. Find the `<head>` section
4. Paste the code into the `<head>` tag
5. Save and refresh your website

**Example placement in HTML:**
```html
<!DOCTYPE html>
<html>
  <head>
    <title>My Website</title>
    <!-- Sliples Recorder Snippet -->
    <script src="..."></script>
    <script>
      SliplesRecorder.init({...});
    </script>
  </head>
  <body>
    ...
  </body>
</html>
```

### Phase 2: Recording Interactions

#### 2.1 Start Recording

Once the snippet is embedded:

1. Refresh your website in the browser
2. Check the browser console (F12 → Console tab)
3. You should see: `[Sliples] Recording started for session: <session-id>`

#### 2.2 Interact Normally

The recorder captures:
- **Clicks** on buttons, links, form fields
- **Form inputs** (text, select boxes, checkboxes, radio buttons)
- **Navigation** (page changes, hash changes)
- **Keyboard events** (Enter key presses, special keys)

Simply use your website like a normal user:
- Fill out forms
- Click buttons
- Navigate between pages
- Perform the workflow you want to test

#### 2.3 Stop Recording

When you're finished recording:

1. Open the browser console (F12 → Console tab)
2. Type the command: `SliplesRecorder.stop()`
3. Press Enter
4. You should see: `[Sliples] Recording stopped`

#### 2.4 Return to Sliples

Go back to the Sliples UI at https://sliples.agantis.in/recordings

You should see your new recording in the list with status **"recording"** or **"stopped"**.

---

### Phase 3: Reviewing & Annotating

#### 3.1 View Recording Sessions

1. Navigate to **Recordings** page
2. Use filters to find your session:
   - **Search** by name or URL
   - **Status** dropdown (recording/stopped/converted)
3. Click **View** to see the recording details

#### 3.2 Review Events

The Recording Details page shows:

- **Session header** with name, URL, status badge
- **Summary cards** showing:
  - Total number of events
  - Browser information
  - Viewport dimensions
  - Recording duration

- **Event list** showing each interaction in order:
  - Sequence number
  - Timestamp
  - Event type (click, input, navigation, etc.)
  - Element information (selector, label, value)
  - User annotations (if added)

Click any event to expand and see full details.

#### 3.3 Edit Event Annotations

For each event, click **Edit Annotations** to open the edit modal:

##### Add a Step Label

1. In the **Step Label** field, enter a human-readable description
   - Examples:
     - "Enter email address"
     - "Click login button"
     - "Wait for dashboard to load"
     - "Navigate to account settings"

2. Use consistent naming across similar steps
3. Click **Save Changes**

The label will appear in the event list and be used when converting to test scenarios.

##### Mark for Screenshots

1. Check the **📷 Mark for screenshot** checkbox
2. This tells the test runner to capture a screenshot at this point during playback
3. Useful for:
   - Verifying successful page loads
   - Capturing important confirmations
   - Documenting visual state changes

Click **Save Changes**

##### Parametrize Values

Parameters allow you to replace hardcoded values with environment variables. This makes recordings reusable across different test environments.

**Example:** You entered `user@example.com` during recording, but you want tests to use different emails based on environment.

1. In the **Parameters (Parametrize)** section, add a new row:
   - **Parameter name**: `email` (the value you want to replace)
   - **Variable name**: `TEST_USER_EMAIL` (the environment variable)

2. The system will replace `user@example.com` with `${TEST_USER_EMAIL}` during playback

3. You can add multiple parameters per step:
   - Parameter: `password` → Variable: `TEST_PASSWORD`
   - Parameter: `phone` → Variable: `TEST_PHONE`

4. Click **Save Changes**

**Common parameters:**
- User credentials: `TEST_USER`, `TEST_PASSWORD`, `TEST_EMAIL`
- Test data: `TEST_PRODUCT_ID`, `TEST_ORDER_NUMBER`
- Environment URLs: `API_ENDPOINT`, `BASE_URL`

##### Add Notes

1. In the **Notes** field, add context about this step:
   - Why this step matters
   - Expected outcomes
   - Known issues or considerations
   - Related test scenarios

2. Examples:
   - "This step validates the password reset flow"
   - "Email delivery may be delayed in staging"
   - "Use a valid phone number for SMS verification"

3. Click **Save Changes**

Notes are visible to the entire team and help with maintenance.

#### 3.4 View Event Context

Below the edit fields, you'll see **Event Context** showing:

- **Type**: The type of event (click, input, select, etc.)
- **Test ID**: The `data-testid` attribute if present
- **Label**: Human-readable label from the element
- **Value**: The value entered or changed

This helps you understand what element was interacted with.

---

## Recording Best Practices

### Before Recording

1. **Clear your browser cache**
   - Old data might interfere with recording
   - Use an incognito/private window for clean state

2. **Use stable test accounts**
   - Create dedicated test user accounts
   - Use test data that won't change between runs

3. **Know your workflow**
   - Plan the steps you'll perform
   - Document any expected delays or waits

### During Recording

1. **Go slowly**
   - Pause between interactions
   - Let pages fully load before proceeding

2. **Use meaningful data**
   - Enter realistic values
   - Use valid formats (emails, phone numbers, dates)

3. **Mark important steps**
   - Note which steps need screenshots
   - Plan which values need parameterization

4. **Avoid randomness**
   - Don't click random elements
   - Don't use timestamps or random IDs in inputs

### After Recording

1. **Review immediately**
   - While the workflow is fresh in your mind
   - Catch any missed interactions

2. **Be thorough with annotations**
   - Clear labels help others understand the test
   - Good parameters make the test reusable

3. **Test your parameters**
   - Verify environment variables exist
   - Confirm variable names are correct

---

## Reviewing Recordings

### Filtering & Searching

**Search by Name or URL**
- Partial matches work: "login" finds "Login flow"
- Case-insensitive search

**Filter by Status**
- **recording** - Still being recorded, can't be converted yet
- **stopped** - Finished recording, ready for review
- **converted** - Already converted to a test scenario

### Event Sequence

Events are numbered starting from 1 and show in chronological order.

Each event displays:
- **Sequence #** - Order in the workflow
- **Timestamp** - When the event occurred
- **Event Type** - click, input, navigation, etc.
- **Element Info** - What was clicked or changed

### Expanding Events

Click an event to see:
- **Full element selector** (CSS, XPath, text content, etc.)
- **Event details** (coordinates, input value, etc.)
- **Current annotations** (if any)
- **Edit button** to add/modify annotations

---

## Annotating Steps

### When to Annotate

Annotate **every significant step**:

✓ DO annotate:
- User actions (clicks, inputs, navigation)
- Page loads and transitions
- Form submissions
- Important waits or delays

✗ DON'T annotate:
- Mouse movements without interaction
- Hover events (unless critical)
- Duplicate/accidental interactions

### Label Naming Conventions

Use action-oriented, descriptive names:

**Good:**
- "Enter email address"
- "Click continue button"
- "Verify success message"
- "Select delivery method"

**Avoid:**
- "Click" (not descriptive)
- "Event 3" (not meaningful)
- "Test stuff" (too vague)
- "Wait" (use notes instead)

### Parameter Naming Conventions

Parameter names should match their purpose:

**Credentials:**
- `username` / `email` / `phone`
- `password` / `secret_key`

**Test Data:**
- `product_id` / `order_number`
- `address` / `postal_code`
- `name` / `company_name`

**Environment Variables:**
- Use UPPERCASE: `TEST_USER`, `PROD_API_KEY`
- Prefix with context: `TEST_`, `ADMIN_`, `API_`

### Screenshot Markers

Mark for screenshots at:

1. **Success states**
   - After successful login
   - Confirmation page
   - Transaction complete

2. **Important transitions**
   - Before/after critical actions
   - Form validation errors
   - Navigation changes

3. **Visual verification points**
   - Cart contents
   - User profile updates
   - Search results

---

## Troubleshooting

### Recording Not Starting

**Problem:** Snippet not loading or session doesn't start

**Solutions:**
1. Check browser console (F12) for errors
2. Verify API key was correctly copied
3. Confirm website URL is correct and accessible
4. Check if website blocks inline scripts (CSP headers)
5. Try in a different browser or incognito window

### Events Not Being Recorded

**Problem:** Some clicks or inputs aren't appearing in the recording

**Solutions:**
1. Refresh the page - the snippet needs to be loaded
2. Check that the `SliplesRecorder.init()` call succeeded
3. Verify you're interacting with standard HTML elements
4. Some JavaScript frameworks (React, Vue) may need additional setup
5. Try recording slowly and deliberately

### Can't Find Session in List

**Problem:** Started recording but don't see it in the list

**Solutions:**
1. Refresh the Recordings page
2. Check the status filter - may be filtered out
3. Search by the recording name
4. Wait a moment for the UI to update
5. Check if you're in the right project (top selector)

### Snippet Code Not Working

**Problem:** Pasted the code but recording still doesn't work

**Solutions:**
1. Verify the code is in the `<head>` section (or `<body>`)
2. Check for JavaScript errors in console
3. Confirm the website reloaded after adding code
4. Make sure you copied the entire code block
5. Check that API key in the code matches what you generated
6. Try a fresh reload with Ctrl+Shift+R (cache bust)

### Content Security Policy (CSP) Violation

**Problem:** Error in console: "Fetch API cannot load... violates the document's Content Security Policy"

**Solutions:**
1. The website has strict security policies blocking external scripts
2. Ask your website admin to add these to the CSP headers:
   - `script-src: 'self' https://sliples.agantis.in`
   - `connect-src: 'self' https://sliples.agantis.in`
3. Try recording in an incognito/private browser window
4. For development/testing, temporarily disable CSP
5. Contact your Sliples administrator for alternative embedding methods

### Can't Stop Recording

**Problem:** `SliplesRecorder.stop()` command doesn't work

**Solutions:**
1. Open developer console (F12) while on the website
2. Make sure you're typing in the **Console** tab, not other tabs
3. Verify the recorder is running - should see `[Sliples]` messages
4. Try refreshing and re-embedding the snippet
5. Check browser network tab to see if API calls are succeeding

### Missing Events or Incorrect Data

**Problem:** Some events missing or showing wrong values

**Solutions:**
1. Some frameworks cache form inputs - clear and re-enter
2. Very fast interactions may be batched together
3. Network delays might cause out-of-order events
4. Refresh page if something seems wrong and start over
5. Check the session details view to see all events

---

## Advanced Topics

### Custom Element Selectors

The recorder captures multiple selectors for each element:
- **CSS selector** - `.button.primary#submit`
- **XPath** - `//*[@id="form"]/button[1]`
- **data-testid** - Best for maintainability
- **aria-label** - Accessibility attributes
- **Text content** - Fallback if other selectors fail

If elements are fragile, add `data-testid` attributes to your website:
```html
<button data-testid="login-submit">Login</button>
```

### Reusing Recordings

Once annotated, a recording can be:
1. **Converted to a scenario** (future feature)
2. **Duplicated** for similar workflows
3. **Referenced** by other team members

### Environment-Specific Recording

Record the same workflow in different environments:
- Development (for quick testing)
- Staging (for pre-production validation)
- Production simulation (with test accounts)

Use parameters to make scenarios work across all environments.

---

## Tips for Success

1. **Start small** - Record simple workflows first
2. **Be consistent** - Use the same naming style across recordings
3. **Document thoroughly** - Good annotations = better tests
4. **Test your work** - Verify recordings playback correctly
5. **Share knowledge** - Comment on tricky steps to help teammates
6. **Keep it DRY** - Use parameters to avoid duplicating data
7. **Version your scenarios** - Keep track of changes over time

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review browser console (F12) for error messages
3. Reach out to your team lead or QA coordinator
4. File a bug report with details about what you recorded

For API integration questions, see the [API Documentation](./API.md).

For technical details on the recording system, see [Recording Sessions Architecture](./RECORDINGS_FEATURE.md).
