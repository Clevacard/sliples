"""Real-time event streaming service for recording sessions.

Manages WebSocket connections and broadcasts recording events in real-time.
Designed for MCP consumption and monitoring tools.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Set, Optional, Any
from uuid import UUID

from fastapi import WebSocket
from redis.asyncio import Redis as AsyncRedis


class ConnectionManager:
    """Manages WebSocket connections for recording session streams."""

    def __init__(self):
        # session_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, session_id: str):
        """Add a WebSocket connection for a session."""
        await websocket.accept()
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast a message to all connections watching this session."""
        async with self._lock:
            connections = self.active_connections.get(session_id, set()).copy()

        if not connections:
            return

        # Send to all connections, remove dead ones
        dead_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Clean up dead connections
        if dead_connections:
            async with self._lock:
                if session_id in self.active_connections:
                    for conn in dead_connections:
                        self.active_connections[session_id].discard(conn)
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]

    def get_active_session_ids(self) -> list[str]:
        """Get list of session IDs with active connections."""
        return list(self.active_connections.keys())

    def get_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session."""
        return len(self.active_connections.get(session_id, set()))


# Global connection manager instance
connection_manager = ConnectionManager()


class StreamEventBroadcaster:
    """Broadcasts recording events to WebSocket clients via Redis pub/sub."""

    @staticmethod
    def get_session_channel(session_id: str) -> str:
        """Get Redis channel name for a session."""
        return f"sliples:recording:{session_id}:events"

    @staticmethod
    async def publish_event(
        redis: AsyncRedis,
        session_id: str,
        event_type: str,
        event_data: dict,
        sequence: Optional[int] = None,
    ):
        """Publish an event to the session's Redis channel.

        Args:
            redis: Redis client
            session_id: Recording session ID
            event_type: Type of event (event_recorded, session_started, session_stopped, etc.)
            event_data: Event payload
            sequence: Optional sequence number for ordering
        """
        message = {
            "type": event_type,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sequence": sequence,
            "data": event_data,
        }

        channel = StreamEventBroadcaster.get_session_channel(session_id)
        await redis.publish(channel, json.dumps(message))

    @staticmethod
    async def subscribe_to_session(
        redis: AsyncRedis,
        session_id: str,
        callback: callable,
    ):
        """Subscribe to a session's event stream.

        Args:
            redis: Redis client
            session_id: Recording session ID
            callback: Async function to call with each message
        """
        pubsub = redis.pubsub()
        channel = StreamEventBroadcaster.get_session_channel(session_id)
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await callback(data)
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        # Log error but continue listening
                        print(f"Error in stream callback: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()


def format_event_for_mcp(event: dict) -> dict:
    """Format a recorded event for MCP consumption.

    Creates a compact, structured format optimized for:
    - Token efficiency
    - Easy parsing
    - Essential context preservation
    """
    mcp_event = {
        "seq": event.get("sequence"),
        "ts": event.get("timestamp"),
        "type": event.get("event_type"),
    }

    # Add URL if navigation or changed
    if url := event.get("url"):
        mcp_event["url"] = url

    # Prioritized selector strategy
    if test_id := event.get("selector_test_id"):
        mcp_event["target"] = f"[data-testid={test_id}]"
    elif aria := event.get("selector_aria"):
        mcp_event["target"] = f"[aria-label={aria}]"
    elif elem_id := event.get("element_id"):
        mcp_event["target"] = f"#{elem_id}"
    elif css := event.get("selector_css"):
        mcp_event["target"] = css[:100]  # Truncate long selectors

    # Element context
    if tag := event.get("tag_name"):
        mcp_event["tag"] = tag

    if label := event.get("label_text"):
        mcp_event["label"] = label[:50]

    # Event-specific data
    if value := event.get("value"):
        # Truncate long values, mask sensitive data
        if event.get("element_type") == "password":
            mcp_event["value"] = "***"
        else:
            mcp_event["value"] = str(value)[:200]

    if coords := event.get("coordinates"):
        mcp_event["pos"] = coords

    if key_info := event.get("key_info"):
        mcp_event["key"] = key_info

    # User annotations (if present)
    if step_label := event.get("step_label"):
        mcp_event["step"] = step_label

    if params := event.get("parameters"):
        mcp_event["params"] = params

    if notes := event.get("notes"):
        mcp_event["notes"] = notes[:100]

    # Extra data for errors, etc.
    if extra := event.get("extra_data"):
        mcp_event["extra"] = extra

    return mcp_event


def format_session_summary_for_mcp(session: dict) -> dict:
    """Format session metadata for MCP consumption."""
    return {
        "id": session.get("id"),
        "name": session.get("name"),
        "url": session.get("url"),
        "domain": session.get("domain"),
        "status": session.get("status"),
        "user_agent": session.get("user_agent"),
        "viewport": f"{session.get('viewport_width')}x{session.get('viewport_height')}" if session.get('viewport_width') else None,
        "started": session.get("created_at"),
        "stopped": session.get("stopped_at"),
        "event_count": session.get("event_count", 0),
        "client_ip": session.get("client_ip"),
    }


async def get_redis_for_streaming() -> AsyncRedis:
    """Get Redis client for streaming operations."""
    from app.config import get_settings
    settings = get_settings()
    redis = AsyncRedis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    return redis
