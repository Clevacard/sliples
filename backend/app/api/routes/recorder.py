"""Recording session endpoints for UI event capture."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecordingSession, RecordedEvent, RecordingStatus, Project
from app.api.deps import get_api_key, verify_project_access, get_validated_api_key


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

    class Config:
        from_attributes = True


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/recorder/sessions", response_model=RecordingStartResponse, status_code=status.HTTP_201_CREATED)
async def start_recording(
    request: RecordingStartRequest,
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),
    project: Optional[Project] = Depends(verify_project_access),
):
    """
    Start a new recording session.

    Returns a session_id that should be used for all subsequent event submissions.
    """
    session = RecordingSession(
        project_id=project.id if project else None,
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
    _api_key: str = Depends(get_api_key),
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
    _api_key: str = Depends(get_api_key),
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
    _api_key: str = Depends(get_api_key),
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
    _api_key: str = Depends(get_api_key),
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
    _api_key: str = Depends(get_api_key),
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
        )
        for e in events
    ]


@router.delete("/recorder/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(
    session_id: UUID,
    db: Session = Depends(get_db),
    _api_key: str = Depends(get_api_key),
):
    """Delete a recording session and all its events."""
    session = db.query(RecordingSession).filter(RecordingSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording session not found")

    db.delete(session)
    db.commit()


@router.get("/recorder/snippet.js", response_class=PlainTextResponse)
async def get_recorder_snippet(
    api_key: str,
    endpoint: Optional[str] = None,
    project_id: Optional[str] = None,
):
    """
    Get the recorder JavaScript snippet configured for this API key.

    Query params:
    - api_key: Required API key for authentication
    - endpoint: Optional custom API endpoint (defaults to this server)
    - project_id: Optional project ID to associate recordings with
    """
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
