"""Test run management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.database import get_db
from app.models import TestRun, TestResult, Environment, RunStatus, Scenario
from app.api.deps import get_api_key_or_user
from app.config import get_settings
from app.workers.tasks import execute_test_run

router = APIRouter()
settings = get_settings()


class TestRunCreate(BaseModel):
    scenario_tags: list[str] = []
    scenario_ids: list[UUID] = []
    environment: str  # Environment name
    browsers: list[str] = ["chrome"]
    parallel: bool = True


class TestRunResponse(BaseModel):
    id: UUID
    scenario_ids: list[UUID]
    environment_id: UUID
    status: str
    browser: str
    browser_version: str
    triggered_by: Optional[str]
    parallel: bool
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TestResultResponse(BaseModel):
    id: UUID
    step_name: str
    status: str
    duration_ms: int
    error_message: Optional[str]
    screenshot_url: Optional[str]

    class Config:
        from_attributes = True


class TestRunDetail(TestRunResponse):
    results: list[TestResultResponse] = []


@router.get("/runs", response_model=list[TestRunResponse])
async def list_runs(
    status_filter: Optional[str] = None,
    environment_id: Optional[UUID] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """List test runs."""
    query = db.query(TestRun).order_by(TestRun.created_at.desc())

    if status_filter:
        query = query.filter(TestRun.status == status_filter)

    if environment_id:
        query = query.filter(TestRun.environment_id == environment_id)

    return query.offset(offset).limit(limit).all()


@router.post("/runs", response_model=TestRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    run: TestRunCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """
    Trigger a new test run.

    You can specify scenarios either by:
    - `scenario_ids`: Explicit list of scenario UUIDs
    - `scenario_tags`: Tags to filter scenarios (will run all matching scenarios)

    If both are provided, scenario_ids take precedence.
    """
    # Find environment
    env = db.query(Environment).filter(Environment.name == run.environment).first()
    if not env:
        raise HTTPException(status_code=404, detail=f"Environment '{run.environment}' not found")

    # Resolve scenario IDs from tags if not provided explicitly
    scenario_ids = run.scenario_ids
    if not scenario_ids and run.scenario_tags:
        # Find scenarios matching any of the tags
        tag_filters = [Scenario.tags.contains([t]) for t in run.scenario_tags]
        scenarios = db.query(Scenario).filter(or_(*tag_filters)).all()
        scenario_ids = [s.id for s in scenarios]

        if not scenario_ids:
            raise HTTPException(
                status_code=400,
                detail=f"No scenarios found matching tags: {run.scenario_tags}",
            )

    # If no scenario_ids or tags provided, run ALL scenarios
    if not scenario_ids:
        scenarios = db.query(Scenario).all()
        scenario_ids = [s.id for s in scenarios]

        if not scenario_ids:
            raise HTTPException(
                status_code=400,
                detail="No scenarios available. Import scenarios first.",
            )

    # Calculate expiration date
    expires_at = datetime.utcnow() + timedelta(days=env.retention_days)

    # Create test run for each browser
    # For now, just create for the first browser
    browser = run.browsers[0] if run.browsers else "chrome"

    db_run = TestRun(
        scenario_ids=scenario_ids,
        environment_id=env.id,
        status=RunStatus.QUEUED,
        browser=browser,
        browser_version="latest",
        triggered_by=auth.email if hasattr(auth, 'email') else (auth[:8] if isinstance(auth, str) else None),
        parallel=run.parallel,
        expires_at=expires_at,
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)

    # Queue Celery task for test execution
    task = execute_test_run.delay(str(db_run.id))

    # Return the run with task_id for tracking
    return db_run


@router.get("/runs/{run_id}", response_model=TestRunDetail)
async def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get a test run by ID."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Cancel a running test."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if run.status not in [RunStatus.QUEUED, RunStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Can only cancel queued or running tests")

    run.status = RunStatus.CANCELLED
    run.finished_at = datetime.utcnow()
    db.commit()


@router.get("/screenshots/{path:path}")
async def get_screenshot(
    path: str,
    auth = Depends(get_api_key_or_user),
):
    """
    Get a screenshot by its S3 path.

    Streams the image directly from S3/MinIO storage.
    """
    from fastapi.responses import StreamingResponse
    from app.services.s3_service import S3Service
    import io

    try:
        s3 = S3Service()
        response = s3.client.get_object(Bucket=s3.bucket, Key=path)
        return StreamingResponse(
            response['Body'],
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Screenshot not found: {str(e)}")


@router.get("/runs/{run_id}/report")
async def get_run_report(
    run_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get the HTML report for a test run."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if not run.report_html:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    return Response(content=run.report_html, media_type="text/html")


@router.get("/runs/{run_id}/status")
async def get_run_status(
    run_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get just the status of a test run (lightweight polling endpoint)."""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Calculate progress based on results
    total_scenarios = len(run.scenario_ids) if run.scenario_ids else 0
    completed_results = len([r for r in run.results if r.status != "pending"])

    return {
        "id": str(run.id),
        "status": run.status.value,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "total_scenarios": total_scenarios,
        "completed_steps": completed_results,
    }


@router.post("/runs/{run_id}/retry", response_model=TestRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Retry a failed or cancelled test run by creating a new run with the same configuration."""
    original_run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not original_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    if original_run.status in [RunStatus.QUEUED, RunStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Cannot retry a run that is still in progress")

    # Get environment for retention calculation
    env = db.query(Environment).filter(Environment.id == original_run.environment_id).first()
    retention_days = env.retention_days if env else 365
    expires_at = datetime.utcnow() + timedelta(days=retention_days)

    # Create a new run with the same configuration
    new_run = TestRun(
        scenario_ids=original_run.scenario_ids,
        environment_id=original_run.environment_id,
        status=RunStatus.QUEUED,
        browser=original_run.browser,
        browser_version=original_run.browser_version,
        triggered_by=auth.email if hasattr(auth, 'email') else (auth[:8] if isinstance(auth, str) else None),
        parallel=original_run.parallel,
        expires_at=expires_at,
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Queue the execution task
    execute_test_run.delay(str(new_run.id))

    return new_run


class RunStatusUpdate(BaseModel):
    status: str


@router.patch("/runs/{run_id}/status")
async def update_run_status(
    run_id: UUID,
    update: RunStatusUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """
    Update the status of a test run (internal use / worker callback).

    Valid statuses: queued, running, passed, failed, cancelled, error
    """
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Validate status
    try:
        new_status = RunStatus(update.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in RunStatus]}",
        )

    # Update status and timestamps
    old_status = run.status
    run.status = new_status

    if new_status == RunStatus.RUNNING and not run.started_at:
        run.started_at = datetime.utcnow()

    if new_status in [RunStatus.PASSED, RunStatus.FAILED, RunStatus.CANCELLED, RunStatus.ERROR]:
        run.finished_at = datetime.utcnow()

    db.commit()

    return {
        "id": str(run.id),
        "old_status": old_status.value,
        "new_status": new_status.value,
        "updated_at": datetime.utcnow().isoformat(),
    }
