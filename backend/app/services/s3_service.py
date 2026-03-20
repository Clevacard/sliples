"""S3/MinIO service for screenshot storage."""

import io
import logging
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for uploading and managing screenshots in S3/MinIO."""

    def __init__(self):
        """Initialize S3 client."""
        self.settings = get_settings()
        self.bucket = self.settings.s3_bucket

        # Create S3 client with MinIO endpoint
        self.client = boto3.client(
            "s3",
            endpoint_url=self.settings.s3_endpoint,
            aws_access_key_id=self.settings.s3_access_key,
            aws_secret_access_key=self.settings.s3_secret_key,
            region_name="us-east-1",  # MinIO doesn't care but boto3 requires it
        )

        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchBucket"):
                logger.info(f"Creating bucket {self.bucket}")
                self.client.create_bucket(Bucket=self.bucket)
            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    def upload_screenshot(
        self,
        screenshot_data: bytes,
        run_id: str,
        scenario_id: str,
        step_name: str,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Upload a screenshot to S3/MinIO.

        Args:
            screenshot_data: PNG image bytes
            run_id: Test run ID
            scenario_id: Scenario ID
            step_name: Name of the step
            timestamp: Optional timestamp for the screenshot

        Returns:
            S3 object key
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Sanitize step name for use in key
        safe_step = "".join(c if c.isalnum() or c in "-_" else "_" for c in step_name)[:100]
        ts = timestamp.strftime("%Y%m%d_%H%M%S_%f")

        # Create hierarchical key: runs/{run_id}/{scenario_id}/{step}_{timestamp}.png
        key = f"runs/{run_id}/{scenario_id}/{safe_step}_{ts}.png"

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(screenshot_data),
                ContentType="image/png",
            )
            logger.info(f"Uploaded screenshot to {key}")
            return key
        except ClientError as e:
            logger.error(f"Failed to upload screenshot: {e}")
            raise

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for viewing a screenshot.

        Args:
            key: S3 object key
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def delete_screenshot(self, key: str) -> bool:
        """
        Delete a screenshot from S3/MinIO.

        Args:
            key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted screenshot {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete screenshot: {e}")
            return False

    def delete_run_screenshots(self, run_id: str) -> int:
        """
        Delete all screenshots for a test run.

        Args:
            run_id: Test run ID

        Returns:
            Number of deleted screenshots
        """
        prefix = f"runs/{run_id}/"
        deleted_count = 0

        try:
            # List all objects with the run prefix
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if "Contents" not in page:
                    continue

                objects_to_delete = [{"Key": obj["Key"]} for obj in page["Contents"]]
                if objects_to_delete:
                    self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={"Objects": objects_to_delete},
                    )
                    deleted_count += len(objects_to_delete)

            logger.info(f"Deleted {deleted_count} screenshots for run {run_id}")
            return deleted_count
        except ClientError as e:
            logger.error(f"Failed to delete run screenshots: {e}")
            raise

    def cleanup_old_screenshots(self, retention_days: int) -> int:
        """
        Delete screenshots older than retention period.

        Args:
            retention_days: Number of days to retain screenshots

        Returns:
            Number of deleted screenshots
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0

        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix="runs/"):
                if "Contents" not in page:
                    continue

                objects_to_delete = []
                for obj in page["Contents"]:
                    # Check last modified date
                    if obj["LastModified"].replace(tzinfo=None) < cutoff_date:
                        objects_to_delete.append({"Key": obj["Key"]})

                if objects_to_delete:
                    self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={"Objects": objects_to_delete},
                    )
                    deleted_count += len(objects_to_delete)

            logger.info(f"Cleaned up {deleted_count} old screenshots")
            return deleted_count
        except ClientError as e:
            logger.error(f"Failed to cleanup old screenshots: {e}")
            raise
