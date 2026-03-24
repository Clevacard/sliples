"""Scheduled Celery tasks (Celery Beat)."""

from datetime import datetime

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models import TestRun


@celery_app.task
def cleanup_expired_runs():
    """
    Delete test runs that have exceeded their retention period.

    Runs daily at 2 AM (configured in celery_app.py).
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find expired runs
        expired_runs = db.query(TestRun).filter(
            TestRun.expires_at < now
        ).all()

        count = len(expired_runs)

        # Delete expired runs (cascade deletes results)
        for run in expired_runs:
            db.delete(run)

        db.commit()

        return {"deleted_count": count, "timestamp": now.isoformat()}

    finally:
        db.close()


@celery_app.task
def cleanup_orphaned_screenshots():
    """
    Delete screenshots from S3 that are no longer referenced.

    Runs daily at 3 AM (configured in celery_app.py).
    """
    # TODO: Implement S3 cleanup
    # 1. List all screenshots in S3 bucket
    # 2. Query all screenshot_urls from test_results
    # 3. Delete S3 objects not in the database

    return {"status": "not_implemented"}


def calculate_next_run_with_timezone(cron_expression: str, timezone_str: str, after: datetime = None) -> datetime:
    """
    Calculate the next run time for a cron expression in a specific timezone.

    Args:
        cron_expression: The cron expression (e.g., "0 0 * * *")
        timezone_str: The timezone name (e.g., "Europe/London")
        after: The datetime to calculate from (defaults to now)

    Returns:
        The next run time in UTC
    """
    from croniter import croniter
    from zoneinfo import ZoneInfo

    if after is None:
        after = datetime.utcnow()

    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("UTC")

    utc = ZoneInfo("UTC")

    # Convert 'after' to the schedule's timezone
    if after.tzinfo is None:
        after_utc = after.replace(tzinfo=utc)
    else:
        after_utc = after
    after_local = after_utc.astimezone(tz)

    # Calculate next run in the local timezone
    cron = croniter(cron_expression, after_local)
    next_local = cron.get_next(datetime)

    # Ensure the result is timezone-aware
    if next_local.tzinfo is None:
        next_local = next_local.replace(tzinfo=tz)

    # Convert back to UTC and make naive for storage
    next_utc = next_local.astimezone(utc)
    return next_utc.replace(tzinfo=None)


@celery_app.task
def check_scheduled_runs():
    """
    Check for schedules that are due to run and trigger them.

    Runs every minute (configured in celery_app.py).
    """
    from app.models import Schedule
    from app.workers.tasks import execute_scheduled_run

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find enabled schedules that are due to run
        due_schedules = db.query(Schedule).filter(
            Schedule.enabled == True,
            Schedule.next_run_at <= now
        ).all()

        triggered_count = 0

        for schedule in due_schedules:
            # Trigger the scheduled run
            execute_scheduled_run.delay(str(schedule.id))
            triggered_count += 1

            # Update next_run_at using the schedule's timezone
            timezone = schedule.timezone or "UTC"
            schedule.next_run_at = calculate_next_run_with_timezone(
                schedule.cron_expression, timezone, now
            )

        if triggered_count > 0:
            db.commit()

        return {
            "checked_at": now.isoformat(),
            "triggered_count": triggered_count,
        }

    finally:
        db.close()
