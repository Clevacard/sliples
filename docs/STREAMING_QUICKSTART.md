# Sliples Streaming - Quick Start Guide

Get started with Sliples real-time event streaming in 5 minutes.

## Prerequisites

- Python 3.8+
- Docker & Docker Compose
- Sliples backend running

## 1. Start Required Services

```bash
cd /path/to/sliples
docker-compose up -d redis postgres
```

Verify Redis is running:

```bash
docker-compose ps redis
# Should show "Up"

redis-cli ping
# Should return "PONG"
```

## 2. Start the API Server

```bash
cd backend
uvicorn app.main:app --reload
```

Server should start on `http://localhost:8000`

## 3. Get an API Key

### Option A: Use Existing Key

If you already have an API key, skip to step 4.

### Option B: Create via API

```bash
# Create a user and project first (if not exists)
curl -X POST http://localhost:8000/api/v1/auth/keys \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Streaming Test Key",
    "project_id": "YOUR_PROJECT_ID"
  }'
```

Save the returned API key (starts with `slp_`).

## 4. Create a Test Recording Session

### Option A: Via Browser

1. Open `http://localhost:5173` (frontend)
2. Navigate to recorder page
3. Load the recorder snippet
4. Perform some UI interactions
5. Note the session ID from the UI

### Option B: Via API

```bash
# Start a session
curl -X POST http://localhost:8000/api/v1/recorder/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "name": "Test Session",
    "url": "https://example.com",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1920,
    "viewport_height": 1080
  }'

# Returns: {"session_id": "...", "name": "...", "status": "recording"}
```

## 5. List Active Sessions

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/v1/stream/sessions

# Filter by domain
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/api/v1/stream/sessions?domain=example.com"
```

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Test Session",
    "url": "https://example.com",
    "domain": "example.com",
    "status": "recording",
    "user_agent": "Mozilla/5.0...",
    "viewport_width": 1920,
    "viewport_height": 1080,
    "client_ip": "127.0.0.1",
    "created_at": "2026-06-17T14:30:00Z",
    "age_seconds": 45,
    "event_count": 12,
    "active_streams": 0
  }
]
```

## 6. Stream Events (Python)

### Install Dependencies

```bash
pip install aiohttp websockets
```

### Basic Stream

```python
import asyncio
import websockets
import json

async def stream_session():
    session_id = "YOUR_SESSION_ID"
    api_key = "YOUR_API_KEY"
    
    uri = f"ws://localhost:8000/api/v1/stream/sessions/{session_id}/ws"
    headers = {"X-API-Key": api_key}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        print("Connected!")
        
        # Receive and print events
        async for message in ws:
            if message == "pong":
                continue
            
            data = json.loads(message)
            print(f"{data['type']}: {data}")

asyncio.run(stream_session())
```

Save as `stream_test.py` and run:

```bash
python stream_test.py
```

## 7. Use the Example Client

The included example client provides event analysis:

```bash
# List sessions
python examples/mcp_stream_client.py \
  --api-key YOUR_API_KEY \
  --list-only

# Stream with analysis
python examples/mcp_stream_client.py \
  --api-key YOUR_API_KEY \
  --domain example.com

# Stream specific session (no historic)
python examples/mcp_stream_client.py \
  --api-key YOUR_API_KEY \
  --session-id SESSION_ID \
  --no-historic
```

**Output:**

```
📡 Fetching active sessions...

✓ Found 1 active session(s):

1. Test Session
   ID: 550e8400-e29b-41d4-a716-446655440000
   URL: https://example.com
   Domain: example.com
   Age: 120s
   Events: 25
   Watchers: 0

→ Streaming first session: Test Session

✓ Connected to session: Test Session
  URL: https://example.com
  Domain: example.com
  Status: recording
  Events: 25
  Historic: True

✓ Historic replay complete: 25 events
⏳ Watching for live events...

🖱️  [14:32:15] Click: [data-testid=submit-btn] (Submit)
⌨️  [14:32:20] Input: #email = 'user@example.com'
📨 [14:32:25] Submit: form.checkout
```

## 8. Monitor Errors

Watch for JavaScript and network errors:

```python
import asyncio
import websockets
import json

async def monitor_errors(session_id, api_key):
    uri = f"ws://localhost:8000/api/v1/stream/sessions/{session_id}/ws?include_historic=false"
    headers = {"X-API-Key": api_key}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Skip connected message
        await ws.recv()
        
        print("Monitoring for errors...")
        
        async for message in ws:
            data = json.loads(message)
            
            if data.get("type") == "live_event":
                event = data["event"]
                
                # Alert on errors
                if event["type"] in ["js_error", "network_error"]:
                    print(f"\n❌ ERROR DETECTED:")
                    print(f"   Type: {event['type']}")
                    print(f"   Time: {event['ts']}")
                    
                    if extra := event.get("extra"):
                        print(f"   Details: {extra}")

asyncio.run(monitor_errors("SESSION_ID", "API_KEY"))
```

## 9. Detect Rage Clicks

```python
from datetime import datetime
from collections import deque

class RageClickDetector:
    def __init__(self):
        self.clicks = deque(maxlen=5)  # Last 5 clicks
    
    def check(self, event):
        if event["type"] != "click":
            return False
        
        now = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        target = event.get("target", "")
        
        self.clicks.append((now, target))
        
        if len(self.clicks) >= 3:
            # Check last 3 clicks
            recent = list(self.clicks)[-3:]
            targets = [t for _, t in recent]
            times = [ts for ts, _ in recent]
            
            # Same element?
            if len(set(targets)) == 1:
                # Within 2 seconds?
                time_span = (times[-1] - times[0]).total_seconds()
                if time_span < 2:
                    return True
        
        return False

# Usage
detector = RageClickDetector()

async for message in ws:
    data = json.loads(message)
    if data.get("type") == "live_event":
        event = data["event"]
        if detector.check(event):
            print(f"⚠️  RAGE CLICK: {event.get('target')}")
```

## 10. Next Steps

### Read the Docs

- **MCP Integration Guide:** [STREAMING_MCP_GUIDE.md](./STREAMING_MCP_GUIDE.md)
- **Architecture:** [STREAMING_ARCHITECTURE.md](./STREAMING_ARCHITECTURE.md)
- **Feature Overview:** [STREAMING_README.md](./STREAMING_README.md)

### Use Cases

- **Live Support:** Monitor users and offer help when stuck
- **Error Tracking:** Alert on JS/network errors in real-time
- **UX Research:** Identify confusion points and friction
- **A/B Testing:** Compare behavior between variants
- **Bot Detection:** Flag suspicious patterns

### Integrate with Tools

Build integrations with:

- Error tracking (Sentry, Rollbar)
- Analytics (Mixpanel, Amplitude)
- Customer support (Intercom, Zendesk)
- CI/CD dashboards
- Custom monitoring tools

## Troubleshooting

### "Connection refused"

Redis or API server not running:

```bash
docker-compose ps redis
docker-compose up -d redis
```

### "401 Unauthorized"

Invalid or missing API key:

```bash
# Verify key works
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/v1/stream/sessions
```

### "404 Not Found"

Session doesn't exist or was deleted:

```bash
# List sessions
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/v1/stream/sessions
```

### No Events Received

Check session status:

```bash
curl -H "X-API-Key: YOUR_KEY" \
  http://localhost:8000/api/v1/stream/sessions/SESSION_ID/info
```

Verify Redis pub/sub:

```bash
redis-cli
> PSUBSCRIBE sliples:recording:*:events
# (perform browser actions, should see messages)
```

### "Connection closed"

Network timeout or session stopped:

- Implement reconnection with exponential backoff
- Check if session is still active
- Verify network connectivity

## Tips

1. **Use Historic Replay:** Set `include_historic=true` to see past events on connect
2. **Filter Sessions:** Use domain/user-agent filters to find relevant sessions
3. **Keepalive:** Send `ping` every 30s to keep connection alive
4. **Handle Disconnects:** Implement automatic reconnection with backoff
5. **Monitor Stats:** Check `/stream/stats` to see active connections
6. **Password Safety:** Password fields are auto-masked as `***`
7. **Token Efficiency:** Events use compact MCP format (~100-500 bytes each)

## Common Patterns

### Watch All Sessions from Domain

```python
async def watch_domain(domain, api_key):
    sessions = await client.list_sessions(domain=domain)
    
    tasks = [
        stream_session(s["id"], api_key)
        for s in sessions
    ]
    
    await asyncio.gather(*tasks)
```

### Alert on Specific Event Type

```python
async def alert_on_type(session_id, event_type, api_key):
    async with websockets.connect(...) as ws:
        async for message in ws:
            data = json.loads(message)
            if data.get("type") == "live_event":
                event = data["event"]
                if event["type"] == event_type:
                    # Send alert
                    send_alert(f"{event_type} detected", event)
```

### Track Conversion Funnel

```python
funnel = ["cart", "shipping", "payment", "confirmation"]
current_step = 0

async for message in ws:
    event = data["event"]
    if event["type"] == "navigation":
        url = event["url"].lower()
        if current_step < len(funnel) and funnel[current_step] in url:
            current_step += 1
            print(f"✓ Reached step {current_step}: {funnel[current_step-1]}")
```

## Support

- **Documentation:** https://docs.sliples.io/streaming
- **Issues:** https://github.com/Clevacard/sliples/issues
- **Email:** support@agantis.team

---

**Happy Streaming!** 🚀
