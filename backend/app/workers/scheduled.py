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


@celery_app.task
def check_scheduled_runs():
    """
    Check for schedules that are due to run and trigger them.

    Runs every minute (configured in celery_app.py).
    """
    from app.models import Schedule
    from app.workers.tasks import execute_scheduled_run
    from croniter import croniter

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

            # Update next_run_at to prevent re-triggering
            # (execute_scheduled_run will update it properly after execution)
            cron = croniter(schedule.cron_expression, now)
            schedule.next_run_at = cron.get_next(datetime)

        if triggered_count > 0:
            db.commit()

        return {
            "checked_at": now.isoformat(),
            "triggered_count": triggered_count,
        }

    finally:
        db.close()
