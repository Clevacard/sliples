"""Redis pub/sub service for WebSocket broadcasting."""

import json
import logging
from typing import Any, Callable, Optional
import redis
from redis.asyncio import Redis as AsyncRedis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def get_redis_sync() -> redis.Redis:
    """Get synchronous Redis client (for Celery workers)."""
    return redis.from_url(settings.redis_url)


async def get_redis_async() -> AsyncRedis:
    """Get async Redis client (for FastAPI/WebSocket)."""
    return AsyncRedis.from_url(settings.redis_url)


def get_run_channel(run_id: str) -> str:
    """Get the Redis pub/sub channel name for a test run."""
    return f"sliples:run:{run_id}"


class RunUpdatePublisher:
    """
    Publishes test run updates to Redis pub/sub.

    Used by Celery workers to broadcast real-time updates.
    This uses synchronous Redis as Celery tasks are synchronous.
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None

    @property
    def redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = get_redis_sync()
        return self._redis

    def publish(self, run_id: str, message_type: str, data: dict[str, Any]) -> int:
        """
        Publish an update for a test run.

        Args:
            run_id: The test run ID
            message_type: Type of message (status_update, result_added, progress, completed, error)
            data: Message payload

        Returns:
            Number of subscribers that received the message
        """
        channel = get_run_channel(run_id)
        message = json.dumps({
            "type": message_type,
            "data": data,
        })

        try:
            count = self.redis.publish(channel, message)
            logger.debug(f"Published {message_type} to {channel}, {count} subscribers")
            return count
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
            return 0

    def publish_status_update(
        self,
        run_id: str,
        old_status: str,
        new_status: str,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
    ) -> int:
        """Publish a status change event."""
        return self.publish(run_id, "status_update", {
            "id": run_id,
            "old_status": old_status,
            "new_status": new_status,
            "started_at": started_at,
            "finished_at": finished_at,
        })

    def publish_result_added(
        self,
        run_id: str,
        result_id: str,
        step_name: str,
        status: str,
        duration_ms: int,
        error_message: Optional[str] = None,
        screenshot_url: Optional[str] = None,
    ) -> int:
        """Publish a new test result event."""
        return self.publish(run_id, "result_added", {
            "id": result_id,
            "step_name": step_name,
            "status": status,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "screenshot_url": screenshot_url,
        })

    def publish_progress(
        self,
        run_id: str,
        status: str,
        progress_message: str,
        total_scenarios: int,
        completed_steps: int,
        passed: int = 0,
        failed: int = 0,
    ) -> int:
        """Publish a progress update event."""
        return self.publish(run_id, "progress", {
            "id": run_id,
            "status": status,
            "progress_message": progress_message,
            "total_scenarios": total_scenarios,
            "completed_steps": completed_steps,
            "passed": passed,
            "failed": failed,
        })

    def publish_completed(
        self,
        run_id: str,
        status: str,
        started_at: Optional[str],
        finished_at: Optional[str],
        total_results: int,
        passed: int,
        failed: int,
        skipped: int = 0,
    ) -> int:
        """Publish a run completion event."""
        return self.publish(run_id, "completed", {
            "id": run_id,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "total_results": total_results,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        })

    def publish_error(self, run_id: str, message: str) -> int:
        """Publish an error event."""
        return self.publish(run_id, "error", {
            "message": message,
        })


# Global publisher instance for use in Celery tasks
run_update_publisher = RunUpdatePublisher()
