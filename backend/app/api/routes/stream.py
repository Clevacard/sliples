"""Real-time streaming endpoints for recording sessions.

Provides:
- WebSocket stream of live events from active recording sessions
- List active sessions with filters (domain, user agent, age)
- Historic event replay on connection
- MCP-optimized event format
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecordingSession, RecordedEvent, RecordingStatus
from app.api.deps import get_api_key_or_user
from app.services.stream_manager import (
    connection_manager,
    StreamEventBroadcaster,
    format_event_for_mcp,
    format_session_summary_for_mcp,
    get_redis_for_streaming,
)


router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================

class ActiveSessionResponse(BaseModel):
    """Response model for an active recording session."""
    id: UUID
    name: str
    url: str
    domain: Optional[str]
    status: str
    user_agent: Optional[str]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    client_ip: Optional[str]
    created_at: datetime
    age_seconds: int
    event_count: int
    active_streams: int  # Number of WebSocket connections watching this session

    class Config:
        from_attributes = True


class StreamConnectionInfo(BaseModel):
    """Information about stream connection options."""
    session_id: UUID
    websocket_url: str
    supports_historic: bool
    mcp_format: str  # Format version for MCP clients


# =============================================================================
# Active Session List with Filters
# =============================================================================

@router.get("/stream/sessions", response_model=List[ActiveSessionResponse])
async def list_active_sessions(
    domain: Optional[str] = Query(None, description="Filter by domain name"),
    user_agent: Optional[str] = Query(None, description="Filter by user agent (partial match)"),
    max_age_seconds: Optional[int] = Query(None, description="Maximum session age in seconds"),
    status: Optional[str] = Query("recording", description="Session status (recording, stopped, converted)"),
    limit: int = Query(50, le=200, description="Maximum number of sessions to return"),
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    List active recording sessions with optional filters.

    Designed for monitoring tools and MCPs to discover active sessions.

    Filters:
    - domain: Exact match on domain name (e.g., "app.example.com")
    - user_agent: Partial match on user agent string (e.g., "Chrome", "Mobile")
    - max_age_seconds: Only return sessions younger than this (e.g., 3600 for last hour)
    - status: Session status (default: "recording" for active sessions)

    Returns sessions with:
    - Basic metadata (URL, domain, viewport, etc.)
    - Age in seconds
    - Event count
    - Number of active stream connections
    """
    query = db.query(RecordingSession)

    # Apply filters
    filters = []

    if status:
        try:
            status_enum = RecordingStatus(status)
            filters.append(RecordingSession.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Must be one of: recording, stopped, converted"
            )

    if domain:
        filters.append(RecordingSession.domain == domain)

    if user_agent:
        filters.append(RecordingSession.user_agent.ilike(f"%{user_agent}%"))

    if max_age_seconds is not None:
        cutoff = datetime.utcnow() - timedelta(seconds=max_age_seconds)
        filters.append(RecordingSession.created_at >= cutoff)

    if filters:
        query = query.filter(and_(*filters))

    # Order by most recent first
    sessions = query.order_by(RecordingSession.created_at.desc()).limit(limit).all()

    # Build response with additional metadata
    now = datetime.utcnow()
    result = []

    for session in sessions:
        # Count events
        event_count = db.query(RecordedEvent).filter(
            RecordedEvent.session_id == session.id
        ).count()

        # Get active stream count
        active_streams = connection_manager.get_connection_count(str(session.id))

        # Calculate age
        age_seconds = int((now - session.created_at).total_seconds())

        result.append(ActiveSessionResponse(
            id=session.id,
            name=session.name,
            url=session.url,
            domain=session.domain,
            status=session.status.value,
            user_agent=session.user_agent,
            viewport_width=session.viewport_width,
            viewport_height=session.viewport_height,
            client_ip=session.client_ip,
            created_at=session.created_at,
            age_seconds=age_seconds,
            event_count=event_count,
            active_streams=active_streams,
        ))

    return result


@router.get("/stream/sessions/{session_id}/info", response_model=StreamConnectionInfo)
async def get_stream_info(
    session_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    Get connection information for streaming a session.

    Returns WebSocket URL and capabilities.
    """
    # Verify session exists
    session = db.query(RecordingSession).filter(
        RecordingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording session not found"
        )

    return StreamConnectionInfo(
        session_id=session.id,
        websocket_url=f"/api/v1/stream/sessions/{session_id}/ws",
        supports_historic=True,
        mcp_format="sliples-stream-v1",
    )


# =============================================================================
# WebSocket Stream Endpoint
# =============================================================================

@router.websocket("/stream/sessions/{session_id}/ws")
async def stream_session_events(
    websocket: WebSocket,
    session_id: UUID,
    include_historic: bool = Query(True, description="Include historic events on connection"),
):
    """
    Stream recording events from a session in real-time via WebSocket.

    Connection flow:
    1. Client connects with optional ?include_historic=true/false
    2. Server sends 'connected' message with session info
    3. If include_historic=true, server sends all existing events as 'historic_event' messages
    4. Server sends 'historic_complete' message
    5. Server streams live events as they occur ('live_event' messages)
    6. Client sends 'ping' periodically for keepalive (server responds 'pong')

    Message types sent to client:
    - connected: Initial connection with session metadata
    - historic_event: Past event (if include_historic=true)
    - historic_complete: All historic events sent
    - live_event: Real-time event as it's recorded
    - session_stopped: Session was stopped
    - error: Error occurred

    Event format is MCP-optimized (compact, structured, token-efficient).
    """
    from app.database import SessionLocal

    session_id_str = str(session_id)

    # Verify session exists and get metadata
    db = SessionLocal()
    try:
        session = db.query(RecordingSession).filter(
            RecordingSession.id == session_id
        ).first()

        if not session:
            await websocket.close(code=4004, reason="Recording session not found")
            return

        # Count events
        event_count = db.query(RecordedEvent).filter(
            RecordedEvent.session_id == session_id
        ).count()

        session_info = {
            "id": str(session.id),
            "name": session.name,
            "url": session.url,
            "domain": session.domain,
            "status": session.status.value,
            "user_agent": session.user_agent,
            "viewport": f"{session.viewport_width}x{session.viewport_height}" if session.viewport_width else None,
            "created_at": session.created_at.isoformat(),
            "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
            "event_count": event_count,
        }
    finally:
        db.close()

    # Accept connection
    await connection_manager.connect(websocket, session_id_str)

    try:
        # Send connected message
        await websocket.send_json({
            "type": "connected",
            "format": "sliples-stream-v1",
            "session": session_info,
            "include_historic": include_historic,
        })

        # Send historic events if requested
        if include_historic:
            db = SessionLocal()
            try:
                events = db.query(RecordedEvent).filter(
                    RecordedEvent.session_id == session_id
                ).order_by(
                    RecordedEvent.timestamp.asc(),
                    RecordedEvent.sequence.asc()
                ).all()

                for event in events:
                    event_dict = {
                        "id": str(event.id),
                        "sequence": event.sequence,
                        "timestamp": event.timestamp.isoformat(),
                        "event_type": event.event_type,
                        "url": event.url,
                        "selector_css": event.selector_css,
                        "selector_xpath": event.selector_xpath,
                        "selector_text": event.selector_text,
                        "selector_test_id": event.selector_test_id,
                        "selector_aria": event.selector_aria,
                        "tag_name": event.tag_name,
                        "element_id": event.element_id,
                        "element_type": event.element_type,
                        "label_text": event.label_text,
                        "value": event.value,
                        "coordinates": event.coordinates,
                        "key_info": event.key_info,
                        "extra_data": event.extra_data,
                        "step_label": event.step_label,
                        "should_screenshot": event.should_screenshot,
                        "parameters": event.parameters,
                        "notes": event.notes,
                    }

                    await websocket.send_json({
                        "type": "historic_event",
                        "event": format_event_for_mcp(event_dict),
                    })

            finally:
                db.close()

            # Signal historic replay complete
            await websocket.send_json({
                "type": "historic_complete",
                "count": event_count,
            })

        # Subscribe to Redis pub/sub for live events
        redis = await get_redis_for_streaming()

        async def handle_redis_message(message: dict):
            """Forward Redis messages to WebSocket."""
            try:
                await websocket.send_json({
                    "type": "live_event",
                    "event": message,
                })
            except Exception:
                pass  # Connection closed, will be handled by disconnect

        # Start Redis subscription in background
        redis_task = asyncio.create_task(
            StreamEventBroadcaster.subscribe_to_session(
                redis,
                session_id_str,
                handle_redis_message,
            )
        )

        # Handle keepalive pings from client
        try:
            while True:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            pass
        finally:
            # Clean up
            redis_task.cancel()
            try:
                await redis_task
            except asyncio.CancelledError:
                pass
            await redis.close()

    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
    finally:
        await connection_manager.disconnect(websocket, session_id_str)


# =============================================================================
# Helper Endpoints for Stream Management
# =============================================================================

@router.get("/stream/stats")
async def get_stream_stats(
    _auth = Depends(get_api_key_or_user),
):
    """
    Get statistics about active streams.

    Returns:
    - Total active sessions
    - Total WebSocket connections
    - Sessions by domain
    """
    session_ids = connection_manager.get_active_session_ids()

    # Get session details from DB
    from app.database import SessionLocal
    db = SessionLocal()

    try:
        sessions = db.query(RecordingSession).filter(
            RecordingSession.id.in_([UUID(sid) for sid in session_ids])
        ).all()

        domain_counts = {}
        for session in sessions:
            domain = session.domain or "unknown"
            domain_counts[domain] = domain_counts.get(domain, 0) + connection_manager.get_connection_count(str(session.id))

        total_connections = sum(
            connection_manager.get_connection_count(sid)
            for sid in session_ids
        )

        return {
            "active_sessions": len(session_ids),
            "total_connections": total_connections,
            "sessions_by_domain": domain_counts,
        }
    finally:
        db.close()


@router.post("/stream/sessions/{session_id}/broadcast")
async def broadcast_to_session(
    session_id: UUID,
    message: dict,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    Broadcast a custom message to all clients streaming this session.

    Useful for:
    - Sending notifications to watchers
    - Coordinating between multiple viewers
    - Injecting custom events into the stream

    The message will be wrapped in a 'custom' type envelope.
    """
    # Verify session exists
    session = db.query(RecordingSession).filter(
        RecordingSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording session not found"
        )

    # Broadcast via connection manager
    await connection_manager.broadcast_to_session(
        str(session_id),
        {
            "type": "custom",
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
        }
    )

    return {
        "broadcasted": True,
        "session_id": str(session_id),
        "recipients": connection_manager.get_connection_count(str(session_id)),
    }
