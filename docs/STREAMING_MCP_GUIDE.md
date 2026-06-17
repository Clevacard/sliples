# Sliples Streaming API - MCP Integration Guide

## Overview

The Sliples streaming API provides real-time access to UI recording sessions via WebSockets, designed for easy integration with Model Context Protocol (MCP) tools and monitoring systems.

## Quick Start

### 1. Authentication

All endpoints require authentication via API key or user session:

```bash
# Using API key header
curl -H "X-API-Key: your-api-key" \
  https://api.sliples.io/api/v1/stream/sessions
```

### 2. Discover Active Sessions

List all active recording sessions with optional filters:

```bash
GET /api/v1/stream/sessions?domain=app.example.com&max_age_seconds=3600&limit=50
```

**Query Parameters:**
- `domain`: Filter by exact domain name (e.g., "app.example.com")
- `user_agent`: Partial match on user agent (e.g., "Chrome", "Mobile", "iPhone")
- `max_age_seconds`: Only return sessions younger than this (e.g., 3600 for last hour)
- `status`: Session status - "recording" (default), "stopped", "converted"
- `limit`: Max results (default 50, max 200)

**Response:**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "mac-chrome-20260617-1430",
    "url": "https://app.example.com/checkout",
    "domain": "app.example.com",
    "status": "recording",
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "viewport_width": 1920,
    "viewport_height": 1080,
    "client_ip": "203.0.113.42",
    "created_at": "2026-06-17T14:30:22Z",
    "age_seconds": 127,
    "event_count": 45,
    "active_streams": 2
  }
]
```

### 3. Connect to Event Stream

Establish WebSocket connection to stream events:

```javascript
const ws = new WebSocket(
  'wss://api.sliples.io/api/v1/stream/sessions/550e8400-e29b-41d4-a716-446655440000/ws?include_historic=true',
  {
    headers: {
      'X-API-Key': 'your-api-key'
    }
  }
);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message);
};

// Send keepalive ping every 30s
setInterval(() => ws.send('ping'), 30000);
```

**Connection Parameters:**
- `include_historic`: `true` (default) to receive all past events on connect, `false` for live-only

## Message Types

### Connection Flow

1. **connected** - Initial handshake with session metadata
2. **historic_event** - Past events (if `include_historic=true`)
3. **historic_complete** - All historic events sent
4. **live_event** - Real-time events as they occur
5. **session_stopped** - Session was stopped
6. **error** - Error occurred

### Message Formats

#### `connected`

```json
{
  "type": "connected",
  "format": "sliples-stream-v1",
  "session": {
    "id": "550e8400-...",
    "name": "mac-chrome-20260617-1430",
    "url": "https://app.example.com",
    "domain": "app.example.com",
    "status": "recording",
    "user_agent": "Mozilla/5.0...",
    "viewport": "1920x1080",
    "created_at": "2026-06-17T14:30:22Z",
    "stopped_at": null,
    "event_count": 45
  },
  "include_historic": true
}
```

#### `historic_event` / `live_event`

Events use MCP-optimized compact format:

```json
{
  "type": "live_event",
  "event": {
    "seq": 47,
    "ts": "2026-06-17T14:32:15.234Z",
    "type": "click",
    "url": "https://app.example.com/checkout",
    "target": "[data-testid=submit-button]",
    "tag": "button",
    "label": "Complete Purchase",
    "pos": {"x": 425, "y": 38}
  }
}
```

**Event Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| `seq` | Sequence number (ordering) | `47` |
| `ts` | ISO 8601 timestamp | `"2026-06-17T14:32:15.234Z"` |
| `type` | Event type | `"click"`, `"input"`, `"navigation"`, `"js_error"`, `"network_error"` |
| `url` | Page URL (when changed) | `"https://app.example.com/checkout"` |
| `target` | Element selector (prioritized) | `"[data-testid=email]"`, `"#login-btn"`, `"button.primary"` |
| `tag` | HTML tag name | `"button"`, `"input"`, `"a"` |
| `label` | Associated label text | `"Email Address"` |
| `value` | Input value (truncated, masked for passwords) | `"user@example.com"`, `"***"` |
| `pos` | Click coordinates | `{"x": 425, "y": 38}` |
| `key` | Keyboard event info | `{"key": "Enter", "ctrl": true}` |
| `step` | User-annotated step label | `"Login with valid credentials"` |
| `params` | Extracted parameters | `{"email": "userEmail"}` |
| `notes` | User notes | `"Expected to redirect to dashboard"` |
| `extra` | Additional data (errors, etc.) | `{"message": "TypeError: ...", "stack": "..."}` |

**Event Types:**

- `click` - Element clicked
- `input` - Text input (debounced)
- `change` - Select/checkbox changed
- `submit` - Form submitted
- `keydown` - Special key pressed (Enter, Tab, Esc, etc.)
- `navigation` - Page navigation
- `js_error` - JavaScript exception
- `network_error` - HTTP error (4xx/5xx)

#### `historic_complete`

```json
{
  "type": "historic_complete",
  "count": 45
}
```

#### `session_stopped`

```json
{
  "type": "session_stopped",
  "event": {
    "event_count": 52,
    "stopped_at": "2026-06-17T14:35:00Z"
  }
}
```

## MCP Tool Implementation

### Example: Session Monitor Tool

```python
import asyncio
import json
import websockets
from typing import Optional

class SliplesStreamClient:
    """MCP tool for monitoring Sliples recording sessions."""
    
    def __init__(self, api_key: str, base_url: str = "wss://api.sliples.io"):
        self.api_key = api_key
        self.base_url = base_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
    
    async def list_sessions(
        self,
        domain: Optional[str] = None,
        user_agent: Optional[str] = None,
        max_age_seconds: Optional[int] = None,
    ):
        """List active recording sessions."""
        import aiohttp
        
        params = {}
        if domain:
            params["domain"] = domain
        if user_agent:
            params["user_agent"] = user_agent
        if max_age_seconds:
            params["max_age_seconds"] = max_age_seconds
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/v1/stream/sessions",
                headers={"X-API-Key": self.api_key},
                params=params,
            ) as resp:
                return await resp.json()
    
    async def stream_session(
        self,
        session_id: str,
        include_historic: bool = True,
        event_callback: callable = None,
    ):
        """Stream events from a session in real-time."""
        uri = f"{self.base_url}/api/v1/stream/sessions/{session_id}/ws"
        uri += f"?include_historic={str(include_historic).lower()}"
        
        async with websockets.connect(
            uri,
            extra_headers={"X-API-Key": self.api_key},
        ) as websocket:
            self.ws = websocket
            
            # Keepalive task
            async def keepalive():
                while True:
                    await asyncio.sleep(30)
                    await websocket.send("ping")
            
            keepalive_task = asyncio.create_task(keepalive())
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    
                    if event_callback:
                        await event_callback(data)
                    
                    # Auto-exit on session stopped
                    if data["type"] == "session_stopped":
                        break
            finally:
                keepalive_task.cancel()
                self.ws = None


# Usage in MCP tool
async def monitor_checkout_flows():
    """Monitor all checkout flows in real-time."""
    client = SliplesStreamClient(api_key="your-api-key")
    
    # Find sessions on checkout pages
    sessions = await client.list_sessions(
        domain="app.example.com",
        max_age_seconds=3600,  # Last hour
    )
    
    checkout_sessions = [
        s for s in sessions
        if "checkout" in s["url"].lower()
    ]
    
    print(f"Found {len(checkout_sessions)} active checkout sessions")
    
    # Stream events from first session
    if checkout_sessions:
        session_id = checkout_sessions[0]["id"]
        
        async def handle_event(message):
            if message["type"] == "live_event":
                event = message["event"]
                if event["type"] == "js_error":
                    print(f"⚠️  JavaScript error in checkout: {event['extra']}")
                elif event["type"] == "network_error":
                    print(f"⚠️  Network error: {event['extra']}")
        
        await client.stream_session(
            session_id,
            include_historic=False,  # Live-only
            event_callback=handle_event,
        )
```

## Advanced Features

### Stream Statistics

Get aggregated stats about active streams:

```bash
GET /api/v1/stream/stats
```

```json
{
  "active_sessions": 12,
  "total_connections": 28,
  "sessions_by_domain": {
    "app.example.com": 15,
    "staging.example.com": 8,
    "demo.example.com": 5
  }
}
```

### Custom Broadcasts

Send custom messages to all clients watching a session:

```bash
POST /api/v1/stream/sessions/{session_id}/broadcast
Content-Type: application/json
X-API-Key: your-api-key

{
  "alert": "Payment gateway is experiencing delays",
  "severity": "warning"
}
```

All connected clients receive:

```json
{
  "type": "custom",
  "timestamp": "2026-06-17T14:40:00Z",
  "message": {
    "alert": "Payment gateway is experiencing delays",
    "severity": "warning"
  }
}
```

## Use Cases

### 1. Live User Behavior Analysis

Monitor user interactions in real-time to identify UX issues:

```python
async def analyze_user_behavior(session_id):
    client = SliplesStreamClient(api_key="...")
    
    click_patterns = []
    
    async def analyze_event(msg):
        if msg["type"] == "live_event":
            event = msg["event"]
            if event["type"] == "click":
                click_patterns.append(event["target"])
                
                # Detect rage clicks
                if len(click_patterns) >= 3:
                    recent = click_patterns[-3:]
                    if len(set(recent)) == 1:  # Same element clicked 3x
                        print(f"⚠️  Rage click detected on {recent[0]}")
    
    await client.stream_session(session_id, event_callback=analyze_event)
```

### 2. Error Monitoring

Watch for JavaScript and network errors across all sessions:

```python
async def monitor_errors():
    client = SliplesStreamClient(api_key="...")
    
    sessions = await client.list_sessions(status="recording")
    
    async def error_handler(msg):
        if msg["type"] == "live_event":
            event = msg["event"]
            if event["type"] in ["js_error", "network_error"]:
                # Send to error tracking service
                await log_to_sentry(event)
    
    # Monitor all sessions
    tasks = [
        client.stream_session(s["id"], include_historic=False, event_callback=error_handler)
        for s in sessions
    ]
    await asyncio.gather(*tasks)
```

### 3. Conversion Funnel Tracking

Track users through multi-step flows:

```python
async def track_checkout_funnel(session_id):
    funnel_steps = [
        "cart",
        "shipping",
        "payment",
        "confirmation"
    ]
    current_step = 0
    
    async def track_progress(msg):
        nonlocal current_step
        
        if msg["type"] == "live_event":
            event = msg["event"]
            if event["type"] == "navigation":
                url = event["url"].lower()
                
                # Check if user progressed to next step
                if current_step < len(funnel_steps):
                    next_step = funnel_steps[current_step]
                    if next_step in url:
                        current_step += 1
                        print(f"✓ User reached step {current_step}: {next_step}")
                
                # Check for drop-off
                if "cart" in url and current_step > 0:
                    print(f"⚠️  User returned to cart from step {current_step}")
    
    await client.stream_session(session_id, event_callback=track_progress)
```

## Rate Limits & Performance

- **WebSocket connections**: Unlimited concurrent connections per session
- **Historic replay**: Loads all past events on connect (can be disabled)
- **Event throughput**: ~1000 events/second per session
- **Message size**: Events compressed to ~100-500 bytes each (MCP-optimized)
- **Reconnection**: Client should reconnect on disconnect with exponential backoff

## Event Format Philosophy

The MCP-optimized event format prioritizes:

1. **Token efficiency** - Compact field names (`seq`, `ts`, `pos` vs `sequence`, `timestamp`, `position`)
2. **Essential context** - Only fields relevant to the event type
3. **Prioritized selectors** - `data-testid` > ARIA > ID > CSS (most stable to least)
4. **Truncated values** - Long text truncated to 200 chars, masked for sensitive fields
5. **Flat structure** - No deep nesting for easy parsing

This makes events ideal for:
- LLM analysis (low token cost)
- Stream processing (small message size)
- Pattern matching (consistent structure)
- Real-time dashboards (minimal bandwidth)

## Error Handling

### WebSocket Disconnects

Clients should handle disconnects gracefully:

```python
async def stream_with_retry(session_id):
    max_retries = 5
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            await client.stream_session(session_id)
            break  # Success
        except websockets.ConnectionClosed:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries exceeded")
```

### Session Not Found

If session ID is invalid or expired:

```json
{
  "type": "error",
  "message": "Recording session not found"
}
```

WebSocket closes with code `4004`.

## Security Notes

- **Authentication required** - All endpoints require valid API key or user session
- **CORS enabled** - WebSocket connections allowed from any origin (with valid auth)
- **Sensitive data** - Password fields automatically masked as `"***"`
- **Private sessions** - Only users with project access can stream sessions
- **Historic data** - Can be disabled per connection to prevent data leakage

## Support

- **Documentation**: https://docs.sliples.io/streaming
- **API Reference**: https://api.sliples.io/docs#/Streaming
- **Issues**: https://github.com/Clevacard/sliples/issues
- **Email**: support@agantis.team
