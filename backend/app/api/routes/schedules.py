"""Schedule management endpoints."""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from croniter import croniter

from app.database import get_db
from app.models import Schedule, Environment, Scenario, Project, ApiKey
from app.api.deps import (
    get_api_key_or_user,
    verify_project_access,
    get_validated_api_key,
    can_write_to_project,
)

router = APIRouter()


def validate_cron_expression(cron: str) -> str:
    """Validate that a cron expression is valid."""
    try:
        # Test if the cron expression is valid
        croniter(cron, datetime.utcnow())
        return cron
    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid cron expression: {e}")


def calculate_next_run(cron_expression: str, base_time: datetime = None) -> datetime:
    """Calculate the next run time from a cron expression."""
    if base_time is None:
        base_time = datetime.utcnow()
    cron = croniter(cron_expression, base_time)
    return cron.get_next(datetime)


def get_cron_description(cron_expression: str) -> str:
    """Generate a human-readable description of a cron expression."""
    parts = cron_expression.split()
    if len(parts) != 5:
        return cron_expression

    minute, hour, day, month, weekday = parts

    # Common patterns
    if cron_expression == "0 * * * *":
        return "Every hour"
    if cron_expression == "*/15 * * * *":
        return "Every 15 minutes"
    if cron_expression == "*/30 * * * *":
        return "Every 30 minutes"
    if cron_expression == "0 0 * * *":
        return "Every day at midnight"
    if cron_expression == "0 9 * * *":
        return "Every day at 9:00 AM"
    if cron_expression == "0 9 * * 1-5":
        return "Weekdays at 9:00 AM"
    if cron_expression == "0 0 * * 0":
        return "Every Sunday at midnight"
    if cron_expression == "0 0 1 * *":
        return "First day of every month at midnight"

    # Build description
    desc_parts = []

    # Minute
    if minute == "*":
        desc_parts.append("every minute")
    elif minute.startswith("*/"):
        desc_parts.append(f"every {minute[2:]} minutes")
    elif minute == "0":
        pass  # At the top of the hour
    else:
        desc_parts.append(f"at minute {minute}")

    # Hour
    if hour == "*":
        if minute != "*":
            desc_parts.append("every hour")
    elif hour.startswith("*/"):
        desc_parts.append(f"every {hour[2:]} hours")
    else:
        try:
            h = int(hour)
            am_pm = "AM" if h < 12 else "PM"
            display_hour = h if h <= 12 else h - 12
            if display_hour == 0:
                display_hour = 12
            desc_parts.append(f"at {display_hour}:{minute.zfill(2)} {am_pm}")
        except ValueError:
            desc_parts.append(f"at hour {hour}")

    # Day of month
    if day != "*":
        if day == "1":
            desc_parts.append("on the 1st")
        elif day == "2":
            desc_parts.append("on the 2nd")
        elif day == "3":
            desc_parts.append("on the 3rd")
        else:
            desc_parts.append(f"on day {day}")

    # Month
    month_names = {
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September", "10": "October", "11": "November", "12": "December"
    }
    if month != "*":
        desc_parts.append(f"in {month_names.get(month, f'month {month}')}")

    # Day of week
    day_names = {
        "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
        "4": "Thursday", "5": "Friday", "6": "Saturday", "7": "Sunday"
    }
    if weekday != "*":
        if weekday == "1-5":
            desc_parts.append("on weekdays")
        elif weekday == "0,6":
            desc_parts.append("on weekends")
        elif weekday in day_names:
            desc_parts.append(f"on {day_names[weekday]}")
        else:
            desc_parts.append(f"on day {weekday}")

    if desc_parts:
        return " ".join(desc_parts).capitalize()
    return cron_expression


class ScheduleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cron_expression: str = Field(..., min_length=9, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    scenario_tags: list[str] = Field(default=[])
    scenario_ids: list[UUID] = Field(default=[])
    environment_ids: list[UUID] = Field(..., min_length=1)
    browsers: list[str] = Field(default=["chromium"])
    enabled: bool = True

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        return validate_cron_expression(v)

    @field_validator("browsers")
    @classmethod
    def validate_browsers(cls, v: list[str]) -> list[str]:
        valid_browsers = {"chromium", "firefox", "webkit", "chrome", "edge"}
        for browser in v:
            if browser.lower() not in valid_browsers:
                raise ValueError(f"Invalid browser: {browser}. Must be one of: {', '.join(valid_browsers)}")
        return [b.lower() for b in v]


class ScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    cron_expression: Optional[str] = Field(None, min_length=9, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    scenario_tags: Optional[list[str]] = None
    scenario_ids: Optional[list[UUID]] = None
    environment_ids: Optional[list[UUID]] = None
    browsers: Optional[list[str]] = None
    enabled: Optional[bool] = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_cron_expression(v)
        return v

    @field_validator("browsers")
    @classmethod
    def validate_browsers(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            valid_browsers = {"chromium", "firefox", "webkit", "chrome", "edge"}
            for browser in v:
                if browser.lower() not in valid_browsers:
                    raise ValueError(f"Invalid browser: {browser}. Must be one of: {', '.join(valid_browsers)}")
            return [b.lower() for b in v]
        return v


class ScheduleResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    name: str
    cron_expression: str
    cron_description: str
    timezone: str
    scenario_tags: list[str]
    scenario_ids: list[UUID]
    environment_ids: list[UUID]
    environment_names: list[str] = []
    browsers: list[str]
    enabled: bool
    created_by: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_run_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


def schedule_to_response(schedule: Schedule, db: Session = None) -> ScheduleResponse:
    """Convert a Schedule model to a ScheduleResponse."""
    # Look up environment names if db session provided
    environment_names = []
    if db and schedule.environment_ids:
        envs = db.query(Environment).filter(Environment.id.in_(schedule.environment_ids)).all()
        env_map = {env.id: env.name for env in envs}
        environment_names = [env_map.get(env_id, "Unknown") for env_id in schedule.environment_ids]

    return ScheduleResponse(
        id=schedule.id,
        project_id=schedule.project_id,
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        cron_description=get_cron_description(schedule.cron_expression),
        timezone=schedule.timezone or "UTC",
        scenario_tags=schedule.scenario_tags or [],
        scenario_ids=schedule.scenario_ids or [],
        environment_ids=schedule.environment_ids or [],
        environment_names=environment_names,
        browsers=schedule.browsers or ["chromium"],
        enabled=schedule.enabled,
        created_by=schedule.created_by,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        last_run_id=schedule.last_run_id,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
    )


@router.get("/schedules", response_model=list[ScheduleResponse])
async def list_schedules(
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
):
    """List all schedules, optionally filtered by project."""
    query = db.query(Schedule)
    if project:
        query = query.filter(Schedule.project_id == project.id)
    if enabled_only:
        query = query.filter(Schedule.enabled == True)
    schedules = query.order_by(Schedule.created_at.desc()).all()
    return [schedule_to_response(s, db) for s in schedules]


@router.post("/schedules", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    project: Optional[Project] = Depends(verify_project_access),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Create a new schedule."""
    # Check write permissions
    if not can_write_to_project(db, auth, project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create schedules in this project",
        )

    # Verify all environments exist
    if schedule.environment_ids:
        existing_envs = {
            e.id for e in db.query(Environment.id).filter(Environment.id.in_(schedule.environment_ids)).all()
        }
        missing = set(schedule.environment_ids) - existing_envs
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Environments not found: {', '.join(str(m) for m in missing)}"
            )

    # Verify scenario_ids exist if provided
    if schedule.scenario_ids:
        existing_ids = {
            s.id for s in db.query(Scenario.id).filter(Scenario.id.in_(schedule.scenario_ids)).all()
        }
        missing = set(schedule.scenario_ids) - existing_ids
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Scenarios not found: {', '.join(str(m) for m in missing)}"
            )

    # Calculate next run time with timezone
    from app.workers.scheduled import calculate_next_run_with_timezone
    timezone = schedule.timezone or "UTC"
    next_run = calculate_next_run_with_timezone(schedule.cron_expression, timezone) if schedule.enabled else None

    db_schedule = Schedule(
        project_id=project.id if project else None,
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        timezone=timezone,
        scenario_tags=schedule.scenario_tags,
        scenario_ids=schedule.scenario_ids,
        environment_ids=schedule.environment_ids,
        browsers=schedule.browsers,
        enabled=schedule.enabled,
        next_run_at=next_run,
        created_by=auth.email if hasattr(auth, 'email') else (str(auth)[:50] if auth else None),
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return schedule_to_response(db_schedule, db)


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Get a schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule_to_response(schedule, db)


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_update: ScheduleUpdate,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Update a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    update_data = schedule_update.model_dump(exclude_unset=True)

    # Verify environments if being updated
    if "environment_ids" in update_data and update_data["environment_ids"]:
        existing_envs = {
            e.id for e in db.query(Environment.id).filter(Environment.id.in_(update_data["environment_ids"])).all()
        }
        missing = set(update_data["environment_ids"]) - existing_envs
        if missing:
            raise HTTPException(
                status_code=404,
                detail=f"Environments not found: {', '.join(str(m) for m in missing)}"
            )

    # Verify scenario_ids if being updated
    if "scenario_ids" in update_data and update_data["scenario_ids"]:
        existing_ids = {
            s.id for s in db.query(Scenario.id).filter(Scenario.id.in_(update_data["scenario_ids"])).all()
        }
        missing = set(update_data["scenario_ids"]) - existing_ids
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Scenarios not found: {', '.join(str(m) for m in missing)}"
            )

    for field, value in update_data.items():
        setattr(schedule, field, value)

    # Recalculate next run if cron, timezone, or enabled changed
    from app.workers.scheduled import calculate_next_run_with_timezone
    cron_changed = "cron_expression" in update_data
    timezone_changed = "timezone" in update_data
    enabled_changed = "enabled" in update_data

    if cron_changed or timezone_changed or enabled_changed:
        if schedule.enabled:
            timezone = schedule.timezone or "UTC"
            schedule.next_run_at = calculate_next_run_with_timezone(schedule.cron_expression, timezone)
        else:
            schedule.next_run_at = None

    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    return schedule_to_response(schedule, db)


@router.delete("/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
    api_key: Optional[ApiKey] = Depends(get_validated_api_key),
):
    """Delete a schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Check write permissions for the schedule's project
    schedule_project = db.query(Project).filter(Project.id == schedule.project_id).first() if schedule.project_id else None
    if not can_write_to_project(db, auth, schedule_project, api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this schedule",
        )

    db.delete(schedule)
    db.commit()


@router.post("/schedules/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Toggle a schedule's enabled status."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.enabled = not schedule.enabled

    if schedule.enabled:
        schedule.next_run_at = calculate_next_run(schedule.cron_expression)
    else:
        schedule.next_run_at = None

    schedule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(schedule)
    return schedule_to_response(schedule, db)


@router.post("/schedules/{schedule_id}/run-now", status_code=status.HTTP_202_ACCEPTED)
async def run_schedule_now(
    schedule_id: UUID,
    db: Session = Depends(get_db),
    auth = Depends(get_api_key_or_user),
):
    """Manually trigger a scheduled run immediately."""
    from app.workers.tasks import execute_scheduled_run

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Trigger the task with manual_trigger=True to allow running disabled schedules
    task = execute_scheduled_run.delay(str(schedule_id), manual_trigger=True)

    return {
        "message": "Schedule triggered",
        "schedule_id": str(schedule_id),
        "task_id": task.id,
    }


@router.get("/schedules/cron/describe")
async def describe_cron(
    expression: str,
    auth = Depends(get_api_key_or_user),
):
    """Get a human-readable description and next runs for a cron expression."""
    try:
        validate_cron_expression(expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Calculate next 5 run times
    base_time = datetime.utcnow()
    next_runs = []
    for _ in range(5):
        next_run = calculate_next_run(expression, base_time)
        next_runs.append(next_run.isoformat())
        base_time = next_run

    return {
        "expression": expression,
        "description": get_cron_description(expression),
        "next_runs": next_runs,
    }
