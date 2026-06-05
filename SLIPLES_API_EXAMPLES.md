# Sliples API Usage Examples

## Authentication

### 1. Login via Web (Automatic)
```bash
# User clicks "Sign in with Google" button in frontend
# Frontend redirects to:
curl -v "http://localhost:8000/api/v1/auth/google/login"
# → Backend redirects to Google OAuth consent screen
# → User authorizes
# → Google redirects back to /api/v1/auth/google/callback?code=...
# → Backend creates JWT, sets httpOnly cookie, redirects to dashboard
```

### 2. Get Current User (Web UI - automatic via cookie)
```bash
curl -v \
  -H "Content-Type: application/json" \
  --cookie "access_token=eyJ..." \
  "http://localhost:8000/api/v1/auth/me"

# Response:
# {
#   "id": "550e8400-e29b-41d4-a716-446655440000",
#   "email": "user@example.com",
#   "name": "John Doe",
#   "picture_url": "https://...",
#   "workspace_domain": "example.com",
#   "role": "admin",
#   "is_active": true,
#   "created_at": "2025-03-20T10:00:00",
#   "last_login": "2025-03-27T14:30:00"
# }
```

### 3. Get New Token (Refresh)
```bash
curl -X GET \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/auth/token"

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 86400
# }
```

### 4. Logout (Clear Cookie)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  --cookie "access_token=eyJ..." \
  "http://localhost:8000/api/v1/auth/logout"

# Response:
# { "message": "Successfully logged out" }
```

---

## API Key Management

### 5. Create API Key
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "name": "ci-key-prod",
    "project_id": "550e8400-e29b-41d4-a716-446655440001"
  }' \
  "http://localhost:8000/api/v1/auth/keys"

# Response (SAVE THIS KEY - returned only once!):
# {
#   "id": "660e8400-e29b-41d4-a716-446655440002",
#   "project_id": "550e8400-e29b-41d4-a716-446655440001",
#   "name": "ci-key-prod",
#   "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3",
#   "key_prefix": "a1b2c3d4",
#   "created_at": "2025-03-27T15:00:00",
#   "active": true
# }
```

### 6. List API Keys (Masked)
```bash
curl -X GET \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/auth/keys"

# Response:
# [
#   {
#     "id": "660e8400-e29b-41d4-a716-446655440002",
#     "project_id": "550e8400-e29b-41d4-a716-446655440001",
#     "name": "ci-key-prod",
#     "key_prefix": "a1b2c3d4",
#     "created_at": "2025-03-27T15:00:00",
#     "last_used_at": "2025-03-27T16:30:00",
#     "active": true
#   }
# ]
```

### 7. Revoke API Key
```bash
curl -X DELETE \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/auth/keys/660e8400-e29b-41d4-a716-446655440002"

# Response: 204 No Content
```

---

## Recording Sessions - List & Retrieve

### 8. List All Recording Sessions
```bash
curl -X GET \
  -H "Authorization: Bearer eyJ..." \
  -H "X-Project-Id: 550e8400-e29b-41d4-a716-446655440001" \
  "http://localhost:8000/api/v1/recorder/sessions"

# Response:
# [
#   {
#     "id": "770e8400-e29b-41d4-a716-446655440003",
#     "project_id": "550e8400-e29b-41d4-a716-446655440001",
#     "name": "Login Flow - Chrome",
#     "url": "https://example.com/login",
#     "status": "stopped",
#     "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
#     "viewport_width": 1920,
#     "viewport_height": 1080,
#     "domain": "example.com",
#     "client_ip": "192.168.1.100",
#     "created_at": "2025-03-27T10:00:00",
#     "stopped_at": "2025-03-27T10:15:00",
#     "event_count": 42
#   }
# ]
```

### 9. Get Single Session
```bash
curl -X GET \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003"

# Response: (same as above, single object)
```

### 10. Get Session Events
```bash
curl -X GET \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003/events"

# Response:
# [
#   {
#     "id": "880e8400-e29b-41d4-a716-446655440004",
#     "sequence": 1,
#     "timestamp": "2025-03-27T10:00:05",
#     "event_type": "navigation",
#     "url": "https://example.com/login",
#     "value": null,
#     "selector_css": null,
#     "tag_name": null
#   },
#   {
#     "id": "880e8400-e29b-41d4-a716-446655440005",
#     "sequence": 2,
#     "timestamp": "2025-03-27T10:00:08",
#     "event_type": "click",
#     "url": "https://example.com/login",
#     "selector_test_id": "email-input",
#     "tag_name": "input",
#     "element_type": "email",
#     "coordinates": { "x": 400, "y": 200 }
#   },
#   {
#     "id": "880e8400-e29b-41d4-a716-446655440006",
#     "sequence": 3,
#     "timestamp": "2025-03-27T10:00:09",
#     "event_type": "input",
#     "value": "user@example.com",
#     "selector_test_id": "email-input",
#     "tag_name": "input"
#   }
# ]
```

---

## Recording Sessions - Record & Manage

### 11. Start Recording (Domain-based Auth)
```bash
# From browser JavaScript (via recorder snippet):
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: https://example.com" \
  -d '{
    "name": "User Registration Flow",
    "url": "https://example.com/signup",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1920,
    "viewport_height": 1080
  }' \
  "http://localhost:8000/api/v1/recorder/sessions"

# Response:
# {
#   "session_id": "770e8400-e29b-41d4-a716-446655440003",
#   "name": "User Registration Flow",
#   "status": "recording"
# }
```

### 12. Record Batch of Events
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Origin: https://example.com" \
  -d '{
    "events": [
      {
        "sequence": 1,
        "timestamp": "2025-03-27T10:00:05.000Z",
        "event_type": "navigation",
        "url": "https://example.com/signup",
        "selector_css": null
      },
      {
        "sequence": 2,
        "timestamp": "2025-03-27T10:00:08.500Z",
        "event_type": "click",
        "url": "https://example.com/signup",
        "selector_test_id": "first-name-field",
        "tag_name": "input",
        "coordinates": { "x": 400, "y": 200 }
      },
      {
        "sequence": 3,
        "timestamp": "2025-03-27T10:00:09.200Z",
        "event_type": "input",
        "value": "John",
        "selector_test_id": "first-name-field",
        "tag_name": "input"
      }
    ]
  }' \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003/events"

# Response:
# { "recorded": 3 }
```

### 13. Stop Recording
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003/stop"

# Response:
# {
#   "id": "770e8400-e29b-41d4-a716-446655440003",
#   "project_id": "550e8400-e29b-41d4-a716-446655440001",
#   "name": "User Registration Flow",
#   "url": "https://example.com/signup",
#   "status": "stopped",
#   "created_at": "2025-03-27T10:00:00",
#   "stopped_at": "2025-03-27T10:15:00",
#   "event_count": 42
# }
```

### 14. Rename Session
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{ "name": "Registration Flow - Chrome 120" }' \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003"

# Response: (updated session object)
```

### 15. Update Event Annotations
```bash
curl -X PATCH \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "step_label": "Fill in First Name",
    "should_screenshot": true,
    "parameters": { "firstName": "userInput" },
    "notes": "User enters their first name"
  }' \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003/events/880e8400-e29b-41d4-a716-446655440006"

# Response: (updated event object)
```

### 16. Delete Session
```bash
curl -X DELETE \
  -H "Authorization: Bearer eyJ..." \
  "http://localhost:8000/api/v1/recorder/sessions/770e8400-e29b-41d4-a716-446655440003"

# Response: 204 No Content
```

---

## Advanced - Export & Export Compact Format

### 17. Export Sessions (AI-Optimized Format)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJ..." \
  -d '{
    "session_ids": [
      "770e8400-e29b-41d4-a716-446655440003",
      "770e8400-e29b-41d4-a716-446655440004"
    ]
  }' \
  "http://localhost:8000/api/v1/recorder/sessions/export"

# Response (compact format for LLMs):
# {
#   "format": "sliples-session-export-v1",
#   "exported_at": "2025-03-27T16:45:00.000Z",
#   "session_count": 2,
#   "sessions": [
#     {
#       "id": "770e8400-e29b-41d4-a716-446655440003",
#       "name": "User Registration Flow",
#       "url": "https://example.com/signup",
#       "domain": "example.com",
#       "viewport": "1920x1080",
#       "started": "2025-03-27T10:00:00Z",
#       "stopped": "2025-03-27T10:15:00Z",
#       "events": [
#         {
#           "seq": 1,
#           "t": "2025-03-27T10:00:05Z",
#           "type": "navigation",
#           "url": "https://example.com/signup"
#         },
#         {
#           "seq": 2,
#           "t": "2025-03-27T10:00:08Z",
#           "type": "click",
#           "target": "[data-testid=first-name-field]",
#           "pos": { "x": 400, "y": 200 }
#         },
#         {
#           "seq": 3,
#           "t": "2025-03-27T10:00:09Z",
#           "type": "input",
#           "target": "[data-testid=first-name-field]",
#           "value": "John"
#         }
#       ]
#     }
#   ]
# }
```

---

## Using API Keys (CI/CD)

### 18. List Sessions with API Key
```bash
curl -X GET \
  -H "Authorization: Bearer a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3" \
  -H "X-Project-Id: 550e8400-e29b-41d4-a716-446655440001" \
  "http://localhost:8000/api/v1/recorder/sessions"

# OR if key format is key_prefix:key_full
curl -X GET \
  -H "X-API-Key: a1b2c3d4:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3" \
  -H "X-Project-Id: 550e8400-e29b-41d4-a716-446655440001" \
  "http://localhost:8000/api/v1/recorder/sessions"
```

### 19. Export Sessions with API Key (for CI/CD automation)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2g3" \
  -d '{ "session_ids": ["770e8400-e29b-41d4-a716-446655440003"] }' \
  "http://localhost:8000/api/v1/recorder/sessions/export" \
  | jq .  # Parse JSON

# Save to file:
curl -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ..." \
  -d '{ "session_ids": ["..."] }' \
  "http://localhost:8000/api/v1/recorder/sessions/export" \
  > recording_export.json
```

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "You don't have permission to create API keys in this project"
}
```

### 404 Not Found
```json
{
  "detail": "Recording session not found"
}
```

### 400 Bad Request
```json
{
  "detail": "An active API key with this name already exists"
}
```

---

## Notes

- **httpOnly Cookies:** Token is secure from JavaScript attacks
- **CORS:** withCredentials required for cookie inclusion
- **Token Expiry:** Default 24h (env: JWT_EXPIRY_HOURS)
- **Stateless:** No session table, just JWT validation
- **Rate Limits:** Check backend config (not specified here)
