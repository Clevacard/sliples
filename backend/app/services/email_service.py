"""Email Notification Service.

Sends email notifications for test run completions.
"""

import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import TestRun, TestResult, StepStatus, RunStatus

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self, db: Session):
        """Initialize the email service.

        Args:
            db: Database session
        """
        self.db = db
        self.settings = get_settings()

    async def send_test_completion_email(
        self,
        run_id: str,
        recipients: list[str],
        report_url: Optional[str] = None,
    ) -> bool:
        """Send an email notification for a completed test run.

        Args:
            run_id: The UUID of the test run
            recipients: List of email addresses to notify
            report_url: Optional URL to the full report

        Returns:
            True if email was sent successfully
        """
        from uuid import UUID

        if not recipients:
            logger.warning(f"No recipients specified for test run {run_id}")
            return False

        # Fetch test run
        test_run = self.db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if not test_run:
            logger.error(f"Test run {run_id} not found")
            return False

        # Fetch results
        results = (
            self.db.query(TestResult)
            .filter(TestResult.test_run_id == test_run.id)
            .all()
        )

        # Calculate statistics
        stats = self._calculate_stats(results)

        # Get environment info
        environment = test_run.environment

        # Generate email content
        subject = self._generate_subject(test_run, stats)
        html_body = self._generate_html_body(test_run, environment, stats, results, report_url)
        text_body = self._generate_text_body(test_run, environment, stats, results, report_url)

        # Send email
        try:
            success = await self._send_email(
                recipients=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if success:
                # Update test run email_sent flag
                test_run.email_sent = True
                self.db.commit()
                logger.info(f"Email notification sent for test run {run_id} to {recipients}")

            return success

        except Exception as e:
            logger.error(f"Failed to send email for test run {run_id}: {e}")
            return False

    def _calculate_stats(self, results: list[TestResult]) -> dict:
        """Calculate summary statistics from test results.

        Args:
            results: List of test results

        Returns:
            Dictionary with counts for each status
        """
        stats = {
            "total": len(results),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0,
        }

        for result in results:
            if result.status == StepStatus.PASSED:
                stats["passed"] += 1
            elif result.status == StepStatus.FAILED:
                stats["failed"] += 1
            elif result.status == StepStatus.SKIPPED:
                stats["skipped"] += 1
            elif result.status == StepStatus.ERROR:
                stats["error"] += 1

        return stats

    def _generate_subject(self, test_run: TestRun, stats: dict) -> str:
        """Generate email subject line.

        Args:
            test_run: The test run object
            stats: Summary statistics

        Returns:
            Email subject string
        """
        status_emoji = {
            RunStatus.PASSED: "[PASSED]",
            RunStatus.FAILED: "[FAILED]",
            RunStatus.ERROR: "[ERROR]",
            RunStatus.CANCELLED: "[CANCELLED]",
        }

        status_text = status_emoji.get(test_run.status, "[COMPLETED]")
        env_name = test_run.environment.name if test_run.environment else "Unknown"

        return (
            f"{status_text} Test Run - {env_name} - "
            f"{stats['passed']}/{stats['total']} passed"
        )

    def _generate_html_body(
        self,
        test_run: TestRun,
        environment,
        stats: dict,
        results: list[TestResult],
        report_url: Optional[str],
    ) -> str:
        """Generate HTML email body.

        Args:
            test_run: The test run object
            environment: The environment configuration
            stats: Summary statistics
            results: List of test results
            report_url: Optional URL to the full report

        Returns:
            HTML email body string
        """
        # Calculate duration
        duration = "N/A"
        if test_run.started_at and test_run.finished_at:
            delta = test_run.finished_at - test_run.started_at
            total_seconds = delta.total_seconds()
            if total_seconds < 60:
                duration = f"{total_seconds:.2f}s"
            else:
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                duration = f"{minutes}m {seconds:.1f}s"

        # Status color
        status_color = {
            RunStatus.PASSED: "#28a745",
            RunStatus.FAILED: "#dc3545",
            RunStatus.ERROR: "#dc3545",
            RunStatus.CANCELLED: "#6c757d",
        }.get(test_run.status, "#6c757d")

        # Failed steps section
        failed_steps_html = ""
        failed_results = [
            r for r in results
            if r.status in (StepStatus.FAILED, StepStatus.ERROR)
        ]
        if failed_results:
            failed_rows = ""
            for result in failed_results[:10]:  # Limit to first 10 failures
                error_msg = result.error_message or "No error message"
                # Escape HTML
                error_msg = (
                    error_msg.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                step_name = (
                    result.step_name.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                failed_rows += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{step_name}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #dc3545;">{result.status.value}</td>
                </tr>
                <tr>
                    <td colspan="2" style="padding: 8px 8px 16px 8px; background: #fff5f5; font-family: monospace; font-size: 12px; white-space: pre-wrap;">{error_msg}</td>
                </tr>"""

            if len(failed_results) > 10:
                failed_rows += f"""
                <tr>
                    <td colspan="2" style="padding: 8px; text-align: center; color: #6c757d;">
                        ... and {len(failed_results) - 10} more failures
                    </td>
                </tr>"""

            failed_steps_html = f"""
            <h3 style="color: #dc3545; margin-top: 20px;">Failed Steps</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                {failed_rows}
            </table>"""

        # Report link
        report_link = ""
        if report_url:
            report_link = f"""
            <p style="margin: 20px 0;">
                <a href="{report_url}" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">View Full Report</a>
            </p>"""

        env_name = environment.name if environment else "Unknown"
        base_url = environment.base_url if environment else "N/A"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 30px;">
        <h1 style="color: #2c3e50; margin-bottom: 20px;">Test Run Completed</h1>

        <p style="margin: 10px 0;">
            <strong>Status:</strong>
            <span style="display: inline-block; padding: 4px 12px; background: {status_color}; color: white; border-radius: 4px; font-weight: bold;">
                {test_run.status.value.upper()}
            </span>
        </p>

        <h2 style="color: #34495e; margin-top: 20px;">Summary</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Total Steps:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{stats['total']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Passed:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #28a745;">{stats['passed']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Failed:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #dc3545;">{stats['failed']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Errors:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #dc3545;">{stats['error']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Skipped:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: #6c757d;">{stats['skipped']}</td>
            </tr>
        </table>

        <h2 style="color: #34495e; margin-top: 20px;">Environment</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Environment:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{env_name}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Base URL:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{base_url}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Browser:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{test_run.browser}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Duration:</strong></td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{duration}</td>
            </tr>
        </table>

        {failed_steps_html}

        {report_link}

        <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            Run ID: {test_run.id}<br>
            Triggered by: {test_run.triggered_by or 'manual'}<br>
            This is an automated message from Sliples.
        </p>
    </div>
</body>
</html>"""

        return html

    def _generate_text_body(
        self,
        test_run: TestRun,
        environment,
        stats: dict,
        results: list[TestResult],
        report_url: Optional[str],
    ) -> str:
        """Generate plain text email body.

        Args:
            test_run: The test run object
            environment: The environment configuration
            stats: Summary statistics
            results: List of test results
            report_url: Optional URL to the full report

        Returns:
            Plain text email body string
        """
        # Calculate duration
        duration = "N/A"
        if test_run.started_at and test_run.finished_at:
            delta = test_run.finished_at - test_run.started_at
            total_seconds = delta.total_seconds()
            if total_seconds < 60:
                duration = f"{total_seconds:.2f}s"
            else:
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                duration = f"{minutes}m {seconds:.1f}s"

        env_name = environment.name if environment else "Unknown"
        base_url = environment.base_url if environment else "N/A"

        text = f"""TEST RUN COMPLETED
==================

Status: {test_run.status.value.upper()}

SUMMARY
-------
Total Steps: {stats['total']}
Passed: {stats['passed']}
Failed: {stats['failed']}
Errors: {stats['error']}
Skipped: {stats['skipped']}

ENVIRONMENT
-----------
Environment: {env_name}
Base URL: {base_url}
Browser: {test_run.browser}
Duration: {duration}
"""

        # Add failed steps
        failed_results = [
            r for r in results
            if r.status in (StepStatus.FAILED, StepStatus.ERROR)
        ]
        if failed_results:
            text += "\nFAILED STEPS\n------------\n"
            for result in failed_results[:10]:
                text += f"\n- {result.step_name}\n"
                text += f"  Status: {result.status.value}\n"
                if result.error_message:
                    text += f"  Error: {result.error_message}\n"

            if len(failed_results) > 10:
                text += f"\n... and {len(failed_results) - 10} more failures\n"

        # Add report link
        if report_url:
            text += f"\nFull Report: {report_url}\n"

        text += f"""
---
Run ID: {test_run.id}
Triggered by: {test_run.triggered_by or 'manual'}
This is an automated message from Sliples.
"""

        return text

    async def _send_email(
        self,
        recipients: list[str],
        subject: str,
        html_body: str,
        text_body: str,
    ) -> bool:
        """Send an email using SMTP.

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            True if email was sent successfully
        """
        # Check SMTP configuration
        if not self.settings.smtp_host or self.settings.smtp_host == "smtp.example.com":
            logger.warning("SMTP not configured, skipping email send")
            return False

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.settings.email_from
        message["To"] = ", ".join(recipients)

        # Attach both text and HTML versions
        text_part = MIMEText(text_body, "plain", "utf-8")
        html_part = MIMEText(html_body, "html", "utf-8")

        message.attach(text_part)
        message.attach(html_part)

        try:
            # Connect and send
            logger.info(
                f"Connecting to SMTP server {self.settings.smtp_host}:{self.settings.smtp_port}"
            )

            smtp_kwargs = {
                "hostname": self.settings.smtp_host,
                "port": self.settings.smtp_port,
            }

            # Use TLS for common TLS ports
            if self.settings.smtp_port in (465, 587):
                smtp_kwargs["use_tls"] = self.settings.smtp_port == 465
                smtp_kwargs["start_tls"] = self.settings.smtp_port == 587

            async with aiosmtplib.SMTP(**smtp_kwargs) as smtp:
                # Authenticate if credentials are provided
                if self.settings.smtp_user and self.settings.smtp_password:
                    await smtp.login(
                        self.settings.smtp_user,
                        self.settings.smtp_password,
                    )

                # Send email
                await smtp.send_message(message)

            logger.info(f"Email sent successfully to {recipients}")
            return True

        except aiosmtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def send_test_completion_email_sync(
        self,
        run_id: str,
        recipients: list[str],
        report_url: Optional[str] = None,
    ) -> bool:
        """Synchronous wrapper for send_test_completion_email.

        Args:
            run_id: The UUID of the test run
            recipients: List of email addresses to notify
            report_url: Optional URL to the full report

        Returns:
            True if email was sent successfully
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.send_test_completion_email(run_id, recipients, report_url)
        )
