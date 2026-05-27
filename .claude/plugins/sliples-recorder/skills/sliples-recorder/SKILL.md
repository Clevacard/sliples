---
name: sliples-recorder
description: >
  Authenticate with Sliples (https://sliples.agantis.in) via browser-based
  Google OAuth and analyse front-end recording sessions. No API keys needed —
  auth is handled via a short-lived device-flow token. Trigger: "analyse
  sliples", "list sliples sessions", "sliples recording", "/sliples".
---

# Sliples Recorder Skill

Sliples captures real user interactions (clicks, inputs, navigation, errors) as
browser events. This skill lets you authenticate, browse sessions, and analyse
the event stream.

## Constants

```bash
SLIPLES_API="https://sliples.agantis.in/api/v1"
SLIPLES_TOKEN_FILE="$HOME/.claude/sliples-token.json"
```

## Step 0 — Token Check

Before any API call, check for a valid saved token:

```bash
if [ -f "$SLIPLES_TOKEN_FILE" ]; then
  EXPIRES_AT=$(jq -r '.expires_at' "$SLIPLES_TOKEN_FILE")
  NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  # If expires_at > now, token is still valid
  if [[ "$EXPIRES_AT" > "$NOW" ]]; then
    TOKEN=$(jq -r '.token' "$SLIPLES_TOKEN_FILE")
  else
    TOKEN=""  # expired, re-auth
  fi
else
  TOKEN=""  # no token, auth required
fi
```

If `TOKEN` is empty, run the Auth Flow below.

## Auth Flow

```bash
# 1. Create nonce
RESP=$(curl -s -X POST "$SLIPLES_API/auth/cli-token")
NONCE=$(echo "$RESP" | jq -r '.nonce')
LOGIN_URL=$(echo "$RESP" | jq -r '.login_url')

echo "[Sliples] Opening browser for authentication..."
echo "[Sliples] If browser does not open, visit: $LOGIN_URL"

# 2. Open browser
case "$(uname -s)" in
  Darwin) open "$LOGIN_URL" ;;
  Linux)
    if grep -qi microsoft /proc/version 2>/dev/null; then
      cmd.exe /c start "" "$LOGIN_URL" 2>/dev/null || xdg-open "$LOGIN_URL"
    else
      xdg-open "$LOGIN_URL"
    fi ;;
  *) echo "Open in browser: $LOGIN_URL" ;;
esac

# 3. Poll for JWT (max 2 minutes, 3s interval)
TOKEN=""
EXPIRES_AT=""
for i in $(seq 1 40); do
  POLL_RESP=$(curl -s -w "\n%{http_code}" "$SLIPLES_API/auth/cli-token/$NONCE")
  HTTP_CODE=$(echo "$POLL_RESP" | tail -1)
  BODY=$(echo "$POLL_RESP" | head -1)
  if [ "$HTTP_CODE" = "200" ]; then
    TOKEN=$(echo "$BODY" | jq -r '.access_token')
    EXPIRES_AT=$(echo "$BODY" | jq -r '.expires_at')
    echo "[Sliples] Authenticated successfully."
    break
  elif [ "$HTTP_CODE" = "404" ]; then
    echo "[Sliples] Login window expired. Run again to retry."
    break
  fi
  sleep 3
done

# 4. Save token
if [ -n "$TOKEN" ]; then
  echo "{\"token\":\"$TOKEN\",\"expires_at\":\"$EXPIRES_AT\"}" > "$SLIPLES_TOKEN_FILE"
  chmod 600 "$SLIPLES_TOKEN_FILE"
fi
```

## List Sessions

```bash
TOKEN=$(jq -r '.token' "$SLIPLES_TOKEN_FILE")

# All recent sessions (latest 20)
curl -s -H "Authorization: Bearer $TOKEN" \
  "$SLIPLES_API/recorder/sessions?limit=20" \
  | jq '[.[] | {id, name, url, domain, status, event_count, created_at}]'

# Filter by domain
curl -s -H "Authorization: Bearer $TOKEN" \
  "$SLIPLES_API/recorder/sessions?limit=10&domain=admin.giftstarr.cards" \
  | jq '[.[] | {id, name, url, domain, status, event_count, created_at}]'
```

Present the list to the user and ask which session to analyse (by name or index).

## Fetch Events

```bash
TOKEN=$(jq -r '.token' "$SLIPLES_TOKEN_FILE")
SESSION_ID="<uuid>"

curl -s -H "Authorization: Bearer $TOKEN" \
  "$SLIPLES_API/recorder/sessions/$SESSION_ID/events" | jq '.'
```

## Analysis Guidance

Each event has these key fields:
- `sequence` — order within page load (resets on refresh)
- `timestamp` — ISO8601, authoritative order
- `event_type` — `click`, `input`, `change`, `keydown`, `navigation`, `submit`, `js_error`, `network_error`
- `url` — page URL at time of event
- `selector_css`, `selector_xpath`, `selector_aria`, `selector_test_id` — element locators
- `tag_name`, `element_id`, `element_classes`, `label_text`, `placeholder` — element metadata
- `value` — input value (`***` for passwords)
- `key_info` — `{key, ctrl, alt, shift, meta}` for keydown events
- `extra_data` — error details for `js_error` / `network_error`

### Analysis Output Format

Produce a structured report with these sections:

**1. Session Summary**
- Domain, total events, duration (first→last timestamp), pages visited

**2. User Journey**
- Numbered step-by-step narrative of what the user did
- Group by page/URL
- Note timing gaps > 10 seconds (user paused/hesitated)

**3. Issues Found**
- `js_error` events: message, file, line → likely cause
- `network_error` events: URL, status code → what failed
- Rage-clicks: same selector clicked 3+ times in < 5 seconds (user frustration)
- Dead-end navigations: user went back without completing a flow
- Failed form submissions

**4. Suggested Playwright Test Steps**
- Convert key user actions to Playwright locator suggestions
- Prefer `selector_test_id` > `selector_aria` > `selector_css`
- Example: `await page.getByTestId('submit-btn').click()`

## Error Handling

- **401 Unauthorized** → token expired, delete `$SLIPLES_TOKEN_FILE` and re-auth
- **404 on session** → wrong session ID, list sessions again
- **jq not found** → `brew install jq` (macOS) or `apt install jq` (Linux)
- **curl not found** → install curl via package manager
