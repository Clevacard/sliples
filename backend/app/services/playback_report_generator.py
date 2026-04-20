"""HTML Report Generator for Playback Runs."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import PlaybackRun, PlaybackStepResult, PlaybackStatus, PlaybackStepStatus, RecordedEvent

logger = logging.getLogger(__name__)


class PlaybackReportGenerator:
    """Generates HTML reports for playback runs."""

    REPORT_CSS = """
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
            border-bottom: 3px solid #9b59b6;
            padding-bottom: 10px;
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
        .summary-card.passed { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .summary-card.failed { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
        .summary-card .count { font-size: 2.5em; font-weight: bold; }
        .summary-card .label { font-size: 0.9em; opacity: 0.9; }
        .info { background: #ecf0f1; padding: 15px 20px; border-radius: 6px; margin: 20px 0; }
        .info dt { font-weight: bold; color: #7f8c8d; display: inline; }
        .info dd { display: inline; margin: 0 20px 0 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f5f5f5; }
        .status-passed { color: #27ae60; font-weight: bold; }
        .status-failed { color: #e74c3c; font-weight: bold; }
        .error-msg { color: #e74c3c; font-size: 0.9em; margin-top: 5px; }
        .screenshot { max-width: 400px; border: 1px solid #ddd; border-radius: 4px; margin-top: 10px; }
        .event-type {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }
        .event-click { background: #3498db; color: white; }
        .event-input { background: #f39c12; color: white; }
        .event-navigation { background: #9b59b6; color: white; }
        .event-submit { background: #27ae60; color: white; }
        .event-change { background: #e67e22; color: white; }
        .event-default { background: #95a5a6; color: white; }
        .selector { font-family: monospace; font-size: 0.85em; color: #666; }
    """

    def __init__(self, db: Session):
        self.db = db

    def generate_report(self, playback_run_id: str) -> str:
        """Generate HTML report for a playback run."""
        run = self.db.query(PlaybackRun).filter(PlaybackRun.id == UUID(playback_run_id)).first()
        if not run:
            return "<html><body><h1>Playback run not found</h1></body></html>"

        session = run.session
        environment = run.environment
        step_results = self.db.query(PlaybackStepResult).filter(
            PlaybackStepResult.playback_run_id == run.id
        ).order_by(PlaybackStepResult.sequence).all()

        # Build step results with event data
        steps_html = []
        for result in step_results:
            event = self.db.query(RecordedEvent).filter(RecordedEvent.id == result.event_id).first()
            steps_html.append(self._render_step(result, event))

        duration_str = f"{run.duration_ms / 1000:.2f}s" if run.duration_ms else "N/A"
        status_class = "passed" if run.status == PlaybackStatus.passed else "failed"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playback Report - {session.name}</title>
    <style>{self.REPORT_CSS}</style>
</head>
<body>
    <div class="report-container">
        <h1>Playback Report: {session.name}</h1>

        <div class="summary">
            <div class="summary-card {status_class}">
                <div class="count">{run.status.value.upper()}</div>
                <div class="label">Status</div>
            </div>
            <div class="summary-card passed">
                <div class="count">{run.passed_steps}</div>
                <div class="label">Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="count">{run.failed_steps}</div>
                <div class="label">Failed</div>
            </div>
            <div class="summary-card">
                <div class="count">{run.total_steps}</div>
                <div class="label">Total Steps</div>
            </div>
        </div>

        <div class="info">
            <dl>
                <dt>Recording:</dt><dd>{session.name}</dd>
                <dt>URL:</dt><dd>{session.url}</dd>
                <dt>Environment:</dt><dd>{environment.name}</dd>
                <dt>Browser:</dt><dd>{run.browser}</dd>
                <dt>Viewport:</dt><dd>{run.viewport_width}x{run.viewport_height}</dd>
                <dt>Duration:</dt><dd>{duration_str}</dd>
                <dt>Started:</dt><dd>{run.started_at.strftime('%Y-%m-%d %H:%M:%S') if run.started_at else 'N/A'}</dd>
                <dt>Finished:</dt><dd>{run.finished_at.strftime('%Y-%m-%d %H:%M:%S') if run.finished_at else 'N/A'}</dd>
            </dl>
        </div>

        <h2>Step Results</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Event</th>
                    <th>Element</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {''.join(steps_html)}
            </tbody>
        </table>
    </div>
</body>
</html>"""
        return html

    def _render_step(self, result: PlaybackStepResult, event: RecordedEvent) -> str:
        """Render a single step row."""
        status_class = "status-passed" if result.status == PlaybackStepStatus.passed else "status-failed"
        event_class = f"event-{event.event_type}" if event else "event-default"

        element_display = ""
        if event:
            if event.step_label:
                element_display = event.step_label
            elif event.label_text:
                element_display = event.label_text
            elif event.selector_test_id:
                element_display = f'[data-testid="{event.selector_test_id}"]'
            elif event.element_id:
                element_display = f"#{event.element_id}"
            elif event.selector_css:
                element_display = event.selector_css[:50] + "..." if len(event.selector_css or "") > 50 else event.selector_css
            else:
                element_display = event.tag_name or "unknown"

        duration_str = f"{result.duration_ms}ms" if result.duration_ms else "-"

        details = ""
        if result.error_message:
            details += f'<div class="error-msg">{result.error_message}</div>'
        if result.selector_used:
            details += f'<div class="selector">Selector: {result.selector_used[:80]}</div>'
        if result.screenshot_url:
            details += f'<div><img class="screenshot" src="/api/v1/screenshots/{result.screenshot_url}" alt="Screenshot" /></div>'

        value_display = ""
        if event and event.value:
            value_display = f' = "{event.value[:30]}{"..." if len(event.value) > 30 else ""}"'

        return f"""
            <tr>
                <td>{result.sequence}</td>
                <td><span class="event-type {event_class}">{event.event_type if event else 'unknown'}</span>{value_display}</td>
                <td>{element_display}</td>
                <td class="{status_class}">{result.status.value}</td>
                <td>{duration_str}</td>
                <td>{details}</td>
            </tr>
        """

    def save_report(self, playback_run_id: str) -> bool:
        """Generate and save report to database."""
        try:
            html = self.generate_report(playback_run_id)
            run = self.db.query(PlaybackRun).filter(PlaybackRun.id == UUID(playback_run_id)).first()
            if run:
                run.report_html = html
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to save playback report: {e}")
            return False
