# Sliples Streaming Architecture

## High-Level Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        Browser Clients                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ User Session │  │ User Session │  │ User Session │             │
│  │   #12345     │  │   #12346     │  │   #12347     │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │ UI Events        │                 │                     │
│         │ (batched 3s)     │                 │                     │
└─────────┼──────────────────┼─────────────────┼─────────────────────┘
          │                  │                 │
          ▼                  ▼                 ▼
    ┌─────────────────────────────────────────────────┐
    │         FastAPI Server (Recorder API)           │
    │                                                  │
    │  POST /recorder/sessions/{id}/events            │
    │    ├─→ Save to PostgreSQL                       │
    │    └─→ Publish to Redis pub/sub                 │
    │                                                  │
    │  WS /stream/sessions/{id}/ws                    │
    │    └─→ Subscribe to Redis pub/sub               │
    └──────────┬─────────────────┬────────────────────┘
               │                 │
               │                 │
    ┌──────────▼──────┐   ┌─────▼──────────┐
    │   PostgreSQL    │   │     Redis      │
    │  (persistence)  │   │   (pub/sub)    │
    │                 │   │                │
    │ • Sessions      │   │ Channel format:│
    │ • Events        │   │ sliples:       │
    │ • Metadata      │   │  recording:    │
    │                 │   │   {session_id}:│
    └─────────────────┘   │    events      │
                          └────────┬───────┘
                                   │
                          ┌────────▼────────────────────────┐
                          │  WebSocket Subscribers          │
                          │                                 │
                          │  ┌──────────────────────────┐   │
                          │  │  MCP Tools & Monitors    │   │
                          │  │  • Error tracking        │   │
                          │  │  • UX analysis           │   │
                          │  │  • Live support          │   │
                          │  │  • Bot detection         │   │
                          │  │  • A/B test analysis     │   │
                          │  └──────────────────────────┘   │
                          └─────────────────────────────────┘
```

## Component Interaction Flow

### 1. Event Recording Flow

```
┌─────────┐
│ Browser │ Records UI interaction (click, input, navigation)
└────┬────┘
     │ JavaScript recorder snippet batches events (3s interval)
     ▼
┌────────────┐
│   POST     │ /recorder/sessions/{session_id}/events
│  /events   │ Body: {events: [...]}
└─────┬──────┘
      │
      ▼
┌──────────────────┐
│ FastAPI Handler  │
│ record_events()  │
├──────────────────┤
│ 1. Validate auth │
│ 2. Save to DB    │───────────┐
│ 3. Commit txn    │           │
│ 4. Broadcast     │           ▼
└────┬─────────────┘    ┌──────────────┐
     │                  │ PostgreSQL   │
     │                  │ • recorded_  │
     │                  │   events     │
     │                  └──────────────┘
     │
     │ asyncio.create_task()
     ▼
┌──────────────────────────┐
│ _broadcast_events_to_    │
│ stream()                 │
├──────────────────────────┤
│ • Format as MCP event    │
│ • Publish to Redis       │
└────┬─────────────────────┘
     │
     ▼
┌──────────────────────────┐
│ Redis pub/sub            │
│ Channel: sliples:        │
│  recording:{id}:events   │
└────┬─────────────────────┘
     │
     └──→ Delivered to all WebSocket subscribers
```

### 2. WebSocket Streaming Flow

```
┌──────────────┐
│ MCP Client   │ Wants to watch session #12345
└──────┬───────┘
       │ Step 1: Discover sessions
       ▼
  GET /stream/sessions?domain=app.example.com
       │
       │ Returns: [{id: "12345", name: "...", event_count: 45, ...}]
       ▼
┌──────────────┐
│ Client       │ Chooses session
└──────┬───────┘
       │ Step 2: Get connection info
       ▼
  GET /stream/sessions/12345/info
       │
       │ Returns: {websocket_url: "/ws", supports_historic: true, ...}
       ▼
┌──────────────┐
│ Client       │ Connects WebSocket
└──────┬───────┘
       │ Step 3: Establish WebSocket
       ▼
  WS /stream/sessions/12345/ws?include_historic=true
       │
       ▼
┌───────────────────────────┐
│ WebSocket Handler         │
├───────────────────────────┤
│ 1. Accept connection      │
│ 2. Send "connected" msg   │
│ 3. Load historic events   │───────→ PostgreSQL query
│    (if requested)         │
│ 4. Send each as           │
│    "historic_event"       │
│ 5. Send "historic_        │
│    complete"              │
│ 6. Subscribe to Redis     │───────→ Redis pub/sub
│ 7. Forward live events    │
│ 8. Handle keepalive       │
└───────────────────────────┘
       │
       ├──→ Send: {"type": "connected", "session": {...}}
       ├──→ Send: {"type": "historic_event", "event": {...}}
       ├──→ Send: {"type": "historic_event", "event": {...}}
       ├──→ ...
       ├──→ Send: {"type": "historic_complete", "count": 45}
       │
       │ [Live events arrive via Redis]
       │
       └──→ Send: {"type": "live_event", "event": {...}}
```

### 3. Connection Management

```
┌─────────────────────────────────────────────────────┐
│            ConnectionManager                        │
│                                                     │
│  active_connections: Dict[session_id, Set[WS]]     │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Session #12345:                               │ │
│  │   ├─ WebSocket #1 (MCP Tool A)                │ │
│  │   ├─ WebSocket #2 (Dashboard)                 │ │
│  │   └─ WebSocket #3 (Support Console)           │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Session #12346:                               │ │
│  │   └─ WebSocket #4 (Error Monitor)             │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Methods:                                          │
│  • connect(ws, session_id)                        │
│  • disconnect(ws, session_id)                     │
│  • broadcast_to_session(session_id, message)      │
│  • get_connection_count(session_id)               │
│  • get_active_session_ids()                       │
└─────────────────────────────────────────────────────┘
```

## Data Models

### PostgreSQL Schema

```sql
-- Recording sessions
CREATE TABLE recording_sessions (
    id UUID PRIMARY KEY,
    project_id UUID,
    name VARCHAR(255),
    url TEXT,
    domain VARCHAR(255),
    user_agent TEXT,
    viewport_width INT,
    viewport_height INT,
    client_ip VARCHAR(45),
    status VARCHAR(20),  -- recording, stopped, converted
    created_at TIMESTAMP,
    stopped_at TIMESTAMP,
    INDEX idx_domain (domain),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Recorded events
CREATE TABLE recorded_events (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES recording_sessions(id),
    sequence INT,
    timestamp TIMESTAMP,
    event_type VARCHAR(50),  -- click, input, navigation, js_error, etc.
    
    -- Selectors (priority: test_id > aria > id > css)
    selector_test_id VARCHAR(255),
    selector_aria VARCHAR(255),
    element_id VARCHAR(255),
    selector_css TEXT,
    
    -- Element metadata
    tag_name VARCHAR(50),
    label_text TEXT,
    value TEXT,
    
    -- Coordinates, key info, extra data
    coordinates JSONB,
    key_info JSONB,
    extra_data JSONB,
    
    -- User annotations
    step_label TEXT,
    should_screenshot BOOLEAN,
    parameters JSONB,
    notes TEXT,
    
    INDEX idx_session_timestamp (session_id, timestamp),
    INDEX idx_session_sequence (session_id, sequence)
);
```

### Redis Pub/Sub Message Format

```json
{
  "type": "event_recorded",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-06-17T14:32:15.234Z",
  "sequence": 47,
  "data": {
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

### WebSocket Message Formats

#### Connected
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

#### Historic/Live Event
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

## Deployment Architecture

### Single-Server Setup (Development)

```
┌──────────────────────────────────────────────┐
│            Docker Host                       │
│                                              │
│  ┌────────────┐  ┌────────────┐             │
│  │ PostgreSQL │  │   Redis    │             │
│  │   :5432    │  │   :6379    │             │
│  └──────┬─────┘  └──────┬─────┘             │
│         │                │                   │
│  ┌──────┴────────────────┴─────┐            │
│  │      FastAPI Server         │            │
│  │         :8000               │            │
│  │  • HTTP/REST endpoints      │            │
│  │  • WebSocket endpoints      │            │
│  └─────────────────────────────┘            │
└──────────────────────────────────────────────┘
```

### Production Setup (Multi-Server)

```
                    Internet
                       │
                       ▼
              ┌────────────────┐
              │  Load Balancer │
              │  (sticky sess) │
              └────┬───────────┘
                   │
        ┏━━━━━━━━━━┻━━━━━━━━━━┓
        ▼                      ▼
┌──────────────┐      ┌──────────────┐
│ FastAPI #1   │      │ FastAPI #2   │
│  • HTTP API  │      │  • HTTP API  │
│  • WebSocket │      │  • WebSocket │
└────┬─────┬───┘      └────┬─────┬───┘
     │     │               │     │
     │     └───────┬───────┘     │
     │             │             │
     │      ┌──────▼──────┐      │
     │      │ Redis Cluster│     │
     │      │  (pub/sub)   │     │
     │      └──────────────┘     │
     │                           │
     └──────────┬────────────────┘
                │
         ┌──────▼──────┐
         │ PostgreSQL  │
         │  (primary)  │
         │             │
         │ (replicas)  │
         └─────────────┘
```

### Scaling Considerations

**Horizontal Scaling:**
- Multiple FastAPI servers share Redis pub/sub
- Sticky sessions recommended for WebSocket (but not required)
- PostgreSQL read replicas for historic event queries

**Redis Cluster:**
- Use Redis cluster or Sentinel for HA
- Pub/sub works across cluster nodes
- Monitor memory usage (pub/sub buffers)

**Load Balancing:**
- WebSocket sticky sessions (IP hash or cookie-based)
- Health check: `GET /health`
- Fallback to different server on disconnect

## Security Model

### Authentication Flow

```
┌──────────────┐
│ Client       │ Has API key: slp_12345678abcdefgh...
└──────┬───────┘
       │ Sends: X-API-Key: slp_12345678abcdefgh...
       ▼
┌───────────────────────────┐
│ get_api_key_or_user()     │
├───────────────────────────┤
│ 1. Extract API key        │
│ 2. Lookup by prefix       │──→ SELECT * FROM api_keys
│    (first 8 chars)        │    WHERE key_prefix = 'slp_1234'
│ 3. Verify bcrypt hash     │
│ 4. Check active status    │
│ 5. Return ApiKey object   │
└──────┬────────────────────┘
       │
       ▼
┌───────────────────────────┐
│ Check project scope       │
├───────────────────────────┤
│ IF api_key.project_id:    │
│   THEN verify session     │
│        belongs to project │
│ ELSE: global key, allow   │
└───────────────────────────┘
```

### Authorization Matrix

| Endpoint | Auth Required | Project Scope | Admin Only |
|----------|---------------|---------------|------------|
| `GET /stream/sessions` | ✅ | Optional filter | ❌ |
| `GET /stream/sessions/{id}/info` | ✅ | Session's project | ❌ |
| `WS /stream/sessions/{id}/ws` | ✅ | Session's project | ❌ |
| `GET /stream/stats` | ✅ | Global view | ❌ |
| `POST /stream/sessions/{id}/broadcast` | ✅ | Session's project | ❌ |

## Monitoring & Observability

### Key Metrics

```python
# Active WebSocket connections
active_connections_total = Gauge(
    'sliples_stream_connections_total',
    'Total active WebSocket connections'
)

# Connections per session
active_connections_per_session = Gauge(
    'sliples_stream_connections_per_session',
    'Active connections watching a session',
    ['session_id']
)

# Event broadcast rate
events_broadcast_total = Counter(
    'sliples_stream_events_broadcast_total',
    'Total events broadcast via streaming',
    ['session_id', 'event_type']
)

# Redis pub/sub lag
redis_pubsub_lag_seconds = Histogram(
    'sliples_stream_redis_lag_seconds',
    'Lag between event publication and delivery'
)

# WebSocket disconnect rate
websocket_disconnects_total = Counter(
    'sliples_stream_disconnects_total',
    'Total WebSocket disconnections',
    ['reason']  # 'normal', 'timeout', 'error'
)
```

### Health Checks

```bash
# API health
GET /health

# Redis connectivity
redis-cli ping

# WebSocket connectivity
wscat -c ws://localhost:8000/api/v1/stream/sessions/{id}/ws \
  -H "X-API-Key: ..."
```

## Error Handling

### Client-Side Reconnection

```python
async def stream_with_retry(session_id, max_retries=5):
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            await client.stream_session(session_id)
            break  # Success
        except websockets.ConnectionClosed as e:
            if e.code == 4004:  # Session not found
                print("Session not found")
                break
            
            if attempt < max_retries - 1:
                print(f"Reconnecting in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries exceeded")
```

### Server-Side Error Codes

| Code | Reason | Action |
|------|--------|--------|
| 1000 | Normal close | None |
| 4004 | Session not found | Stop retrying |
| 4003 | Forbidden | Check API key/permissions |
| 1011 | Internal error | Retry with backoff |

## Performance Tuning

### Redis Configuration

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

### FastAPI Settings

```python
# app/main.py
app = FastAPI(
    # WebSocket settings
    websocket_ping_interval=30,
    websocket_ping_timeout=60,
)
```

### PostgreSQL Indexes

```sql
-- Optimize historic event queries
CREATE INDEX idx_recorded_events_session_timestamp 
ON recorded_events(session_id, timestamp);

-- Optimize session listing
CREATE INDEX idx_recording_sessions_status_created 
ON recording_sessions(status, created_at DESC);

CREATE INDEX idx_recording_sessions_domain_status 
ON recording_sessions(domain, status);
```

---

**Last Updated:** 2026-06-17  
**Version:** 1.0.0
