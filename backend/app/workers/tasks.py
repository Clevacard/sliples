"""Celery tasks for test execution."""

import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models import ScenarioRepo, TestRun, RunStatus

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
    5. Generates the report
    6. Sends email notification
    """
    db = SessionLocal()
    try:
        # Fetch the test run
        from uuid import UUID

        run = db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if not run:
            logger.error(f"Test run {run_id} not found")
            return {"success": False, "error": "Test run not found"}

        # Update status to running
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        db.commit()

        # TODO: Implement actual test execution in Phase 3
        # For now, just mark as passed after a placeholder
        logger.info(f"Executing test run {run_id}")

        # Placeholder: mark as passed for now
        run.status = RunStatus.PASSED
        run.finished_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "run_id": run_id,
            "status": run.status.value,
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


@celery_app.task(bind=True)
def generate_report(self, run_id: str):
    """
    Generate HTML report for a test run.

    This task:
    1. Fetches all test results
    2. Generates pytest-html style report
    3. Stores the report in the database
    """
    # TODO: Implement in Phase 5
    pass


@celery_app.task(bind=True)
def send_notification(self, run_id: str):
    """
    Send email notification for a completed test run.

    This task:
    1. Fetches the test run results
    2. Generates email content
    3. Sends email via SMTP
    """
    # TODO: Implement in Phase 5
    pass
