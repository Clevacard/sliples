# Sliples Real-Time Streaming Feature

## Overview

The Sliples streaming feature provides real-time WebSocket access to UI recording sessions, enabling live monitoring, analysis, and integration with external tools and MCPs.

## Key Features

### 1. **Live Event Streaming**
- Real-time WebSocket streams of UI events as they're recorded
- Support for historic event replay on connection
- MCP-optimized compact event format
- Automatic keepalive and reconnection handling

### 2. **Session Discovery**
- List active recording sessions with rich filters:
  - Domain name (exact match)
  - User agent (partial match)
  - Session age (max seconds)
  - Session status (recording/stopped/converted)
- Includes metadata: event count, active watchers, viewport, etc.

### 3. **MCP-Ready Format**
- Token-efficient event encoding (~100-500 bytes per event)
- Prioritized selector strategies (data-testid → ARIA → ID → CSS)
- Automatic masking of sensitive data (passwords)
- Flat structure for easy parsing
- Timestamped and sequenced for ordering

### 4. **Monitoring & Analytics**
- Stream statistics (active sessions, connections by domain)
- Custom broadcast messages to watchers
- Error event tracking (JS errors, network failures)
- User behavior pattern detection

## Architecture

```
┌─────────────────┐
│  Browser Client │ ──→ Records UI events
└────────┬────────┘
         │ HTTP POST /recorder/sessions/{id}/events
         ↓
┌─────────────────┐
│  FastAPI Server │ ──→ Stores events in PostgreSQL
└────────┬────────┘     Publishes to Redis pub/sub
         │
         ├──→ PostgreSQL (persistent storage)
         │
         └──→ Redis pub/sub (real-time broadcast)
                    │
                    ↓
         ┌──────────────────────┐
         │  WebSocket Clients   │ ──→ MCPs, monitoring tools
         └──────────────────────┘
```

## Components

### Backend Services

1. **`app/services/stream_manager.py`**
   - `ConnectionManager`: WebSocket connection pool
   - `StreamEventBroadcaster`: Redis pub/sub integration
   - Event formatting utilities (MCP-optimized)

2. **`app/api/routes/stream.py`**
   - `GET /stream/sessions` - List active sessions
   - `GET /stream/sessions/{id}/info` - Connection info
   - `WS /stream/sessions/{id}/ws` - Event stream
   - `GET /stream/stats` - Stream statistics
   - `POST /stream/sessions/{id}/broadcast` - Custom messages

3. **`app/api/routes/recorder.py`** (enhanced)
   - Broadcasts events to Redis on recording
   - Publishes session lifecycle events (started/stopped)

### Example Clients

1. **`examples/mcp_stream_client.py`**
   - Python CLI client for streaming sessions
   - Event analysis and pattern detection
   - Rage-click detection
   - Error monitoring
   - Usage: `python mcp_stream_client.py --api-key <key>`

2. **Documentation**
   - `docs/STREAMING_MCP_GUIDE.md` - Complete integration guide
   - Event format specification
   - Use case examples
   - Rate limits and security notes

## Quick Start

### 1. Start the Server

Ensure Redis is running (required for pub/sub):

```bash
docker-compose up -d redis
```

### 2. List Active Sessions

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/stream/sessions
```

### 3. Stream Events (Python)

```python
import asyncio
import websockets
import json

async def stream_session(session_id):
    uri = f"ws://localhost:8000/api/v1/stream/sessions/{session_id}/ws"
    
    async with websockets.connect(
        uri,
        extra_headers={"X-API-Key": "your-api-key"}
    ) as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"{data['type']}: {data.get('event', {}).get('type')}")

asyncio.run(stream_session("550e8400-e29b-41d4-a716-446655440000"))
```

### 4. Use the Example Client

```bash
# Install dependencies
pip install aiohttp websockets

# List sessions
python examples/mcp_stream_client.py \
  --api-key your-api-key \
  --list-only

# Stream a session with analysis
python examples/mcp_stream_client.py \
  --api-key your-api-key \
  --domain app.example.com
```

## Event Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `click` | Element clicked | Button clicks, link navigation |
| `input` | Text input (debounced) | Form field completion |
| `change` | Select/checkbox changed | Dropdown selection |
| `submit` | Form submitted | Form submission tracking |
| `keydown` | Special key pressed | Enter/Tab navigation |
| `navigation` | Page navigation | Multi-page flow tracking |
| `js_error` | JavaScript exception | Error monitoring |
| `network_error` | HTTP error (4xx/5xx) | API failure detection |

## Use Cases

### 1. **Live User Support**
Monitor user sessions in real-time to provide proactive help when they encounter issues.

```python
async def watch_for_stuck_users(session_id):
    idle_threshold = 30  # seconds
    last_event_time = None
    
    async def check_idle(message):
        nonlocal last_event_time
        if message["type"] == "live_event":
            last_event_time = time.time()
            
    # Alert if no events for 30s
```

### 2. **Error Monitoring**
Track JavaScript and network errors across all active sessions.

```python
async def monitor_all_errors():
    sessions = await client.list_sessions(status="recording")
    
    for session in sessions:
        asyncio.create_task(stream_errors(session["id"]))
```

### 3. **A/B Test Analysis**
Track user behavior differences between variants.

```python
async def compare_checkout_flows():
    variant_a = await client.list_sessions(domain="a.example.com")
    variant_b = await client.list_sessions(domain="b.example.com")
    
    # Compare conversion rates, time-to-purchase, etc.
```

### 4. **Bot Detection**
Identify suspicious patterns (too fast, unnatural clicks).

```python
async def detect_bots(session_id):
    event_times = []
    
    async def analyze_timing(message):
        if message["type"] == "live_event":
            event_times.append(time.time())
            # Check for superhuman speed
```

### 5. **UX Research**
Analyze user behavior patterns to improve design.

```python
async def find_confusion_points(session_id):
    # Detect rage clicks, back-and-forth navigation, etc.
```

## Configuration

### Environment Variables

```bash
# Redis (required for streaming)
REDIS_URL=redis://localhost:6379/0

# Optional: Tune connection limits
MAX_WS_CONNECTIONS_PER_SESSION=100
```

### CORS

WebSocket endpoints are CORS-enabled by default. API key authentication is required regardless of origin.

## Performance

- **WebSocket throughput**: ~1,000 events/second per session
- **Message size**: 100-500 bytes per event (compressed)
- **Historic replay**: Loads all past events on connect (disable with `include_historic=false`)
- **Redis pub/sub**: Near-zero latency (<10ms)
- **Connection limits**: No hard limit on concurrent connections

## Security

- ✅ **Authentication required**: All endpoints require valid API key or user session
- ✅ **Project scoping**: Only users with project access can stream sessions
- ✅ **Sensitive data**: Password fields auto-masked as `"***"`
- ✅ **Rate limiting**: Standard API rate limits apply
- ✅ **Historic data**: Can be disabled per connection (`include_historic=false`)

## Troubleshooting

### "Recording session not found"
- Session ID is invalid or expired
- User doesn't have access to the session's project

### WebSocket Connection Closed
- Network interruption (client should reconnect with exponential backoff)
- Session stopped (normal termination)
- API key expired or invalid

### No Events Received
- Check `include_historic` setting (may need historic events first)
- Verify session is in "recording" status
- Check Redis connection (`docker-compose ps redis`)

### High Latency
- Redis overloaded (check `redis-cli info stats`)
- Network bandwidth saturated
- Too many historic events on connect (disable with `include_historic=false`)

## Future Enhancements

- [ ] Event filtering on server side (by event type)
- [ ] Compressed binary format option (MessagePack)
- [ ] Multi-session streaming (watch multiple sessions in one connection)
- [ ] Event search and replay API
- [ ] Built-in event analysis (heatmaps, funnels, cohorts)
- [ ] Webhook delivery option (for non-WebSocket clients)

## API Reference

See [STREAMING_MCP_GUIDE.md](./STREAMING_MCP_GUIDE.md) for complete API documentation.

## Contributing

When adding new event types or modifying the stream format:

1. Update `format_event_for_mcp()` in `stream_manager.py`
2. Document in `STREAMING_MCP_GUIDE.md`
3. Update example client in `examples/mcp_stream_client.py`
4. Add tests for new event types

## Support

- **Documentation**: https://docs.sliples.io/streaming
- **Issues**: https://github.com/Clevacard/sliples/issues
- **Email**: support@agantis.team
