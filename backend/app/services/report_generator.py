"""HTML Report Generator Service.

Generates pytest-html style reports for test runs.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import TestRun, TestResult, Environment, Scenario, StepStatus, RunStatus

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates HTML reports for test runs."""

    # CSS styles for the report (inline for self-contained HTML)
    REPORT_CSS = """
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .report-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        .summary {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        .summary-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 8px;
            min-width: 150px;
            text-align: center;
        }
        .summary-card.passed {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .summary-card.failed {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        .summary-card.skipped {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .summary-card.error {
            background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        }
        .summary-card .count {
            font-size: 2.5em;
            font-weight: bold;
        }
        .summary-card .label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .environment {
            background: #ecf0f1;
            padding: 15px 20px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .environment dt {
            font-weight: bold;
            color: #7f8c8d;
            display: inline;
        }
        .environment dd {
            display: inline;
            margin: 0 20px 0 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-passed {
            background: #d4edda;
            color: #155724;
        }
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .status-skipped {
            background: #fff3cd;
            color: #856404;
        }
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        .status-pending {
            background: #e2e3e5;
            color: #383d41;
        }
        .error-message {
            background: #fff5f5;
            border-left: 4px solid #e74c3c;
            padding: 10px 15px;
            margin: 5px 0;
            font-family: monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .screenshot-link {
            color: #3498db;
            text-decoration: none;
        }
        .screenshot-link:hover {
            text-decoration: underline;
        }
        .duration {
            font-family: monospace;
            color: #7f8c8d;
        }
        .meta-info {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        .run-status {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        .run-status.passed {
            background: #d4edda;
            color: #155724;
        }
        .run-status.failed {
            background: #f8d7da;
            color: #721c24;
        }
        .run-status.error {
            background: #f8d7da;
            color: #721c24;
        }
    """

    def __init__(self, db: Session):
        """Initialize the report generator.

        Args:
            db: Database session
        """
        self.db = db

    def generate_report(self, run_id: str) -> str:
        """Generate an HTML report for a test run.

        Args:
            run_id: The UUID of the test run

        Returns:
            HTML string of the generated report
        """
        from uuid import UUID

        # Fetch test run with results
        test_run = self.db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if not test_run:
            logger.error(f"Test run {run_id} not found")
            raise ValueError(f"Test run {run_id} not found")

        # Fetch environment
        environment = test_run.environment

        # Fetch all results
        results = (
            self.db.query(TestResult)
            .filter(TestResult.test_run_id == test_run.id)
            .order_by(TestResult.created_at)
            .all()
        )

        # Calculate summary statistics
        stats = self._calculate_stats(results)

        # Calculate duration
        duration = self._calculate_duration(test_run)

        # Generate HTML
        html = self._render_html(test_run, environment, results, stats, duration)

        logger.info(f"Generated report for test run {run_id}")
        return html

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
            "pending": 0,
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
            else:
                stats["pending"] += 1

        return stats

    def _calculate_duration(self, test_run: TestRun) -> str:
        """Calculate the duration of a test run.

        Args:
            test_run: The test run object

        Returns:
            Formatted duration string
        """
        if test_run.started_at and test_run.finished_at:
            delta = test_run.finished_at - test_run.started_at
            total_seconds = delta.total_seconds()

            if total_seconds < 60:
                return f"{total_seconds:.2f}s"
            elif total_seconds < 3600:
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes}m {seconds:.1f}s"
            else:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"

        return "N/A"

    def _format_step_duration(self, duration_ms: int) -> str:
        """Format step duration from milliseconds.

        Args:
            duration_ms: Duration in milliseconds

        Returns:
            Formatted duration string
        """
        if duration_ms < 1000:
            return f"{duration_ms}ms"
        elif duration_ms < 60000:
            return f"{duration_ms / 1000:.2f}s"
        else:
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) / 1000
            return f"{minutes}m {seconds:.1f}s"

    def _escape_html(self, text: Optional[str]) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def _render_html(
        self,
        test_run: TestRun,
        environment: Environment,
        results: list[TestResult],
        stats: dict,
        duration: str,
    ) -> str:
        """Render the full HTML report.

        Args:
            test_run: The test run object
            environment: The environment configuration
            results: List of test results
            stats: Summary statistics
            duration: Formatted duration string

        Returns:
            Complete HTML string
        """
        # Build results rows
        results_html = self._render_results_table(results)

        # Determine overall status class
        status_class = test_run.status.value.lower()

        # Format timestamps
        started_at = (
            test_run.started_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if test_run.started_at
            else "N/A"
        )
        finished_at = (
            test_run.finished_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            if test_run.finished_at
            else "N/A"
        )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {self._escape_html(str(test_run.id))}</title>
    <style>
{self.REPORT_CSS}
    </style>
</head>
<body>
    <div class="report-container">
        <h1>Test Report</h1>

        <p>
            <strong>Run ID:</strong> {self._escape_html(str(test_run.id))}<br>
            <strong>Status:</strong> <span class="run-status {status_class}">{test_run.status.value.upper()}</span>
        </p>

        <h2>Summary</h2>
        <div class="summary">
            <div class="summary-card">
                <div class="count">{stats['total']}</div>
                <div class="label">Total Steps</div>
            </div>
            <div class="summary-card passed">
                <div class="count">{stats['passed']}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="count">{stats['failed']}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card skipped">
                <div class="count">{stats['skipped']}</div>
                <div class="label">Skipped</div>
            </div>
            <div class="summary-card error">
                <div class="count">{stats['error']}</div>
                <div class="label">Errors</div>
            </div>
        </div>

        <h2>Environment</h2>
        <dl class="environment">
            <dt>Name:</dt>
            <dd>{self._escape_html(environment.name)}</dd>
            <dt>Base URL:</dt>
            <dd>{self._escape_html(environment.base_url)}</dd>
            <dt>Browser:</dt>
            <dd>{self._escape_html(test_run.browser)} ({self._escape_html(test_run.browser_version or 'latest')})</dd>
        </dl>

        <h2>Timing</h2>
        <dl class="environment">
            <dt>Started:</dt>
            <dd>{started_at}</dd>
            <dt>Finished:</dt>
            <dd>{finished_at}</dd>
            <dt>Duration:</dt>
            <dd>{duration}</dd>
        </dl>

        <h2>Test Results</h2>
        {results_html}

        <div class="meta-info">
            <p>
                Generated by Sliples on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}<br>
                Triggered by: {self._escape_html(test_run.triggered_by or 'manual')}
            </p>
        </div>
    </div>
</body>
</html>"""

        return html

    def _render_results_table(self, results: list[TestResult]) -> str:
        """Render the results table HTML.

        Args:
            results: List of test results

        Returns:
            HTML table string
        """
        if not results:
            return "<p>No test results recorded.</p>"

        rows = []
        for idx, result in enumerate(results, 1):
            status_class = f"status-{result.status.value.lower()}"
            duration = self._format_step_duration(result.duration_ms)

            # Screenshot link
            screenshot = ""
            if result.screenshot_url:
                # Construct URL through the screenshots API endpoint
                screenshot_path = result.screenshot_url
                if not screenshot_path.startswith('/') and not screenshot_path.startswith('http'):
                    screenshot_path = f"/api/v1/screenshots/{screenshot_path}"
                screenshot = (
                    f'<a href="{self._escape_html(screenshot_path)}" '
                    f'class="screenshot-link" target="_blank">View</a>'
                )

            # Error message
            error_html = ""
            if result.error_message:
                error_html = (
                    f'<div class="error-message">{self._escape_html(result.error_message)}</div>'
                )

            row = f"""
        <tr>
            <td>{idx}</td>
            <td>
                {self._escape_html(result.step_name)}
                {error_html}
            </td>
            <td><span class="status {status_class}">{result.status.value}</span></td>
            <td class="duration">{duration}</td>
            <td>{screenshot}</td>
        </tr>"""
            rows.append(row)

        return f"""
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Step</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Screenshot</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>"""

    def save_report(self, run_id: str) -> bool:
        """Generate and save a report to the database.

        Args:
            run_id: The UUID of the test run

        Returns:
            True if successful
        """
        from uuid import UUID

        html = self.generate_report(run_id)

        test_run = self.db.query(TestRun).filter(TestRun.id == UUID(run_id)).first()
        if test_run:
            test_run.report_html = html
            self.db.commit()
            logger.info(f"Saved report for test run {run_id}")
            return True

        return False
