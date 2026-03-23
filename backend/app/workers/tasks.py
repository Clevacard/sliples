"""Celery tasks for test execution."""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models import ScenarioRepo, TestRun, TestResult, RunStatus, StepStatus, Scenario, CustomStep, Page, PageEnvironmentOverride
from app.services.s3_service import S3Service
from app.services.test_executor import run_test_execution
from app.services.websocket_pubsub import run_update_publisher


def load_pages_for_environment(db, project_id, environment_id) -> dict[str, str]:
    """Load page name -> path mapping for an environment."""
    if not project_id:
        return {}

    pages = db.query(Page).filter(Page.project_id == project_id).all()
    if not pages:
        return {}

    # Build override lookup for this environment
    override_map = {}
    overrides = db.query(PageEnvironmentOverride).filter(
        PageEnvironmentOverride.environment_id == environment_id
    ).all()
    for override in overrides:
        override_map[override.page_id] = override.path

    # Build page_name -> path mapping
    result = {}
    for page in pages:
        path = override_map.get(page.id, page.path)
        result[page.name] = path

    return result

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
    passed_count = 0
    failed_count = 0
    completed_steps = 0

    def update_progress(message: str):
        """Update progress message in database and publish to WebSocket."""
        nonlocal passed_count, failed_count, completed_steps
        try:
            run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
            if run:
                run.progress_message = message
                db.commit()

                # Publish progress update via Redis pub/sub
                run_update_publisher.publish_progress(
                    run_id=run_id,
                    status=run.status.value,
                    progress_message=message,
                    total_scenarios=len(run.scenario_ids) if run.scenario_ids else 0,
                    completed_steps=completed_steps,
                    passed=passed_count,
                    failed=failed_count,
                )

            logger.info(f"[{run_id}] {message}")
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    try:
        # Fetch the test run
        run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if not run:
            logger.error(f"Test run {run_id} not found")
            return {"success": False, "error": "Test run not found"}

        update_progress("Initializing test run...")

        # Update status to running
        old_status = run.status.value
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        db.commit()

        # Publish status update via Redis pub/sub
        run_update_publisher.publish_status_update(
            run_id=run_id,
            old_status=old_status,
            new_status=run.status.value,
            started_at=run.started_at.isoformat() if run.started_at else None,
        )

        logger.info(f"Executing test run {run_id} with browser {run.browser}")

        # Initialize S3 service for screenshot uploads
        update_progress("Initializing screenshot storage...")
        try:
            s3_service = S3Service()
        except Exception as e:
            logger.warning(f"Failed to initialize S3 service: {e}. Screenshots will not be saved.")

        # Get environment base URL
        environment = run.environment
        base_url = environment.base_url

        # Fetch scenarios to execute
        update_progress("Loading scenarios...")
        scenario_ids = run.scenario_ids or []
        if scenario_ids:
            scenarios = db.query(Scenario).filter(Scenario.id.in_(scenario_ids)).all()
        else:
            # If no specific scenarios, this might be an error
            logger.warning(f"No scenarios specified for run {run_id}")
            scenarios = []

        if not scenarios:
            run.status = RunStatus.ERROR
            run.progress_message = "Error: No scenarios to execute"
            run.finished_at = datetime.utcnow()
            db.commit()
            return {"success": False, "error": "No scenarios to execute"}

        update_progress(f"Found {len(scenarios)} scenario(s) to execute")

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
        update_progress("Loading custom step definitions...")
        custom_steps = {}
        custom_step_records = db.query(CustomStep).all()
        for step in custom_step_records:
            custom_steps[step.pattern] = step.code

        # Load pages for named page navigation
        # Try environment's project_id, then run's project_id
        project_id = environment.project_id or run.project_id
        update_progress("Loading page definitions...")
        logger.info(f"Loading pages for project_id={project_id}, environment_id={environment.id}")
        pages = load_pages_for_environment(db, project_id, environment.id)
        if pages:
            logger.info(f"Loaded {len(pages)} page definitions: {list(pages.keys())}")
        else:
            logger.info("No page definitions found")

        # Run the test execution asynchronously
        update_progress(f"Connecting to {run.browser} browser...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            execution_result = loop.run_until_complete(
                run_test_execution(
                    run_id=run_id,
                    scenarios=scenario_data,
                    browser=run.browser,
                    base_url=base_url,
                    locale=environment.locale or "en-GB",
                    timezone_id=environment.timezone_id or "Europe/London",
                    custom_steps=custom_steps if custom_steps else None,
                    pages=pages if pages else None,
                    progress_callback=update_progress,
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
                    passed_count += 1
                elif step_result.status == "failed":
                    status = StepStatus.FAILED
                    failed_count += 1
                    all_passed = False
                elif step_result.status == "skipped":
                    status = StepStatus.SKIPPED
                else:
                    status = StepStatus.ERROR
                    failed_count += 1
                    all_passed = False

                completed_steps += 1

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
                    scenario_name=scenario_result.scenario_name,
                    step_name=step_result.step_name,
                    status=status,
                    duration_ms=step_result.duration_ms,
                    error_message=step_result.error_message,
                    screenshot_url=screenshot_url,
                )
                db.add(test_result)
                db.flush()  # Flush to get the result ID

                # Publish result added event via Redis pub/sub
                run_update_publisher.publish_result_added(
                    run_id=run_id,
                    result_id=str(test_result.id),
                    step_name=step_result.step_name,
                    status=status.value,
                    duration_ms=step_result.duration_ms,
                    error_message=step_result.error_message,
                    screenshot_url=screenshot_url,
                )

        # Update run status
        old_status = run.status.value
        if execution_result.status == "error":
            run.status = RunStatus.ERROR
        elif all_passed:
            run.status = RunStatus.PASSED
        else:
            run.status = RunStatus.FAILED

        run.finished_at = datetime.utcnow()
        db.commit()

        logger.info(f"Test run {run_id} completed with status {run.status.value}")

        # Publish status update and completion event via Redis pub/sub
        run_update_publisher.publish_status_update(
            run_id=run_id,
            old_status=old_status,
            new_status=run.status.value,
            started_at=run.started_at.isoformat() if run.started_at else None,
            finished_at=run.finished_at.isoformat() if run.finished_at else None,
        )

        # Calculate final counts for completion message
        skipped_count = completed_steps - passed_count - failed_count
        run_update_publisher.publish_completed(
            run_id=run_id,
            status=run.status.value,
            started_at=run.started_at.isoformat() if run.started_at else None,
            finished_at=run.finished_at.isoformat() if run.finished_at else None,
            total_results=completed_steps,
            passed=passed_count,
            failed=failed_count,
            skipped=skipped_count if skipped_count > 0 else 0,
        )

        # Generate HTML report
        try:
            from app.services.report_generator import ReportGenerator
            report_generator = ReportGenerator(db)
            report_generator.save_report(run_id)
            logger.info(f"Generated report for test run {run_id}")
        except Exception as e:
            logger.error(f"Failed to generate report for {run_id}: {e}")

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
                old_status = run.status.value
                run.status = RunStatus.ERROR
                run.finished_at = datetime.utcnow()
                run.progress_message = f"Error: {str(e)}"
                db.commit()

                # Publish error and completion events via Redis pub/sub
                run_update_publisher.publish_error(run_id, str(e))
                run_update_publisher.publish_status_update(
                    run_id=run_id,
                    old_status=old_status,
                    new_status=run.status.value,
                    started_at=run.started_at.isoformat() if run.started_at else None,
                    finished_at=run.finished_at.isoformat() if run.finished_at else None,
                )
                run_update_publisher.publish_completed(
                    run_id=run_id,
                    status=run.status.value,
                    started_at=run.started_at.isoformat() if run.started_at else None,
                    finished_at=run.finished_at.isoformat() if run.finished_at else None,
                    total_results=completed_steps,
                    passed=passed_count,
                    failed=failed_count,
                    skipped=0,
                )
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


@celery_app.task(bind=True, max_retries=3)
def execute_scheduled_run(self, schedule_id: str, manual_trigger: bool = False):
    """
    Execute a scheduled test run.

    This task:
    1. Fetches the schedule configuration
    2. Creates a new test run
    3. Queues the test execution
    4. Updates the schedule with last/next run info

    Args:
        schedule_id: The schedule UUID
        manual_trigger: If True, run even if schedule is disabled (for "Run now" feature)
    """
    from croniter import croniter
    from app.models import Schedule, Environment

    db = SessionLocal()

    try:
        schedule = db.query(Schedule).filter(Schedule.id == UUID(schedule_id)).first()
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return {"success": False, "error": "Schedule not found"}

        if not schedule.enabled and not manual_trigger:
            logger.info(f"Schedule {schedule_id} is disabled, skipping")
            return {"success": False, "error": "Schedule is disabled"}

        # Get environments
        environment_ids = schedule.environment_ids or []
        if not environment_ids:
            logger.error(f"No environments configured for schedule {schedule_id}")
            return {"success": False, "error": "No environments configured"}

        environments = db.query(Environment).filter(
            Environment.id.in_(environment_ids)
        ).all()
        if not environments:
            logger.error(f"No valid environments found for schedule {schedule_id}")
            return {"success": False, "error": "Environments not found"}

        logger.info(f"Executing scheduled run: {schedule.name} (ID: {schedule_id})")

        # Determine scenarios to run
        scenario_ids = list(schedule.scenario_ids) if schedule.scenario_ids else []

        # If tags are specified, find scenarios with those tags
        if schedule.scenario_tags:
            from app.models import Scenario
            tagged_scenarios = db.query(Scenario).filter(
                Scenario.tags.overlap(schedule.scenario_tags)
            ).all()
            tag_scenario_ids = [s.id for s in tagged_scenarios]
            # Combine with explicit scenario_ids (union)
            scenario_ids = list(set(scenario_ids + tag_scenario_ids))

        if not scenario_ids:
            logger.warning(f"No scenarios to run for schedule {schedule_id}")
            return {"success": False, "error": "No scenarios to execute"}

        # Create test runs for each environment and browser combination
        browsers = schedule.browsers or ["chromium"]
        run_ids = []

        for environment in environments:
            for browser in browsers:
                # Create a new test run
                run = TestRun(
                    scenario_ids=scenario_ids,
                    environment_id=environment.id,
                    status=RunStatus.QUEUED,
                    browser=browser,
                    triggered_by=f"schedule:{schedule.name}",
                    parallel=True,
                )
                db.add(run)
                db.flush()

                run_ids.append(str(run.id))

                # Queue the test execution
                execute_test_run.delay(str(run.id))

        # Update schedule tracking
        now = datetime.utcnow()
        schedule.last_run_at = now
        schedule.last_run_id = UUID(run_ids[0]) if run_ids else None

        # Calculate next run time
        cron = croniter(schedule.cron_expression, now)
        schedule.next_run_at = cron.get_next(datetime)

        db.commit()

        logger.info(
            f"Scheduled run {schedule.name} created {len(run_ids)} test run(s): {run_ids}"
        )

        return {
            "success": True,
            "schedule_id": schedule_id,
            "schedule_name": schedule.name,
            "run_ids": run_ids,
            "browsers": browsers,
            "scenario_count": len(scenario_ids),
        }

    except Exception as e:
        logger.error(f"Error executing scheduled run {schedule_id}: {e}")
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
