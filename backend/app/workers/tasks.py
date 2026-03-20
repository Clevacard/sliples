"""Celery tasks for test execution."""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models import ScenarioRepo, TestRun, TestResult, RunStatus, StepStatus, Scenario, CustomStep
from app.services.s3_service import S3Service
from app.services.test_executor import run_test_execution

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def execute_test_run(self, run_id: str):
    """
    Execute a test run.

    This task:
    1. Fetches the test run configuration
    2. Connects to the appropriate browser
    3. Executes all scenarios
    4. Captures screenshots
    5. Stores results in database
    6. Uploads screenshots to S3/MinIO
    """
    db = SessionLocal()
    s3_service = None

    try:
        # Fetch the test run
        run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if not run:
            logger.error(f"Test run {run_id} not found")
            return {"success": False, "error": "Test run not found"}

        # Update status to running
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Executing test run {run_id} with browser {run.browser}")

        # Initialize S3 service for screenshot uploads
        try:
            s3_service = S3Service()
        except Exception as e:
            logger.warning(f"Failed to initialize S3 service: {e}. Screenshots will not be saved.")

        # Get environment base URL
        environment = run.environment
        base_url = environment.base_url

        # Fetch scenarios to execute
        scenario_ids = run.scenario_ids or []
        if scenario_ids:
            scenarios = db.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        else:
            # If no specific scenarios, this might be an error
            logger.warning(f"No scenarios specified for run {run_id}")
            scenarios = []

        if not scenarios:
            run.status = RunStatus.ERROR
            run.finished_at = datetime.utcnow()
            db.commit()
            return {"success": False, "error": "No scenarios to execute"}

        # Prepare scenario data for executor
        scenario_data = [
            {
                "id": str(s.id),
                "name": s.name,
                "content": s.content or "",
            }
            for s in scenarios
        ]

        # Fetch custom step definitions
        custom_steps = {}
        custom_step_records = db.query(CustomStep).all()
        for step in custom_step_records:
            custom_steps[step.pattern] = step.code

        # Run the test execution asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            execution_result = loop.run_until_complete(
                run_test_execution(
                    run_id=run_id,
                    scenarios=scenario_data,
                    browser=run.browser,
                    base_url=base_url,
                    custom_steps=custom_steps if custom_steps else None,
                )
            )
        finally:
            loop.close()

        # Process results and store in database
        all_passed = True
        for scenario_result in execution_result.scenarios:
            for step_result in scenario_result.steps:
                # Map status
                if step_result.status == "passed":
                    status = StepStatus.PASSED
                elif step_result.status == "failed":
                    status = StepStatus.FAILED
                    all_passed = False
                elif step_result.status == "skipped":
                    status = StepStatus.SKIPPED
                else:
                    status = StepStatus.ERROR
                    all_passed = False

                # Upload screenshot if available
                screenshot_url = None
                if step_result.screenshot_data and s3_service:
                    try:
                        s3_key = s3_service.upload_screenshot(
                            screenshot_data=step_result.screenshot_data,
                            run_id=run_id,
                            scenario_id=scenario_result.scenario_id,
                            step_name=step_result.step_name,
                        )
                        screenshot_url = s3_key  # Store key, generate presigned URL on access
                    except Exception as e:
                        logger.error(f"Failed to upload screenshot: {e}")

                # Create TestResult record
                test_result = TestResult(
                    test_run_id=UUID(run_id),
                    scenario_id=UUID(scenario_result.scenario_id),
                    step_name=step_result.step_name,
                    status=status,
                    duration_ms=step_result.duration_ms,
                    error_message=step_result.error_message,
                    screenshot_url=screenshot_url,
                )
                db.add(test_result)

        # Update run status
        if execution_result.status == "error":
            run.status = RunStatus.ERROR
        elif all_passed:
            run.status = RunStatus.PASSED
        else:
            run.status = RunStatus.FAILED

        run.finished_at = datetime.utcnow()
        db.commit()

        logger.info(f"Test run {run_id} completed with status {run.status.value}")

        return {
            "success": True,
            "run_id": run_id,
            "status": run.status.value,
            "scenarios_executed": len(execution_result.scenarios),
            "duration_ms": execution_result.total_duration_ms,
        }

    except Exception as e:
        logger.error(f"Error executing test run {run_id}: {e}")
        # Update run status to error
        try:
            run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
            if run:
                run.status = RunStatus.ERROR
                run.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def sync_repository(self, repo_id: str):
    """
    Sync scenarios from a git repository.

    This task:
    1. Clones or pulls the repository
    2. Parses all .feature files
    3. Updates the scenarios in the database
    """
    from app.services.git_sync_service import GitSyncService

    db = SessionLocal()
    try:
        from uuid import UUID

        repo = db.query(ScenarioRepo).filter(ScenarioRepo.id == UUID(repo_id)).first()
        if not repo:
            logger.error(f"Repository {repo_id} not found")
            return {"success": False, "error": "Repository not found"}

        logger.info(f"Starting sync for repository {repo.name}")

        sync_service = GitSyncService(db)
        result = sync_service.full_sync(repo)

        logger.info(
            f"Sync completed for {repo.name}: "
            f"created={result['created']}, updated={result['updated']}, "
            f"errors={len(result['errors'])}"
        )

        return result

    except Exception as e:
        logger.error(f"Error syncing repository {repo_id}: {e}")
        raise self.retry(exc=e, countdown=60)  # Retry after 1 minute
    finally:
        db.close()


@celery_app.task(bind=True)
def sync_all_repositories(self):
    """
    Sync all repositories.

    This task triggers sync_repository for each configured repo.
    """
    db = SessionLocal()
    try:
        repos = db.query(ScenarioRepo).all()
        results = []

        for repo in repos:
            # Queue individual sync tasks
            task = sync_repository.delay(str(repo.id))
            results.append({"repo_id": str(repo.id), "repo_name": repo.name, "task_id": task.id})

        return {"queued": len(results), "repos": results}

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, run_id: str):
    """
    Generate HTML report for a test run.

    This task:
    1. Fetches all test results
    2. Generates pytest-html style report
    3. Stores the report in the database
    """
    from app.services.report_generator import ReportGenerator

    db = SessionLocal()
    try:
        logger.info(f"Generating report for test run {run_id}")

        report_generator = ReportGenerator(db)
        success = report_generator.save_report(run_id)

        if success:
            logger.info(f"Report generated successfully for test run {run_id}")
            return {"success": True, "run_id": run_id}
        else:
            logger.error(f"Failed to generate report for test run {run_id}")
            return {"success": False, "run_id": run_id, "error": "Report generation failed"}

    except Exception as e:
        logger.error(f"Error generating report for test run {run_id}: {e}")
        raise self.retry(exc=e, countdown=30)
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def send_notification(self, run_id: str, recipients: list[str] = None, report_url: str = None):
    """
    Send email notification for a completed test run.

    This task:
    1. Fetches the test run results
    2. Generates email content
    3. Sends email via SMTP

    Args:
        run_id: The UUID of the test run
        recipients: List of email addresses to notify (optional)
        report_url: URL to the full report (optional)
    """
    from app.services.email_service import EmailService

    db = SessionLocal()
    try:
        logger.info(f"Sending notification for test run {run_id}")

        # If no recipients provided, skip
        if not recipients:
            logger.warning(f"No recipients specified for test run {run_id}, skipping notification")
            return {"success": False, "run_id": run_id, "error": "No recipients specified"}

        email_service = EmailService(db)
        success = email_service.send_test_completion_email_sync(
            run_id=run_id,
            recipients=recipients,
            report_url=report_url,
        )

        if success:
            logger.info(f"Notification sent successfully for test run {run_id}")
            return {"success": True, "run_id": run_id, "recipients": recipients}
        else:
            logger.warning(f"Notification not sent for test run {run_id} (SMTP may not be configured)")
            return {"success": False, "run_id": run_id, "error": "Email not sent"}

    except Exception as e:
        logger.error(f"Error sending notification for test run {run_id}: {e}")
        raise self.retry(exc=e, countdown=30)
    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_old_data(self):
    """
    Clean up old test runs and screenshots based on retention policy.

    This task:
    1. Finds test runs past their retention period
    2. Deletes associated screenshots from S3/MinIO
    3. Deletes the test runs and results from the database
    """
    from app.config import get_settings

    db = SessionLocal()
    settings = get_settings()

    try:
        # Initialize S3 service
        try:
            s3_service = S3Service()
        except Exception as e:
            logger.error(f"Failed to initialize S3 service for cleanup: {e}")
            return {"success": False, "error": str(e)}

        # Find expired test runs
        now = datetime.utcnow()
        expired_runs = db.query(TestRun).filter(
            TestRun.expires_at.isnot(None),
            TestRun.expires_at < now
        ).all()

        deleted_runs = 0
        deleted_screenshots = 0

        for run in expired_runs:
            run_id = str(run.id)

            # Delete screenshots from S3
            try:
                count = s3_service.delete_run_screenshots(run_id)
                deleted_screenshots += count
            except Exception as e:
                logger.error(f"Failed to delete screenshots for run {run_id}: {e}")

            # Delete test results and run from database
            db.query(TestResult).filter(TestResult.test_run_id == run.id).delete()
            db.delete(run)
            deleted_runs += 1

        db.commit()

        # Also clean up screenshots that might be orphaned (based on file age)
        try:
            orphan_count = s3_service.cleanup_old_screenshots(settings.retention_days)
            deleted_screenshots += orphan_count
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned screenshots: {e}")

        logger.info(
            f"Cleanup completed: deleted {deleted_runs} test runs "
            f"and {deleted_screenshots} screenshots"
        )

        return {
            "success": True,
            "deleted_runs": deleted_runs,
            "deleted_screenshots": deleted_screenshots,
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
