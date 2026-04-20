"""Recording session endpoints for UI event capture."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecordingSession, RecordedEvent, RecordingStatus, Project, ApiKey, PlaybackRun, PlaybackStepResult, PlaybackStatus, PlaybackStepStatus, Environment, BrowserConfig
from app.api.deps import get_api_key, verify_project_access, get_validated_api_key, get_api_key_or_user


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
    created_at: datetime
    stopped_at: Optional[datetime]
    event_count: int

    class Config:
        from_attributes = True


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
    db: Session = Depends(get_db),
    _auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """
    Start a new recording session.

    Returns a session_id that should be used for all subsequent event submissions.
    The session is automatically associated with the API key's project.
    """
    project_id = api_key.project_id if api_key else None
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key must be scoped to a project to create recording sessions",
        )

    session = RecordingSession(
        project_id=project_id,
        name=request.name,
        url=request.url,
        user_agent=request.user_agent,
        viewport_width=request.viewport_width,
        viewport_height=request.viewport_height,
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
    _auth = Depends(get_api_key_or_user),
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
    _auth = Depends(get_api_key_or_user),
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
        step_label=event.step_label,
        should_screenshot=event.should_screenshot or False,
        parameters=event.parameters,
        notes=event.notes,
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


@router.get("/recorder/snippet.js", response_class=PlainTextResponse)
async def get_recorder_snippet(
    api_key: str,
    endpoint: Optional[str] = None,
    project_id: Optional[str] = None,
    response: Response = None,
):
    """
    Get the recorder JavaScript snippet configured for this API key.

    This endpoint is publicly accessible and can be embedded on any website.
    CORS headers are set to allow cross-origin loading.

    Query params:
    - api_key: Required API key for authentication
    - endpoint: Optional custom API endpoint (defaults to this server)
    - project_id: Optional project ID to associate recordings with
    """
    # Set CORS headers to allow loading from any origin
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Cache-Control"] = "public, max-age=3600"
    # Build the snippet with embedded configuration
    config = {
        "apiKey": api_key,
        "endpoint": endpoint or "/api/v1",
        "projectId": project_id,
    }

    snippet = f"""// Sliples UI Recorder - Paste this into your browser console or inject via script tag
(function() {{
  'use strict';

  const CONFIG = {config};

  const SliplesRecorder = {{
    sessionId: null,
    events: [],
    sequence: 0,
    isRecording: false,
    flushInterval: null,

    // Generate CSS selector for an element
    getCssSelector: function(el) {{
      if (!el || el === document.body) return 'body';
      if (el.id) return '#' + CSS.escape(el.id);

      const path = [];
      while (el && el !== document.body) {{
        let selector = el.tagName.toLowerCase();
        if (el.id) {{
          selector = '#' + CSS.escape(el.id);
          path.unshift(selector);
          break;
        }}
        if (el.className && typeof el.className === 'string') {{
          const classes = el.className.trim().split(/\\s+/).filter(c => c && !c.match(/^(hover|active|focus|ng-|\\d)/));
          if (classes.length) selector += '.' + classes.slice(0, 2).map(c => CSS.escape(c)).join('.');
        }}
        const parent = el.parentElement;
        if (parent) {{
          const siblings = Array.from(parent.children).filter(c => c.tagName === el.tagName);
          if (siblings.length > 1) {{
            const index = siblings.indexOf(el) + 1;
            selector += ':nth-of-type(' + index + ')';
          }}
        }}
        path.unshift(selector);
        el = parent;
      }}
      return path.join(' > ');
    }},

    // Generate XPath for an element
    getXPath: function(el) {{
      if (!el) return '';
      if (el.id) return '//*[@id="' + el.id + '"]';

      const parts = [];
      while (el && el.nodeType === Node.ELEMENT_NODE) {{
        let index = 1;
        let sibling = el.previousSibling;
        while (sibling) {{
          if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === el.tagName) index++;
          sibling = sibling.previousSibling;
        }}
        parts.unshift(el.tagName.toLowerCase() + '[' + index + ']');
        el = el.parentNode;
      }}
      return '/' + parts.join('/');
    }},

    // Get associated label text
    getLabelText: function(el) {{
      if (el.labels && el.labels.length) return el.labels[0].textContent.trim();
      const ariaLabel = el.getAttribute('aria-label');
      if (ariaLabel) return ariaLabel;
      const labelledBy = el.getAttribute('aria-labelledby');
      if (labelledBy) {{
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return labelEl.textContent.trim();
      }}
      // Check parent label
      const parentLabel = el.closest('label');
      if (parentLabel) return parentLabel.textContent.trim();
      return null;
    }},

    // Extract element metadata
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

    // Record an event
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
      console.log('[Sliples] Recorded:', type, event.selector_css || event.url);
    }},

    // Flush events to server
    flush: async function() {{
      if (!this.events.length || !this.sessionId) return;

      const batch = this.events.splice(0, this.events.length);
      try {{
        const resp = await fetch(CONFIG.endpoint + '/recorder/sessions/' + this.sessionId + '/events', {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
            'X-API-Key': CONFIG.apiKey,
          }},
          body: JSON.stringify({{ events: batch }}),
        }});
        if (!resp.ok) console.error('[Sliples] Failed to send events:', resp.status);
      }} catch (e) {{
        console.error('[Sliples] Network error:', e);
        // Put events back for retry
        this.events.unshift(...batch);
      }}
    }},

    // Event handlers
    handleClick: function(e) {{
      const rect = e.target.getBoundingClientRect();
      this.record('click', e.target, {{
        coordinates: {{ x: Math.round(e.clientX - rect.left), y: Math.round(e.clientY - rect.top) }},
      }});
    }},

    handleInput: function(e) {{
      // Debounce input events - only record final value
      clearTimeout(e.target._sliplesTimeout);
      e.target._sliplesTimeout = setTimeout(() => {{
        this.record('input', e.target, {{
          value: e.target.type === 'password' ? '***' : e.target.value,
        }});
      }}, 500);
    }},

    handleChange: function(e) {{
      this.record('change', e.target, {{
        value: e.target.value,
      }});
    }},

    handleSubmit: function(e) {{
      this.record('submit', e.target);
    }},

    handleKeydown: function(e) {{
      // Only record special keys (Enter, Tab, Escape, etc.)
      if (['Enter', 'Tab', 'Escape', 'Backspace', 'Delete'].includes(e.key) || e.ctrlKey || e.metaKey) {{
        this.record('keydown', e.target, {{
          key_info: {{
            key: e.key,
            code: e.code,
            ctrl: e.ctrlKey,
            alt: e.altKey,
            shift: e.shiftKey,
            meta: e.metaKey,
          }},
        }});
      }}
    }},

    // Start recording
    start: async function(name) {{
      if (this.isRecording) {{
        console.warn('[Sliples] Already recording');
        return;
      }}

      const sessionName = name || 'Recording ' + new Date().toLocaleString();

      try {{
        const url = CONFIG.endpoint + '/recorder/sessions' + (CONFIG.projectId ? '?project_id=' + CONFIG.projectId : '');
        const resp = await fetch(url, {{
          method: 'POST',
          headers: {{
            'Content-Type': 'application/json',
            'X-API-Key': CONFIG.apiKey,
          }},
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

        // Attach listeners
        document.addEventListener('click', this._handleClick, true);
        document.addEventListener('input', this._handleInput, true);
        document.addEventListener('change', this._handleChange, true);
        document.addEventListener('submit', this._handleSubmit, true);
        document.addEventListener('keydown', this._handleKeydown, true);

        // Record navigation events
        this._navObserver = new MutationObserver(() => {{
          if (this._lastUrl !== window.location.href) {{
            this._lastUrl = window.location.href;
            this.record('navigation', null, {{ url: window.location.href }});
          }}
        }});
        this._navObserver.observe(document.body, {{ childList: true, subtree: true }});
        this._lastUrl = window.location.href;

        // Flush periodically
        this.flushInterval = setInterval(() => this.flush(), 3000);

        console.log('[Sliples] Recording started. Session:', this.sessionId);
        console.log('[Sliples] Call SliplesRecorder.stop() to finish');

      }} catch (e) {{
        console.error('[Sliples] Failed to start recording:', e);
      }}
    }},

    // Stop recording
    stop: async function() {{
      if (!this.isRecording) {{
        console.warn('[Sliples] Not recording');
        return;
      }}

      this.isRecording = false;

      // Remove listeners
      document.removeEventListener('click', this._handleClick, true);
      document.removeEventListener('input', this._handleInput, true);
      document.removeEventListener('change', this._handleChange, true);
      document.removeEventListener('submit', this._handleSubmit, true);
      document.removeEventListener('keydown', this._handleKeydown, true);

      if (this._navObserver) this._navObserver.disconnect();
      clearInterval(this.flushInterval);

      // Final flush
      await this.flush();

      // Stop session on server
      try {{
        const resp = await fetch(CONFIG.endpoint + '/recorder/sessions/' + this.sessionId + '/stop', {{
          method: 'POST',
          headers: {{ 'X-API-Key': CONFIG.apiKey }},
        }});

        if (resp.ok) {{
          const data = await resp.json();
          console.log('[Sliples] Recording stopped. Events:', data.event_count);
          console.log('[Sliples] View at: ' + CONFIG.endpoint.replace('/api/v1', '') + '/recordings/' + this.sessionId);
        }} else {{
          const errText = await resp.text();
          console.error('[Sliples] Failed to stop recording. Status:', resp.status, errText);
        }}
      }} catch (e) {{
        console.error('[Sliples] Failed to stop recording:', e);
      }}

      this.sessionId = null;
    }},

    // Initialize bound handlers
    init: function() {{
      this._handleClick = this.handleClick.bind(this);
      this._handleInput = this.handleInput.bind(this);
      this._handleChange = this.handleChange.bind(this);
      this._handleSubmit = this.handleSubmit.bind(this);
      this._handleKeydown = this.handleKeydown.bind(this);
      return this;
    }},
  }}.init();

  // Expose globally
  window.SliplesRecorder = SliplesRecorder;

  console.log('[Sliples] Recorder loaded. Call SliplesRecorder.start("Test Name") to begin recording.');
}})();
"""
    return snippet


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
