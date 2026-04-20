# Recording Quick Reference

## The 6-Step Recording Workflow

### 1. Click "+ Start Recording"
From the **Recordings** page, click the button in the top-right corner.

### 2. Generate API Key
- Name: Give it a descriptive name (e.g., `recorder-login`)
- **Copy and save the full key** - you won't see it again!
- Click **Generate API Key**

### 3. Enter Recording Details
- **Recording Name**: What you're recording (e.g., "User login flow")
- **Website URL**: Where you'll record (e.g., `https://example.com`)
- Click **Start Recording**

### 4. Embed the Snippet
- **Copy** the JavaScript code shown
- Paste it into your website's `<head>` tag
- Refresh your website

### 5. Record Your Actions
- Open browser console (F12 → Console)
- Verify you see: `[Sliples] Recording started`
- Use your website normally - click, fill forms, navigate
- Type `SliplesRecorder.stop()` in console when done

### 6. Review & Annotate
- Go back to **Recordings** page
- Click **View** on your new recording
- For each step, click **Edit Annotations** to add:
  - **Step Label**: What this step does
  - **📷 Screenshot**: Mark important steps
  - **Parameters**: Replace hardcoded values with `${VARIABLE_NAME}`
  - **Notes**: Additional context

---

## Console Commands

```javascript
// Check if recorder is running
console.log('[Sliples] Recorder loaded');

// Stop recording
SliplesRecorder.stop();

// (Advanced) Check session ID
console.log(window.__sliplesSessionId);
```

---

## Parameter Examples

| Use Case | Parameter | Variable | Example |
|----------|-----------|----------|---------|
| User login | `email` | `TEST_USER_EMAIL` | `user@test.com` → `${TEST_USER_EMAIL}` |
| | `password` | `TEST_PASSWORD` | `SecurePass123` → `${TEST_PASSWORD}` |
| Product test | `product_id` | `TEST_PRODUCT` | `SKU-12345` → `${TEST_PRODUCT}` |
| Address | `zip_code` | `TEST_ZIP` | `90210` → `${TEST_ZIP}` |

---

## Label Naming Examples

| Action | Label |
|--------|-------|
| Click login button | "Click login button" |
| Enter email field | "Enter email address" |
| Fill password | "Enter password" |
| Click submit | "Click submit button" |
| Verify success | "Verify login success message" |
| Navigate to account | "Click account menu" |
| Enter search query | "Search for product" |

---

## Best Practices Checklist

- [ ] Use a fresh browser or incognito window
- [ ] Test account is ready before recording
- [ ] Website is accessible at the given URL
- [ ] Go slowly - let pages load between actions
- [ ] Use valid, realistic test data
- [ ] Don't click random elements
- [ ] Review recording immediately after
- [ ] Add labels to every significant step
- [ ] Mark important steps for screenshots
- [ ] Parametrize all test data values
- [ ] Add notes explaining the workflow

---

## Troubleshooting Quick Fixes

| Problem | Fix |
|---------|-----|
| No console message | Refresh page, check snippet pasted correctly |
| Recording won't stop | Try `SliplesRecorder.stop()` again, refresh page |
| Can't find my recording | Refresh Recordings page, check project selector |
| Events look wrong | Try recording again more slowly |
| Snippet code won't load | Check CSP headers, try incognito window |
| Can't copy the API key | Scroll in the code block, use Copy button |

---

## Environment Variables Template

Create these in your test environment:

```bash
# User Credentials
TEST_USER_EMAIL=testuser@example.com
TEST_PASSWORD=SecureTestPass123!
TEST_USERNAME=testuser

# Test Data
TEST_PRODUCT_ID=PROD-SKU-001
TEST_ORDER_NUMBER=ORD-2026-001
TEST_ZIP_CODE=90210

# URLs (if parametrizing)
TEST_BASE_URL=https://example.com
TEST_API_ENDPOINT=https://api.example.com
```

---

## Common Recording Scenarios

### Login Flow
1. Navigate to login page
2. Enter email
3. Enter password
4. Click login
5. Verify dashboard loads
6. Mark dashboard load for screenshot

**Parameters**: email, password
**Notes**: "Validates standard login flow"

### Form Submission
1. Navigate to form
2. Fill each required field
3. Select options from dropdowns
4. Enter test data
5. Submit form
6. Verify success page

**Parameters**: All form data fields
**Notes**: "Tests form validation and submission"

### Search & Filter
1. Navigate to search page
2. Enter search query
3. Apply filters
4. Click search button
5. Verify results
6. Click first result

**Parameters**: search_query, filter_values
**Notes**: "Tests search functionality"

### Multi-step Workflow
1. Record each step separately if complex
2. Or record the entire workflow at once
3. Break into logical sections with labels
4. Mark key transition points

**Parameters**: User-specific data at each step
**Notes**: "Detailed workflow for [scenario name]"

---

## Resource Links

- **Full Guide**: [Recording User Guide](./RECORDING_USER_GUIDE.md)
- **API Reference**: [API Documentation](./API.md)
- **Technical Details**: [Recordings Feature](./RECORDINGS_FEATURE.md)
- **Help & Support**: [User Guide](./USER_GUIDE.md)

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open browser console | F12 or Cmd+Option+I (Mac) |
| Go to Console tab | F12 → Console |
| Clear console | Cmd+K (Mac) or Ctrl+L (Windows) |
| Copy from console | Select text, Cmd+C / Ctrl+C |

---

## File Locations

- Recordings interface: https://sliples.agantis.in/recordings
- API endpoint: `/api/v1/recorder/...`
- Documentation: `/docs/RECORDING_USER_GUIDE.md`

---

## FAQ

**Q: Can I re-record if I make a mistake?**
A: Yes! Start a new recording session. You can delete the old one.

**Q: Can I pause and resume recording?**
A: Not yet. Stop and start a new session if needed.

**Q: Do I have to record in one sitting?**
A: Yes, each recording is one continuous session.

**Q: Can multiple people record simultaneously?**
A: Yes, each person gets their own session with its own API key.

**Q: How long can a recording be?**
A: No hard limit, but complex workflows are easier to maintain if broken into smaller recordings.

**Q: Can I edit recordings after stopping?**
A: No, but you can annotate each step individually.

**Q: What if I recorded something private by accident?**
A: Delete the recording and start over. Recordings are stored securely and not shared.

**Q: Can I convert my recording to a test right away?**
A: Annotate it first (add labels, parameters), then you can convert it.

---

## Tips & Tricks

✨ **Pro Tips:**
- Save API keys in a password manager for reuse
- Use consistent naming for similar recordings
- Team members can review and improve each other's recordings
- Screenshot markers help with visual regression testing
- Well-parametrized recordings are reusable across environments
- Add comments to complex workflows
- Test your parameters in your environment before converting

---

Last updated: 2026-04-20
