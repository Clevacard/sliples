"""Interactive test session management endpoints."""

from uuid import UUID, uuid4
from typing import Optional, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Environment, Scenario, TestSession, User
from app.api.deps import get_api_key_or_user
from app.services.interactive_executor import InteractiveExecutor, StepExecutionResult

router = APIRouter()


# Request/Response Models
class TestSessionCreate(BaseModel):
    """Request to start an interactive test session."""
    scenario_id: Optional[UUID] = None
    environment_id: UUID
    browser_type: str = "chromium"


class TestSessionResponse(BaseModel):
    """Response with test session info."""
    id: UUID
    status: str
    browser_type: str
    environment_name: str
    environment_base_url: str
    scenario_name: Optional[str] = None
    current_step_index: int = 0
    total_steps: int = 0
    started_at: datetime
    last_activity: datetime
    websocket_url: str

    class Config:
        from_attributes = True


class StepExecuteRequest(BaseModel):
    """Request to execute a step."""
    step_index: Optional[int] = None  # None means current step


class StepExecuteResponse(BaseModel):
    """Response from step execution."""
    step_name: str
    status: str
    duration_ms: int
    error_message: Optional[str] = None
    screenshot_base64: Optional[str] = None
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    next_step_index: int
    total_steps: int


class ScreenshotResponse(BaseModel):
    """Response with screenshot data."""
    screenshot_base64: str
    current_url: Optional[str] = None
    page_title: Optional[str] = None


class SessionStatusResponse(BaseModel):
    """Response with session status."""
    id: str
    status: str
    current_step_index: int
    total_steps: int
    current_url: Optional[str] = None
    page_title: Optional[str] = None
    step_results: list
    logs: list


class LoadScenarioRequest(BaseModel):
    """Request to load a scenario into the session."""
    scenario_id: Optional[UUID] = None
    content: Optional[str] = None  # Direct Gherkin content


class LoadScenarioResponse(BaseModel):
    """Response from loading a scenario."""
    steps: list
    total_steps: int


class CustomActionRequest(BaseModel):
    """Request to run a custom browser action."""
    action: str  # click, fill, select, etc.
    selector: str = ""
    value: str = ""


class NavigateRequest(BaseModel):
    """Request to navigate to a URL."""
    url: str


def _get_user_id(auth: Union[str, User]) -> Optional[UUID]:
    """Extract user ID from auth result."""
    if isinstance(auth, User):
        return auth.id
    return None


@router.post("/test-session/start", response_model=TestSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_test_session(
    request: TestSessionCreate,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """
    Start a new interactive test session.

    This launches a visible browser window for interactive testing.
    Returns session info including WebSocket URL for live updates.
    """
    # Validate environment
    environment = db.query(Environment).filter(Environment.id == request.environment_id).first()
    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Validate scenario if provided
    scenario = None
    if request.scenario_id:
        scenario = db.query(Scenario).filter(Scenario.id == request.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

    # Generate session ID
    session_id = uuid4()

    try:
        # Create interactive session
        await InteractiveExecutor.create_session(
            session_id=str(session_id),
            browser_type=request.browser_type,
            base_url=environment.base_url,
            headless=False,  # Always visible for interactive testing
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start browser session: {str(e)}"
        )

    # Create database record
    db_session = TestSession(
        id=session_id,
        user_id=_get_user_id(auth),
        scenario_id=request.scenario_id,
        environment_id=request.environment_id,
        status='active',
        browser_type=request.browser_type,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    # Load scenario steps if scenario provided
    total_steps = 0
    if scenario:
        interactive_session = InteractiveExecutor.get_session(str(session_id))
        if interactive_session and scenario.content:
            steps = await interactive_session.load_scenario(scenario.content)
            total_steps = len(steps)

    return TestSessionResponse(
        id=session_id,
        status="active",
        browser_type=request.browser_type,
        environment_name=environment.name,
        environment_base_url=environment.base_url,
        scenario_name=scenario.name if scenario else None,
        current_step_index=0,
        total_steps=total_steps,
        started_at=db_session.started_at,
        last_activity=db_session.last_activity,
        websocket_url=f"/api/v1/test-session/{session_id}/ws",
    )


@router.post("/test-session/{session_id}/load-scenario", response_model=LoadScenarioResponse)
async def load_scenario(
    session_id: UUID,
    request: LoadScenarioRequest,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Load a scenario into an active test session."""
    # Get interactive session
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    content = request.content

    # Load from scenario if ID provided
    if request.scenario_id:
        scenario = db.query(Scenario).filter(Scenario.id == request.scenario_id).first()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        content = scenario.content

        # Update database record
        db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if db_session:
            db_session.scenario_id = request.scenario_id
            db_session.last_activity = datetime.utcnow()
            db.commit()

    if not content:
        raise HTTPException(status_code=400, detail="No scenario content provided")

    steps = await interactive_session.load_scenario(content)

    return LoadScenarioResponse(
        steps=steps,
        total_steps=len(steps),
    )


@router.post("/test-session/{session_id}/step", response_model=StepExecuteResponse)
async def execute_step(
    session_id: UUID,
    request: StepExecuteRequest = StepExecuteRequest(),
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """
    Execute a single Gherkin step.

    If step_index is not provided, executes the current step.
    Returns step result with screenshot.
    """
    # Get interactive session
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    # Execute step
    result = await interactive_session.execute_step(step_index=request.step_index)

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.current_step_index = str(interactive_session.current_step_index)
        db_session.step_results = interactive_session.step_results
        db_session.current_url = result.current_url
        db_session.current_title = result.page_title
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return StepExecuteResponse(
        step_name=result.step_name,
        status=result.status,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        screenshot_base64=result.screenshot_base64,
        current_url=result.current_url,
        page_title=result.page_title,
        next_step_index=interactive_session.current_step_index,
        total_steps=len(interactive_session.scenario_steps),
    )


@router.post("/test-session/{session_id}/skip", response_model=StepExecuteResponse)
async def skip_step(
    session_id: UUID,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Skip the current step."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    result = await interactive_session.skip_step()

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.current_step_index = str(interactive_session.current_step_index)
        db_session.step_results = interactive_session.step_results
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return StepExecuteResponse(
        step_name=result.step_name,
        status=result.status,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        screenshot_base64=result.screenshot_base64,
        current_url=result.current_url,
        page_title=result.page_title,
        next_step_index=interactive_session.current_step_index,
        total_steps=len(interactive_session.scenario_steps),
    )


@router.post("/test-session/{session_id}/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(
    session_id: UUID,
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Take a screenshot of the current browser state."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    screenshot = await interactive_session.take_screenshot()
    if not screenshot:
        raise HTTPException(status_code=500, detail="Failed to take screenshot")

    state = await interactive_session.get_state()

    return ScreenshotResponse(
        screenshot_base64=screenshot,
        current_url=state.current_url,
        page_title=state.page_title,
    )


@router.get("/test-session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: UUID,
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Get the current status of a test session."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    state = await interactive_session.get_state()

    return SessionStatusResponse(
        id=state.session_id,
        status=state.status,
        current_step_index=state.current_step_index,
        total_steps=state.total_steps,
        current_url=state.current_url,
        page_title=state.page_title,
        step_results=state.step_results,
        logs=state.logs,
    )


@router.post("/test-session/{session_id}/navigate", response_model=StepExecuteResponse)
async def navigate(
    session_id: UUID,
    request: NavigateRequest,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Navigate to a specific URL."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    result = await interactive_session.navigate(request.url)

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.current_url = result.current_url
        db_session.current_title = result.page_title
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return StepExecuteResponse(
        step_name=result.step_name,
        status=result.status,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        screenshot_base64=result.screenshot_base64,
        current_url=result.current_url,
        page_title=result.page_title,
        next_step_index=interactive_session.current_step_index,
        total_steps=len(interactive_session.scenario_steps),
    )


@router.post("/test-session/{session_id}/action", response_model=StepExecuteResponse)
async def run_custom_action(
    session_id: UUID,
    request: CustomActionRequest,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Run a custom browser action (click, fill, etc.)."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    result = await interactive_session.run_custom_action(
        action=request.action,
        selector=request.selector,
        value=request.value,
    )

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.current_url = result.current_url
        db_session.current_title = result.page_title
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return StepExecuteResponse(
        step_name=result.step_name,
        status=result.status,
        duration_ms=result.duration_ms,
        error_message=result.error_message,
        screenshot_base64=result.screenshot_base64,
        current_url=result.current_url,
        page_title=result.page_title,
        next_step_index=interactive_session.current_step_index,
        total_steps=len(interactive_session.scenario_steps),
    )


@router.post("/test-session/{session_id}/pause")
async def pause_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Pause a test session."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    interactive_session.pause()

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.status = 'paused'
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return {"status": "paused", "session_id": str(session_id)}


@router.post("/test-session/{session_id}/resume")
async def resume_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """Resume a paused test session."""
    interactive_session = InteractiveExecutor.get_session(str(session_id))
    if not interactive_session:
        raise HTTPException(status_code=404, detail="Session not found or not active")

    interactive_session.resume()

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.status = 'active'
        db_session.last_activity = datetime.utcnow()
        db.commit()

    return {"status": "active", "session_id": str(session_id)}


@router.delete("/test-session/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_test_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """
    End and cleanup a test session.

    Closes the browser and marks the session as terminated.
    """
    # End interactive session
    ended = await InteractiveExecutor.end_session(str(session_id))

    # Update database
    db_session = db.query(TestSession).filter(TestSession.id == session_id).first()
    if db_session:
        db_session.status = 'terminated'
        db_session.completed_at = datetime.utcnow()
        db_session.last_activity = datetime.utcnow()
        db.commit()

    if not ended and not db_session:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/test-sessions", response_model=list[TestSessionResponse])
async def list_test_sessions(
    active_only: bool = True,
    db: Session = Depends(get_db),
    auth: Union[str, User] = Depends(get_api_key_or_user),
):
    """List all test sessions."""
    query = db.query(TestSession).order_by(TestSession.started_at.desc())

    if active_only:
        query = query.filter(TestSession.status.in_(['active', 'paused']))

    sessions = query.limit(50).all()

    result = []
    for session in sessions:
        env = session.environment
        scenario = session.scenario

        # Get step count from interactive session if active
        total_steps = 0
        current_step = 0
        interactive = InteractiveExecutor.get_session(str(session.id))
        if interactive:
            total_steps = len(interactive.scenario_steps)
            current_step = interactive.current_step_index

        result.append(TestSessionResponse(
            id=session.id,
            status=session.status.value,
            browser_type=session.browser_type,
            environment_name=env.name if env else "Unknown",
            environment_base_url=env.base_url if env else "",
            scenario_name=scenario.name if scenario else None,
            current_step_index=current_step,
            total_steps=total_steps,
            started_at=session.started_at,
            last_activity=session.last_activity,
            websocket_url=f"/api/v1/test-session/{session.id}/ws",
        ))

    return result


# WebSocket for real-time updates
@router.websocket("/test-session/{session_id}/ws")
async def websocket_session(
    websocket: WebSocket,
    session_id: UUID,
):
    """
    WebSocket endpoint for real-time session updates.

    Sends periodic status updates and step results.
    """
    await websocket.accept()

    try:
        while True:
            # Get session
            interactive_session = InteractiveExecutor.get_session(str(session_id))
            if not interactive_session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found or terminated",
                })
                break

            # Send state update
            state = await interactive_session.get_state()
            await websocket.send_json({
                "type": "status",
                "data": {
                    "session_id": state.session_id,
                    "status": state.status,
                    "current_step_index": state.current_step_index,
                    "total_steps": state.total_steps,
                    "current_url": state.current_url,
                    "page_title": state.page_title,
                    "step_results": state.step_results[-10:],  # Last 10 results
                    "logs": state.logs[-20:],  # Last 20 logs
                },
            })

            # Wait for client message or timeout
            try:
                import asyncio
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=2.0,
                )
                # Handle ping/pong
                if message == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                pass  # Normal timeout, continue loop

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
