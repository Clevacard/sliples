"""Recording session endpoints for UI event capture."""

from datetime import datetime
from typing import Optional
from uuid import UUID

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, FileResponse
from redis.asyncio import Redis as AsyncRedis
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecordingSession, RecordedEvent, RecordingStatus, Project, ApiKey, PlaybackRun, PlaybackStepResult, PlaybackStatus, PlaybackStepStatus, Environment, BrowserConfig, AllowedDomain
from app.api.deps import get_api_key, verify_project_access, get_validated_api_key, get_api_key_or_user, get_domain_or_api_key_auth


router = APIRouter()


# Request/Response schemas
class RecordingStartRequest(BaseModel):
    """Request to start a new recording session."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str
    user_agent: Optional[str] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None


class RecordingStartResponse(BaseModel):
    """Response after starting a recording session."""
    session_id: UUID
    name: str
    status: str

    class Config:
        from_attributes = True


class EventCoordinates(BaseModel):
    """Mouse coordinates for click events."""
    x: int
    y: int


class KeyInfo(BaseModel):
    """Keyboard event information."""
    key: Optional[str] = None
    code: Optional[str] = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    meta: bool = False


class RecordedEventCreate(BaseModel):
    """Schema for a single recorded event."""
    sequence: int
    timestamp: datetime
    event_type: str  # click, input, select, navigation, submit, focus, blur, scroll, keydown

    # Selectors (multiple strategies)
    selector_css: Optional[str] = None
    selector_xpath: Optional[str] = None
    selector_text: Optional[str] = None
    selector_test_id: Optional[str] = None
    selector_aria: Optional[str] = None

    # Element metadata
    tag_name: Optional[str] = None
    element_id: Optional[str] = None
    element_classes: Optional[str] = None  # JSON array
    element_name: Optional[str] = None
    element_type: Optional[str] = None
    element_role: Optional[str] = None
    label_text: Optional[str] = None
    placeholder: Optional[str] = None

    # Event data
    value: Optional[str] = None
    url: Optional[str] = None
    coordinates: Optional[EventCoordinates] = None
    key_info: Optional[KeyInfo] = None
    extra_data: Optional[dict] = None


class EventsBatchRequest(BaseModel):
    """Batch of events to record."""
    events: list[RecordedEventCreate]


class RecordingSessionResponse(BaseModel):
    """Full recording session with events."""
    id: UUID
    project_id: Optional[UUID]
    name: str
    url: str
    status: str
    user_agent: Optional[str]
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    domain: Optional[str] = None
    client_ip: Optional[str] = None
    created_at: datetime
    stopped_at: Optional[datetime]
    event_count: int

    class Config:
        from_attributes = True


class SessionRenameRequest(BaseModel):
    """Request to rename a recording session."""
    name: str = Field(..., min_length=1, max_length=255)


class AllowedDomainCreate(BaseModel):
    """Request to create an allowed domain."""
    domain: str = Field(..., min_length=1, max_length=255)
    is_enabled: bool = True


class AllowedDomainUpdate(BaseModel):
    """Request to update an allowed domain."""
    domain: Optional[str] = None
    is_enabled: Optional[bool] = None


class AllowedDomainResponse(BaseModel):
    """Response for an allowed domain."""
    id: UUID
    project_id: UUID
    domain: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionExportRequest(BaseModel):
    """Request to export sessions for AI analysis."""
    session_ids: list[UUID]


class RecordedEventResponse(BaseModel):
    """Response schema for a recorded event."""
    id: UUID
    sequence: int
    timestamp: datetime
    event_type: str
    selector_css: Optional[str]
    selector_xpath: Optional[str]
    selector_text: Optional[str]
    selector_test_id: Optional[str]
    selector_aria: Optional[str]
    tag_name: Optional[str]
    element_id: Optional[str]
    label_text: Optional[str]
    value: Optional[str]
    url: Optional[str]
    coordinates: Optional[dict]
    key_info: Optional[dict]
    extra_data: Optional[dict] = None
    # User annotations
    step_label: Optional[str]
    should_screenshot: bool
    parameters: Optional[dict]
    notes: Optional[str]

    class Config:
        from_attributes = True


class EventMetadataUpdate(BaseModel):
    """Request schema for updating event metadata."""
    step_label: Optional[str] = None
    should_screenshot: Optional[bool] = None
    parameters: Optional[dict] = None
    notes: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/recorder/sessions", response_model=RecordingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_recording(
    request: RecordingStartRequest,
    raw_request: Request = None,
    db: Session = Depends(get_db),
    auth_info: tuple = Depends(get_domain_or_api_key_auth),
):
    """
    Start a new recording session.

    Accepts both API key and domain-based auth (Origin header).
    Returns a session_id that should be used for all subsequent event submissions.
    """
    project_id, auth_method = auth_info

    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication must be scoped to a project",
        )

    # Extract domain and client IP from request
    origin = None
    client_ip = None
    if raw_request:
        origin_header = raw_request.headers.get("origin") or raw_request.headers.get("referer")
        if origin_header:
            from urllib.parse import urlparse
            origin = urlparse(origin_header).hostname
        forwarded = raw_request.headers.get("x-forwarded-for", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (raw_request.client.host if raw_request.client else None)

    session = RecordingSession(
        project_id=project_id,
        name=request.name,
        url=request.url,
        user_agent=request.user_agent,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
        domain=origin,
        client_ip=client_ip,
        status=RecordingStatus.recording,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return RecordingStartResponse(
        session_id=session.id,
        name=session.name,
        status=session.status.value,
    )


@router.post("/recorder/sessions/{session_id}/events", status_code=status.HTTP_201_CREATED)
async def record_events(
    session_id: UUID,
    request: EventsBatchRequest,
    db: Session = Depends(get_db),
    auth_info: tuple = Depends(get_domain_or_api_key_auth),
):
    """
    Record a batch of UI events for a session.

    Events are batched by the recorder snippet and sent periodically.
    """
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    if session.status != RecordingStatus.recording:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recording session is not active")

    for event_data in request.events:
        event = RecordedEvent(
            session_id=session_id,
            sequence=event_data.sequence,
            timestamp=event_data.timestamp,
            event_type=event_data.event_type,
            selector_css=event_data.selector_css,
            selector_xpath=event_data.selector_xpath,
            selector_text=event_data.selector_text,
            selector_test_id=event_data.selector_test_id,
            selector_aria=event_data.selector_aria,
            tag_name=event_data.tag_name,
            element_id=event_data.element_id,
            element_classes=event_data.element_classes,
            element_name=event_data.element_name,
            element_type=event_data.element_type,
            element_role=event_data.element_role,
            label_text=event_data.label_text,
            placeholder=event_data.placeholder,
            value=event_data.value,
            url=event_data.url,
            coordinates=event_data.coordinates.model_dump() if event_data.coordinates else None,
            key_info=event_data.key_info.model_dump() if event_data.key_info else None,
            extra_data=event_data.extra_data,
        )
        db.add(event)

    db.commit()
    return {"recorded": len(request.events)}


@router.post("/recorder/sessions/{session_id}/stop", response_model=RecordingSessionResponse)
async def stop_recording(
    session_id: UUID,
    db: Session = Depends(get_db),
    auth_info: tuple = Depends(get_domain_or_api_key_auth),
):
    """Stop a recording session."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    session.status = RecordingStatus.stopped
    session.stopped_at = datetime.utcnow()
    db.commit()
    db.refresh(session)

    event_count = db.query(RecordedEvent).filter(RecordedEvent.session_id == session_id).count()

    return RecordingSessionResponse(
        id=session.id,
        project_id=session.project_id,
        name=session.name,
        url=session.url,
        status=session.status.value,
        user_agent=session.user_agent,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        domain=session.domain,
        client_ip=session.client_ip,
        created_at=session.created_at,
        stopped_at=session.stopped_at,
        event_count=event_count,
    )


@router.get("/recorder/sessions", response_model=list[RecordingSessionResponse])
async def list_recordings(
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """List all recording sessions, optionally filtered by project."""
    query = db.query(RecordingSession)
    if project:
        query = query.filter(RecordingSession.project_id == project.id)

    sessions = query.order_by(RecordingSession.created_at.desc()).all()

    result = []
    for session in sessions:
        event_count = db.query(RecordedEvent).filter(RecordedEvent.session_id == session.id).count()
        result.append(RecordingSessionResponse(
            id=session.id,
            project_id=session.project_id,
            name=session.name,
            url=session.url,
            status=session.status.value,
            user_agent=session.user_agent,
            viewport_width=session.viewport_width,
            viewport_height=session.viewport_height,
            domain=session.domain,
            client_ip=session.client_ip,
            created_at=session.created_at,
            stopped_at=session.stopped_at,
            event_count=event_count,
        ))
    return result


@router.get("/recorder/sessions/{session_id}", response_model=RecordingSessionResponse)
async def get_recording(
    session_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get a recording session by ID."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    event_count = db.query(RecordedEvent).filter(RecordedEvent.session_id == session_id).count()

    return RecordingSessionResponse(
        id=session.id,
        project_id=session.project_id,
        name=session.name,
        url=session.url,
        status=session.status.value,
        user_agent=session.user_agent,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        domain=session.domain,
        client_ip=session.client_ip,
        created_at=session.created_at,
        stopped_at=session.stopped_at,
        event_count=event_count,
    )


@router.get("/recorder/sessions/{session_id}/events", response_model=list[RecordedEventResponse])
async def get_recording_events(
    session_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get all events for a recording session."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    events = db.query(RecordedEvent).filter(
        RecordedEvent.session_id == session_id
    ).order_by(RecordedEvent.sequence).all()

    return [
        RecordedEventResponse(
            id=e.id,
            sequence=e.sequence,
            timestamp=e.timestamp,
            event_type=e.event_type,
            selector_css=e.selector_css,
            selector_xpath=e.selector_xpath,
            selector_text=e.selector_text,
            selector_test_id=e.selector_test_id,
            selector_aria=e.selector_aria,
            tag_name=e.tag_name,
            element_id=e.element_id,
            label_text=e.label_text,
            value=e.value,
            url=e.url,
            coordinates=e.coordinates,
            key_info=e.key_info,
            extra_data=e.extra_data,
            step_label=e.step_label,
            should_screenshot=e.should_screenshot or False,
            parameters=e.parameters,
            notes=e.notes,
        )
        for e in events
    ]


@router.patch("/recorder/sessions/{session_id}/events/{event_id}", response_model=RecordedEventResponse)
async def update_event_metadata(
    session_id: UUID,
    event_id: UUID,
    data: EventMetadataUpdate,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Update event annotations (label, screenshot flag, parameters, notes)."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    event = db.query(RecordedEvent).filter(
        RecordedEvent.id == event_id,
        RecordedEvent.session_id == session_id,
    ).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Update fields that are provided
    if data.step_label is not None:
        event.step_label = data.step_label
    if data.should_screenshot is not None:
        event.should_screenshot = data.should_screenshot
    if data.parameters is not None:
        event.parameters = data.parameters
    if data.notes is not None:
        event.notes = data.notes

    db.commit()
    db.refresh(event)

    return RecordedEventResponse(
        id=event.id,
        sequence=event.sequence,
        timestamp=event.timestamp,
        event_type=event.event_type,
        selector_css=event.selector_css,
        selector_xpath=event.selector_xpath,
        selector_text=event.selector_text,
        selector_test_id=event.selector_test_id,
        selector_aria=event.selector_aria,
        tag_name=event.tag_name,
        element_id=event.element_id,
        label_text=event.label_text,
        value=event.value,
        url=event.url,
        coordinates=event.coordinates,
        key_info=event.key_info,
        extra_data=event.extra_data,
        step_label=event.step_label,
        should_screenshot=event.should_screenshot or False,
        parameters=event.parameters,
        notes=event.notes,
    )


@router.patch("/recorder/sessions/{session_id}", response_model=RecordingSessionResponse)
async def rename_session(
    session_id: UUID,
    request: SessionRenameRequest,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Rename a recording session."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    session.name = request.name
    db.commit()
    db.refresh(session)

    event_count = db.query(RecordedEvent).filter(RecordedEvent.session_id == session_id).count()

    return RecordingSessionResponse(
        id=session.id,
        project_id=session.project_id,
        name=session.name,
        url=session.url,
        status=session.status.value,
        user_agent=session.user_agent,
        viewport_width=session.viewport_width,
        viewport_height=session.viewport_height,
        domain=session.domain,
        client_ip=session.client_ip,
        created_at=session.created_at,
        stopped_at=session.stopped_at,
        event_count=event_count,
    )


@router.delete("/recorder/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(
    session_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Delete a recording session and all its events."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    db.delete(session)
    db.commit()


# =============================================================================
# Session Export (AI-optimized format)
# =============================================================================


@router.post("/recorder/sessions/export")
async def export_sessions(
    request: SessionExportRequest,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    Export one or more sessions in an AI-analysis-optimized format.

    Returns a structured JSON with session metadata and a compact event log
    designed for token-efficient LLM consumption.
    """
    sessions_data = []

    for sid in request.session_ids:
        session = db.query(RecordingSession).filter(RecordingSession.id == sid).first()
        if not session:
            continue

        events = db.query(RecordedEvent).filter(
            RecordedEvent.session_id == sid
        ).order_by(RecordedEvent.sequence).all()

        compact_events = []
        for e in events:
            entry = {
                "seq": e.sequence,
                "t": e.timestamp.isoformat(),
                "type": e.event_type,
            }
            if e.url:
                entry["url"] = e.url
            if e.selector_test_id:
                entry["target"] = f"[data-testid={e.selector_test_id}]"
            elif e.selector_aria:
                entry["target"] = f"[aria-label={e.selector_aria}]"
            elif e.element_id:
                entry["target"] = f"#{e.element_id}"
            elif e.selector_css:
                entry["target"] = e.selector_css
            if e.value:
                entry["value"] = e.value[:200]
            if e.key_info:
                entry["key"] = e.key_info
            if e.coordinates:
                entry["pos"] = e.coordinates
            if e.extra_data:
                entry["extra"] = e.extra_data

            compact_events.append(entry)

        sessions_data.append({
            "id": str(session.id),
            "name": session.name,
            "url": session.url,
            "domain": session.domain,
            "user_agent": session.user_agent,
            "viewport": f"{session.viewport_width}x{session.viewport_height}" if session.viewport_width else None,
            "started": session.created_at.isoformat(),
            "stopped": session.stopped_at.isoformat() if session.stopped_at else None,
            "events": compact_events,
        })

    return {
        "format": "sliples-session-export-v1",
        "exported_at": datetime.utcnow().isoformat(),
        "session_count": len(sessions_data),
        "sessions": sessions_data,
    }


# =============================================================================
# Domain Management
# =============================================================================


@router.get("/projects/{project_id}/domains", response_model=list[AllowedDomainResponse])
async def list_domains(
    project_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """List all allowed domains for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    domains = db.query(AllowedDomain).filter(
        AllowedDomain.project_id == project_id
    ).order_by(AllowedDomain.created_at.desc()).all()

    return domains


@router.post("/projects/{project_id}/domains", response_model=AllowedDomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(
    project_id: UUID,
    request: AllowedDomainCreate,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Add a new allowed domain to a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    existing = db.query(AllowedDomain).filter(
        AllowedDomain.project_id == project_id,
        AllowedDomain.domain == request.domain,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Domain already exists for this project")

    domain = AllowedDomain(
        project_id=project_id,
        domain=request.domain,
        is_enabled=request.is_enabled,
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)

    return domain


@router.patch("/projects/{project_id}/domains/{domain_id}", response_model=AllowedDomainResponse)
async def update_domain(
    project_id: UUID,
    domain_id: UUID,
    request: AllowedDomainUpdate,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Update an allowed domain (edit domain name or toggle enabled)."""
    domain = db.query(AllowedDomain).filter(
        AllowedDomain.id == domain_id,
        AllowedDomain.project_id == project_id,
    ).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    if request.domain is not None:
        domain.domain = request.domain
    if request.is_enabled is not None:
        domain.is_enabled = request.is_enabled

    db.commit()
    db.refresh(domain)

    return domain


@router.delete("/projects/{project_id}/domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    project_id: UUID,
    domain_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Delete an allowed domain from a project."""
    domain = db.query(AllowedDomain).filter(
        AllowedDomain.id == domain_id,
        AllowedDomain.project_id == project_id,
    ).first()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    db.delete(domain)
    db.commit()


@router.get("/recorder/ignored-domains")
async def get_ignored_domains(
    _auth = Depends(get_api_key_or_user),
):
    """Get all ignored domains with their request counts."""
    import redis
    from app.config import get_settings
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    data = r.hgetall("sliples:ignored_domains")
    r.close()
    return [
        {"domain": k.decode(), "count": int(v)}
        for k, v in sorted(data.items(), key=lambda x: int(x[1]), reverse=True)
    ]


@router.delete("/recorder/ignored-domains/{domain}", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_ignored_domain(
    domain: str,
    _auth = Depends(get_api_key_or_user),
):
    """Remove a domain from the ignored list."""
    import redis
    from app.config import get_settings
    settings = get_settings()
    r = redis.from_url(settings.redis_url)
    r.hdel("sliples:ignored_domains", domain)
    r.close()


# =============================================================================
# Playback Endpoints
# =============================================================================


class PlaybackStartRequest(BaseModel):
    """Request to start a playback run."""
    environment_id: UUID
    browser: str = "chrome"
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None


class PlaybackRunResponse(BaseModel):
    """Response for a playback run."""
    id: UUID
    session_id: UUID
    environment_id: UUID
    browser: str
    status: str
    viewport_width: Optional[int]
    viewport_height: Optional[int]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    progress_message: Optional[str]
    total_steps: int
    passed_steps: int
    failed_steps: int
    created_at: datetime

    class Config:
        from_attributes = True


class PlaybackStepResultResponse(BaseModel):
    """Response for a playback step result."""
    id: UUID
    event_id: UUID
    sequence: int
    status: str
    duration_ms: Optional[int]
    error_message: Optional[str]
    selector_used: Optional[str]
    screenshot_url: Optional[str]

    class Config:
        from_attributes = True


@router.post("/recorder/sessions/{session_id}/playback", response_model=PlaybackRunResponse, status_code=status.HTTP_201_CREATED)
async def start_playback(
    session_id: UUID,
    request: PlaybackStartRequest,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    Start a playback run for a recording session.

    This will queue the playback for execution in a Celery worker.
    """
    from app.workers.tasks import execute_playback

    # Verify session exists
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    # Verify environment exists and has the requested browser
    environment = db.query(Environment).filter(Environment.id == request.environment_id).first()
    if not environment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    browser_config = db.query(BrowserConfig).filter(
        BrowserConfig.environment_id == environment.id,
        BrowserConfig.browser == request.browser
    ).first()
    if not browser_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Browser '{request.browser}' not configured for environment '{environment.name}'"
        )

    # Create playback run
    playback_run = PlaybackRun(
        session_id=session_id,
        environment_id=request.environment_id,
        browser=request.browser,
        viewport_width=request.viewport_width or session.viewport_width,
        viewport_height=request.viewport_height or session.viewport_height,
        status=PlaybackStatus.pending,
    )
    db.add(playback_run)
    db.commit()
    db.refresh(playback_run)

    # Queue for execution
    execute_playback.delay(str(playback_run.id))

    return PlaybackRunResponse(
        id=playback_run.id,
        session_id=playback_run.session_id,
        environment_id=playback_run.environment_id,
        browser=playback_run.browser,
        status=playback_run.status.value,
        viewport_width=playback_run.viewport_width,
        viewport_height=playback_run.viewport_height,
        started_at=playback_run.started_at,
        finished_at=playback_run.finished_at,
        duration_ms=playback_run.duration_ms,
        progress_message=playback_run.progress_message,
        total_steps=playback_run.total_steps,
        passed_steps=playback_run.passed_steps,
        failed_steps=playback_run.failed_steps,
        created_at=playback_run.created_at,
    )


@router.get("/recorder/sessions/{session_id}/playback", response_model=list[PlaybackRunResponse])
async def list_playback_runs(
    session_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """List all playback runs for a recording session."""
    runs = db.query(PlaybackRun).filter(
        PlaybackRun.session_id == session_id
    ).order_by(PlaybackRun.created_at.desc()).all()

    return [
        PlaybackRunResponse(
            id=run.id,
            session_id=run.session_id,
            environment_id=run.environment_id,
            browser=run.browser,
            status=run.status.value,
            viewport_width=run.viewport_width,
            viewport_height=run.viewport_height,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_ms=run.duration_ms,
            progress_message=run.progress_message,
            total_steps=run.total_steps,
            passed_steps=run.passed_steps,
            failed_steps=run.failed_steps,
            created_at=run.created_at,
        )
        for run in runs
    ]


@router.get("/recorder/playback/{playback_id}", response_model=PlaybackRunResponse)
async def get_playback_run(
    playback_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get a playback run by ID."""
    run = db.query(PlaybackRun).filter(PlaybackRun.id == playback_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playback run not found")

    return PlaybackRunResponse(
        id=run.id,
        session_id=run.session_id,
        environment_id=run.environment_id,
        browser=run.browser,
        status=run.status.value,
        viewport_width=run.viewport_width,
        viewport_height=run.viewport_height,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_ms=run.duration_ms,
        progress_message=run.progress_message,
        total_steps=run.total_steps,
        passed_steps=run.passed_steps,
        failed_steps=run.failed_steps,
        created_at=run.created_at,
    )


@router.get("/recorder/playback/{playback_id}/results", response_model=list[PlaybackStepResultResponse])
async def get_playback_results(
    playback_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get step results for a playback run."""
    results = db.query(PlaybackStepResult).filter(
        PlaybackStepResult.playback_run_id == playback_id
    ).order_by(PlaybackStepResult.sequence).all()

    return [
        PlaybackStepResultResponse(
            id=r.id,
            event_id=r.event_id,
            sequence=r.sequence,
            status=r.status.value,
            duration_ms=r.duration_ms,
            error_message=r.error_message,
            selector_used=r.selector_used,
            screenshot_url=r.screenshot_url,
        )
        for r in results
    ]


@router.get("/recorder/playback/{playback_id}/report")
async def get_playback_report(
    playback_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get HTML report for a playback run."""
    run = db.query(PlaybackRun).filter(PlaybackRun.id == playback_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playback run not found")

    if not run.report_html:
        # Generate on demand if not present
        from app.services.playback_report_generator import PlaybackReportGenerator
        generator = PlaybackReportGenerator(db)
        generator.save_report(str(playback_id))
        db.refresh(run)

    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=run.report_html or "<html><body>Report not available</body></html>")


# =============================================================================
# WebSocket for live playback updates
# =============================================================================

@router.websocket("/ws/playback/{playback_id}")
async def websocket_playback_updates(
    websocket: WebSocket,
    playback_id: UUID,
):
    """
    WebSocket endpoint for real-time playback updates.

    Connects to Redis pub/sub to receive updates from the Celery worker
    and forwards them to the client in real-time.

    Message types sent to client:
    - "connected": Initial connection confirmation with current playback state
    - "status": Progress update (status, current step, passed/failed counts)
    - "step_result": Individual step completion with event details
    - "completed": Playback finished
    - "error": If something goes wrong

    The client should send "ping" messages periodically for keepalive.
    """
    from app.database import SessionLocal
    from app.services.websocket_pubsub import get_playback_channel, get_redis_async

    playback_id_str = str(playback_id)

    # Verify playback run exists
    db = SessionLocal()
    try:
        run = db.query(PlaybackRun).filter(PlaybackRun.id == playback_id).first()
        if not run:
            await websocket.close(code=4004, reason="Playback run not found")
            return

        # Get current state to send on connection
        initial_state = {
            "id": playback_id_str,
            "status": run.status.value,
            "progress_message": run.progress_message,
            "total_steps": run.total_steps,
            "passed_steps": run.passed_steps,
            "failed_steps": run.failed_steps,
        }
    finally:
        db.close()

    await websocket.accept()

    # Send initial state
    await websocket.send_json({
        "type": "connected",
        "data": initial_state,
    })

    # If already completed, close connection
    if initial_state["status"] in ["passed", "failed"]:
        await websocket.send_json({
            "type": "completed",
            "data": initial_state,
        })
        await websocket.close()
        return

    # Subscribe to Redis channel for updates
    redis: Optional[AsyncRedis] = None
    pubsub = None

    async def redis_listener():
        nonlocal redis, pubsub
        try:
            redis = await get_redis_async()
            pubsub = redis.pubsub()
            channel = get_playback_channel(playback_id_str)
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)

                        if data.get("type") == "completed":
                            break
                    except json.JSONDecodeError:
                        pass
                    except Exception:
                        break
        except asyncio.CancelledError:
            pass
        finally:
            if pubsub:
                await pubsub.unsubscribe(get_playback_channel(playback_id_str))
                await pubsub.close()
            if redis:
                await redis.close()

    async def keepalive_handler():
        try:
            while True:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            pass
        except asyncio.CancelledError:
            pass

    # Run both tasks concurrently
    listener_task = asyncio.create_task(redis_listener())
    keepalive_task = asyncio.create_task(keepalive_handler())

    try:
        done, pending = await asyncio.wait(
            [listener_task, keepalive_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    except Exception:
        pass
    finally:
        listener_task.cancel()
        keepalive_task.cancel()


@router.get("/recorder/snippet.js", response_class=PlainTextResponse)
async def get_recorder_snippet(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    project_id: Optional[str] = None,
    mode: Optional[str] = None,
    response: Response = None,
):
    """
    Get the recorder JavaScript snippet.

    Supports two auth modes:
    - api_key mode: Pass api_key param, snippet sends X-API-Key header
    - domain mode: No api_key needed, server checks Origin header against allowed_domains

    Query params:
    - api_key: API key for authentication (optional if domain mode)
    - endpoint: Optional custom API endpoint (defaults to this server)
    - project_id: Optional project ID to associate recordings with
    - mode: "domain" for domain-based auth (no API key needed)
    """
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Cache-Control"] = "public, max-age=3600"

    auth_mode = mode or ("domain" if not api_key else "api_key")
    config = {
        "apiKey": api_key or "",
        "endpoint": endpoint or "/api/v1",
        "projectId": project_id,
        "authMode": auth_mode,
    }

    snippet = f"""// Sliples UI Recorder v2 - Domain-based auth + JS/Network error capture
(function() {{
  'use strict';

  const CONFIG = {json.dumps(config)};

  const SliplesRecorder = {{
    sessionId: null,
    events: [],
    sequence: 0,
    isRecording: false,
    flushInterval: null,

    getHeaders: function() {{
      const h = {{'Content-Type': 'application/json'}};
      if (CONFIG.authMode === 'api_key' && CONFIG.apiKey) h['X-API-Key'] = CONFIG.apiKey;
      return h;
    }},

    getCssSelector: function(el) {{
      if (!el || el === document.body) return 'body';
      if (el.id) return '#' + CSS.escape(el.id);
      const path = [];
      while (el && el !== document.body) {{
        let selector = el.tagName.toLowerCase();
        if (el.id) {{ selector = '#' + CSS.escape(el.id); path.unshift(selector); break; }}
        if (el.className && typeof el.className === 'string') {{
          const classes = el.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(hover|active|focus|ng-|\\d)/));
          if (classes.length) selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
        }}
        const parent = el.parentElement;
        if (parent) {{
          const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
          if (siblings.length > 1) selector += ':nth-of-type(' + (siblings.indexOf(el) + 1) + ')';
        }}
        path.unshift(selector);
        el = parent;
      }}
      return path.join(' > ');
    }},

    getXPath: function(el) {{
      if (!el) return '';
      if (el.id) return '//*[@id="' + el.id + '"]';
      const parts = [];
      while (el && el.nodeType === Node.ELEMENT_NODE) {{
        let index = 1, sibling = el.previousSibling;
        while (sibling) {{ if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === el.tagName) index++; sibling = sibling.previousSibling; }}
        parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
        el = el.parentNode;
      }}
      return '/' + parts.join('/');
    }},

    getLabelText: function(el) {{
      if (el.labels && el.labels.length) return el.labels[0].textContent.trim();
      const ariaLabel = el.getAttribute('aria-label');
      if (ariaLabel) return ariaLabel;
      const labelledBy = el.getAttribute('aria-labelledby');
      if (labelledBy) {{ const labelEl = document.getElementById(labelledBy); if (labelEl) return labelEl.textContent.trim(); }}
      const parentLabel = el.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      return null;
    }},

    getElementData: function(el) {{
      if (!el || !el.tagName) return {{}};
      return {{
        selector_css: this.getCssSelector(el),
        selector_xpath: this.getXPath(el),
        selector_text: el.textContent ? el.textContent.trim().substring(0, 100) : null,
        selector_test_id: el.getAttribute('data-testid') || el.getAttribute('data-test-id'),
        selector_aria: el.getAttribute('aria-label'),
        tag_name: el.tagName.toLowerCase(),
        element_id: el.id || null,
        element_classes: el.className && typeof el.className === 'string' ? JSON.stringify(el.className.split(/\\s+/).filter(Boolean)) : null,
        element_name: el.name || null,
        element_type: el.type || null,
        element_role: el.getAttribute('role'),
        label_text: this.getLabelText(el),
        placeholder: el.placeholder || null,
      }};
    }},

    record: function(type, el, extra) {{
      if (!this.isRecording) return;
      const event = {{
        sequence: this.sequence++,
        timestamp: new Date().toISOString(),
        event_type: type,
        url: window.location.href,
        ...this.getElementData(el),
        ...extra,
      }};
      this.events.push(event);
    }},

    flush: async function() {{
      if (!this.events.length || !this.sessionId) return;
      const batch = this.events.splice(0, this.events.length);
      try {{
        const resp = await fetch(CONFIG.endpoint + '/recorder/sessions/' + this.sessionId + '/events', {{
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({{ events: batch }}),
        }});
        if (!resp.ok) this.events.unshift(...batch);
      }} catch (e) {{
        this.events.unshift(...batch);
      }}
    }},

    handleClick: function(e) {{
      const rect = e.target.getBoundingClientRect();
      this.record('click', e.target, {{ coordinates: {{ x: Math.round(e.clientX - rect.left), y: Math.round(e.clientY - rect.top) }} }});
    }},

    handleInput: function(e) {{
      clearTimeout(e.target._sliplesTimeout);
      e.target._sliplesTimeout = setTimeout(() => {{
        this.record('input', e.target, {{ value: e.target.type === 'password' ? '***' : e.target.value }});
      }}, 500);
    }},

    handleChange: function(e) {{ this.record('change', e.target, {{ value: e.target.value }}); }},
    handleSubmit: function(e) {{ this.record('submit', e.target); }},

    handleKeydown: function(e) {{
      if (['Enter', 'Tab', 'Escape', 'Backspace', 'Delete'].includes(e.key) || e.ctrlKey || e.metaKey) {{
        this.record('keydown', e.target, {{ key_info: {{ key: e.key, code: e.code, ctrl: e.ctrlKey, alt: e.altKey, shift: e.shiftKey, meta: e.metaKey }} }});
      }}
    }},

    // JS error and network error capture
    setupErrorCapture: function() {{
      // JS exceptions
      this._onError = (event) => {{
        this.record('js_error', null, {{
          extra_data: {{
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error ? event.error.stack : null,
          }}
        }});
      }};
      window.addEventListener('error', this._onError);

      // Unhandled promise rejections
      this._onUnhandledRejection = (event) => {{
        this.record('js_error', null, {{
          extra_data: {{
            message: 'Unhandled Promise Rejection',
            reason: event.reason ? (event.reason.message || String(event.reason)) : 'unknown',
            stack: event.reason && event.reason.stack ? event.reason.stack : null,
          }}
        }});
      }};
      window.addEventListener('unhandledrejection', this._onUnhandledRejection);

      // Network error capture via fetch monkey-patch
      const origFetch = window.fetch;
      const self = this;
      window.fetch = function() {{
        const url = arguments[0] instanceof Request ? arguments[0].url : String(arguments[0]);
        // Skip our own requests
        if (url.includes('/recorder/sessions/')) return origFetch.apply(this, arguments);
        return origFetch.apply(this, arguments).then(resp => {{
          if (!resp.ok && resp.status >= 400) {{
            self.record('network_error', null, {{
              extra_data: {{ url: url, status: resp.status, statusText: resp.statusText, method: (arguments[1] && arguments[1].method) || 'GET' }}
            }});
          }}
          return resp;
        }}).catch(err => {{
          self.record('network_error', null, {{
            extra_data: {{ url: url, error: err.message, method: (arguments[1] && arguments[1].method) || 'GET' }}
          }});
          throw err;
        }});
      }};
      this._origFetch = origFetch;

      // XHR error capture
      const origXHROpen = XMLHttpRequest.prototype.open;
      const origXHRSend = XMLHttpRequest.prototype.send;
      XMLHttpRequest.prototype.open = function(method, url) {{
        this._sliplesMethod = method;
        this._sliplesUrl = url;
        return origXHROpen.apply(this, arguments);
      }};
      XMLHttpRequest.prototype.send = function() {{
        const xhr = this;
        xhr.addEventListener('loadend', function() {{
          if (xhr._sliplesUrl && !xhr._sliplesUrl.includes('/recorder/sessions/') && xhr.status >= 400) {{
            self.record('network_error', null, {{
              extra_data: {{ url: xhr._sliplesUrl, status: xhr.status, statusText: xhr.statusText, method: xhr._sliplesMethod }}
            }});
          }}
        }});
        xhr.addEventListener('error', function() {{
          if (xhr._sliplesUrl && !xhr._sliplesUrl.includes('/recorder/sessions/')) {{
            self.record('network_error', null, {{
              extra_data: {{ url: xhr._sliplesUrl, error: 'Network error', method: xhr._sliplesMethod }}
            }});
          }}
        }});
        return origXHRSend.apply(this, arguments);
      }};
      this._origXHROpen = origXHROpen;
      this._origXHRSend = origXHRSend;
    }},

    teardownErrorCapture: function() {{
      window.removeEventListener('error', this._onError);
      window.removeEventListener('unhandledrejection', this._onUnhandledRejection);
      if (this._origFetch) window.fetch = this._origFetch;
      if (this._origXHROpen) XMLHttpRequest.prototype.open = this._origXHROpen;
      if (this._origXHRSend) XMLHttpRequest.prototype.send = this._origXHRSend;
    }},

    start: async function(name) {{
      if (this.isRecording) return;
      const sessionName = name || 'Recording ' + new Date().toLocaleString();
      try {{
        const resp = await fetch(CONFIG.endpoint + '/recorder/sessions', {{
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify({{
            name: sessionName,
            url: window.location.href,
            user_agent: navigator.userAgent,
            viewport_width: window.innerWidth,
            viewport_height: window.innerHeight,
          }}),
        }});
        if (!resp.ok) throw new Error('Failed to start session: ' + resp.status);
        const data = await resp.json();
        this.sessionId = data.session_id;
        this.isRecording = true;
        this.sequence = 0;
        this.events = [];

        document.addEventListener('click', this._handleClick, true);
        document.addEventListener('input', this._handleInput, true);
        document.addEventListener('change', this._handleChange, true);
        document.addEventListener('submit', this._handleSubmit, true);
        document.addEventListener('keydown', this._handleKeydown, true);

        this._navObserver = new MutationObserver(() => {{
          if (this._lastUrl !== window.location.href) {{
            this._lastUrl = window.location.href;
            this.record('navigation', null, {{ url: window.location.href }});
          }}
        }});
        this._navObserver.observe(document.body, {{ childList: true, subtree: true }});
        this._lastUrl = window.location.href;

        this.setupErrorCapture();
        this.flushInterval = setInterval(() => this.flush(), 3000);

        console.log('[Sliples] Recording started. Session:', this.sessionId);
      }} catch (e) {{
        console.error('[Sliples] Failed to start recording:', e);
      }}
    }},

    stop: async function() {{
      if (!this.isRecording) return;
      this.isRecording = false;

      document.removeEventListener('click', this._handleClick, true);
      document.removeEventListener('input', this._handleInput, true);
      document.removeEventListener('change', this._handleChange, true);
      document.removeEventListener('submit', this._handleSubmit, true);
      document.removeEventListener('keydown', this._handleKeydown, true);
      if (this._navObserver) this._navObserver.disconnect();
      this.teardownErrorCapture();
      clearInterval(this.flushInterval);

      await this.flush();

      try {{
        const resp = await fetch(CONFIG.endpoint + '/recorder/sessions/' + this.sessionId + '/stop', {{
          method: 'POST',
          headers: this.getHeaders(),
        }});
        if (resp.ok) {{
          const data = await resp.json();
          console.log('[Sliples] Recording stopped. Events:', data.event_count);
        }}
      }} catch (e) {{
        console.error('[Sliples] Failed to stop recording:', e);
      }}
      this.sessionId = null;
    }},

    init: function() {{
      this._handleClick = this.handleClick.bind(this);
      this._handleInput = this.handleInput.bind(this);
      this._handleChange = this.handleChange.bind(this);
      this._handleSubmit = this.handleSubmit.bind(this);
      this._handleKeydown = this.handleKeydown.bind(this);
      return this;
    }},
  }}.init();

  window.SliplesRecorder = SliplesRecorder;
  console.log('[Sliples] Recorder loaded. Call SliplesRecorder.start("Test Name") to begin.');
}})();
"""
    return snippet


# =============================================================================
# AI Diagnosis
# =============================================================================


class DiagnoseRequest(BaseModel):
    """Request for AI diagnosis of a failed step."""
    step_result_id: Optional[UUID] = None  # For playback step
    test_result_id: Optional[UUID] = None  # For test run result


class DiagnoseResponse(BaseModel):
    """Response from AI diagnosis."""
    diagnosis: str
    suggestions: list[str]
    confidence: Optional[float] = None
    raw_response: Optional[dict] = None


@router.post("/recorder/diagnose", response_model=DiagnoseResponse)
async def diagnose_failure(
    request: DiagnoseRequest,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """
    Send failure diagnostics to AI for analysis.

    Supports both playback step results and test run results.
    Collects console logs, DOM snapshot, screenshot, and error message
    and sends to the imperson.agantis.in service for diagnosis.
    """
    import httpx
    from app.config import get_settings
    from app.models import TestResult

    settings = get_settings()

    # Collect diagnostics based on request type
    diagnostics = {
        "error_message": None,
        "console_logs": None,
        "dom_snapshot": None,
        "page_url": None,
        "screenshot_url": None,
        "event_type": None,
        "selector_used": None,
    }

    if request.step_result_id:
        # Playback step result
        step = db.query(PlaybackStepResult).filter(
            PlaybackStepResult.id == request.step_result_id
        ).first()
        if not step:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step result not found")

        diagnostics["error_message"] = step.error_message
        diagnostics["console_logs"] = step.console_logs
        diagnostics["page_url"] = step.page_url
        diagnostics["screenshot_url"] = step.screenshot_url
        diagnostics["selector_used"] = step.selector_used

        # Get event type from related event
        if step.event:
            diagnostics["event_type"] = step.event.event_type

        # Load DOM snapshot from S3 if available
        if step.dom_snapshot_url:
            try:
                from app.services.s3_service import S3Service
                s3 = S3Service()
                presigned_url = s3.get_presigned_url(step.dom_snapshot_url, expires_in=300)
                async with httpx.AsyncClient() as client:
                    resp = await client.get(presigned_url)
                    if resp.status_code == 200:
                        diagnostics["dom_snapshot"] = resp.text[:50000]  # Limit DOM size
            except Exception as e:
                diagnostics["dom_snapshot"] = f"[Failed to load: {e}]"

    elif request.test_result_id:
        # Test run result
        result = db.query(TestResult).filter(
            TestResult.id == request.test_result_id
        ).first()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test result not found")

        diagnostics["error_message"] = result.error_message
        diagnostics["console_logs"] = result.console_logs
        diagnostics["page_url"] = result.page_url
        diagnostics["screenshot_url"] = result.screenshot_url

        # Load DOM snapshot from S3 if available
        if result.dom_snapshot_url:
            try:
                from app.services.s3_service import S3Service
                s3 = S3Service()
                presigned_url = s3.get_presigned_url(result.dom_snapshot_url, expires_in=300)
                async with httpx.AsyncClient() as client:
                    resp = await client.get(presigned_url)
                    if resp.status_code == 200:
                        diagnostics["dom_snapshot"] = resp.text[:50000]
            except Exception as e:
                diagnostics["dom_snapshot"] = f"[Failed to load: {e}]"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either step_result_id or test_result_id"
        )

    # Build prompt for AI
    prompt_parts = ["Diagnose this UI test failure:\n"]

    if diagnostics["error_message"]:
        prompt_parts.append(f"Error: {diagnostics['error_message']}\n")

    if diagnostics["event_type"]:
        prompt_parts.append(f"Action type: {diagnostics['event_type']}\n")

    if diagnostics["selector_used"]:
        prompt_parts.append(f"Selector used: {diagnostics['selector_used']}\n")

    if diagnostics["page_url"]:
        prompt_parts.append(f"Page URL: {diagnostics['page_url']}\n")

    if diagnostics["console_logs"]:
        prompt_parts.append(f"\nBrowser console logs:\n{diagnostics['console_logs'][:5000]}\n")

    if diagnostics["dom_snapshot"]:
        prompt_parts.append(f"\nDOM snapshot (truncated):\n{diagnostics['dom_snapshot'][:10000]}\n")

    prompt_parts.append("\nProvide a diagnosis of why this test failed and suggest fixes.")

    # Call imperson API
    payload = {
        "prompt": "".join(prompt_parts),
        "context": "UI automation test failure diagnosis",
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                settings.ai_diagnosis_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if resp.status_code != 200:
                return DiagnoseResponse(
                    diagnosis=f"AI service returned error: {resp.status_code}",
                    suggestions=["Check if the AI service is available", "Try again later"],
                    raw_response={"status": resp.status_code, "body": resp.text[:500]},
                )

            result = resp.json()

            # Parse response - adjust based on actual imperson API response format
            diagnosis = result.get("response") or result.get("text") or result.get("message") or str(result)
            suggestions = result.get("suggestions", [])

            # If no explicit suggestions, try to extract from diagnosis text
            if not suggestions and "suggest" in diagnosis.lower():
                # Simple extraction of numbered items
                import re
                suggestions = re.findall(r'\d+\.\s*([^\n]+)', diagnosis)

            return DiagnoseResponse(
                diagnosis=diagnosis,
                suggestions=suggestions[:5],
                confidence=result.get("confidence"),
                raw_response=result,
            )

    except httpx.TimeoutException:
        return DiagnoseResponse(
            diagnosis="AI service timed out",
            suggestions=["The AI service took too long to respond", "Try again or diagnose manually"],
        )
    except Exception as e:
        return DiagnoseResponse(
            diagnosis=f"Failed to contact AI service: {str(e)}",
            suggestions=["Check network connectivity", "Verify AI service URL in configuration"],
        )


@router.get("/recorder/playback/{playback_id}/results/{step_id}/diagnostics")
async def get_step_diagnostics(
    playback_id: UUID,
    step_id: UUID,
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
):
    """Get detailed diagnostics for a failed playback step."""
    step = db.query(PlaybackStepResult).filter(
        PlaybackStepResult.id == step_id,
        PlaybackStepResult.playback_run_id == playback_id,
    ).first()

    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step result not found")

    # Build diagnostics response
    diagnostics = {
        "id": str(step.id),
        "sequence": step.sequence,
        "status": step.status.value,
        "error_message": step.error_message,
        "selector_used": step.selector_used,
        "page_url": step.page_url,
        "screenshot_url": step.screenshot_url,
        "dom_snapshot_url": step.dom_snapshot_url,
        "console_logs": None,
    }

    # Parse console logs JSON if present
    if step.console_logs:
        try:
            diagnostics["console_logs"] = json.loads(step.console_logs)
        except json.JSONDecodeError:
            diagnostics["console_logs"] = step.console_logs

    return diagnostics


@router.options("/recorder/sessions")
@router.options("/recorder/sessions/{session_id}")
@router.options("/recorder/sessions/{session_id}/events")
@router.options("/recorder/sessions/{session_id}/events/{event_id}")
@router.options("/recorder/sessions/{session_id}/stop")
@router.options("/recorder/snippet.js")
async def options_recorder_endpoints(response: Response = None):
    """
    Handle CORS preflight requests for all recorder endpoints.

    This allows browsers to make cross-origin requests to recorder endpoints.
    """
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
        response.headers["Access-Control-Max-Age"] = "86400"
    return {"status": "ok"}
