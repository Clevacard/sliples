"""Tests for streaming API endpoints."""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import RecordingSession, RecordedEvent, RecordingStatus, Project, ApiKey
from app.services.stream_manager import format_event_for_mcp, format_session_summary_for_mcp


class TestStreamingEndpoints:
    """Test streaming API endpoints."""

    def test_list_sessions_empty(self, client: TestClient, api_key_header: dict):
        """Test listing sessions when none exist."""
        response = client.get("/api/v1/stream/sessions", headers=api_key_header)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_sessions_with_filters(self, client: TestClient, db: Session, api_key_header: dict, test_project):
        """Test listing sessions with domain and age filters."""
        # Create test sessions
        session1 = RecordingSession(
            project_id=test_project.id,
            name="Session 1",
            url="https://app.example.com",
            domain="app.example.com",
            user_agent="Chrome",
            status=RecordingStatus.recording,
        )
        session2 = RecordingSession(
            project_id=test_project.id,
            name="Session 2",
            url="https://staging.example.com",
            domain="staging.example.com",
            user_agent="Firefox",
            status=RecordingStatus.recording,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        db.add_all([session1, session2])
        db.commit()

        # Filter by domain
        response = client.get(
            "/api/v1/stream/sessions?domain=app.example.com",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["domain"] == "app.example.com"

        # Filter by user agent
        response = client.get(
            "/api/v1/stream/sessions?user_agent=Firefox",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Firefox" in data[0]["user_agent"]

        # Filter by age (last hour)
        response = client.get(
            "/api/v1/stream/sessions?max_age_seconds=3600",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Session 1"

    def test_list_sessions_includes_metadata(self, client: TestClient, db: Session, api_key_header: dict, test_project):
        """Test that session list includes all required metadata."""
        session = RecordingSession(
            project_id=test_project.id,
            name="Test Session",
            url="https://app.example.com/checkout",
            domain="app.example.com",
            user_agent="Mozilla/5.0...",
            viewport_width=1920,
            viewport_height=1080,
            client_ip="203.0.113.42",
            status=RecordingStatus.recording,
        )
        db.add(session)
        db.commit()

        # Add some events
        for i in range(5):
            event = RecordedEvent(
                session_id=session.id,
                sequence=i,
                timestamp=datetime.utcnow(),
                event_type="click",
            )
            db.add(event)
        db.commit()

        response = client.get("/api/v1/stream/sessions", headers=api_key_header)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        session_data = data[0]
        assert session_data["name"] == "Test Session"
        assert session_data["domain"] == "app.example.com"
        assert session_data["viewport_width"] == 1920
        assert session_data["viewport_height"] == 1080
        assert session_data["client_ip"] == "203.0.113.42"
        assert session_data["event_count"] == 5
        assert session_data["age_seconds"] >= 0
        assert session_data["active_streams"] == 0

    def test_get_stream_info(self, client: TestClient, db: Session, api_key_header: dict, test_project):
        """Test getting stream connection info."""
        session = RecordingSession(
            project_id=test_project.id,
            name="Test Session",
            url="https://app.example.com",
            domain="app.example.com",
            status=RecordingStatus.recording,
        )
        db.add(session)
        db.commit()

        response = client.get(
            f"/api/v1/stream/sessions/{session.id}/info",
            headers=api_key_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session.id)
        assert "/ws" in data["websocket_url"]
        assert data["supports_historic"] is True
        assert data["mcp_format"] == "sliples-stream-v1"

    def test_get_stream_info_not_found(self, client: TestClient, api_key_header: dict):
        """Test stream info for non-existent session."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/stream/sessions/{fake_id}/info",
            headers=api_key_header,
        )
        assert response.status_code == 404

    def test_get_stream_stats(self, client: TestClient, api_key_header: dict):
        """Test getting stream statistics."""
        response = client.get("/api/v1/stream/stats", headers=api_key_header)
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
        assert "total_connections" in data
        assert "sessions_by_domain" in data


class TestEventFormatting:
    """Test MCP event formatting utilities."""

    def test_format_event_basic(self):
        """Test basic event formatting."""
        event = {
            "id": str(uuid4()),
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "url": "https://app.example.com",
            "selector_test_id": "submit-button",
            "tag_name": "button",
            "label_text": "Submit",
        }

        mcp_event = format_event_for_mcp(event)

        assert mcp_event["seq"] == 1
        assert mcp_event["type"] == "click"
        assert mcp_event["target"] == "[data-testid=submit-button]"
        assert mcp_event["tag"] == "button"
        assert mcp_event["label"] == "Submit"

    def test_format_event_selector_priority(self):
        """Test selector priority: test-id > aria > id > css."""
        # Test ID priority
        event1 = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "selector_test_id": "my-button",
            "selector_aria": "Submit",
            "element_id": "btn",
            "selector_css": ".btn.primary",
        }
        mcp1 = format_event_for_mcp(event1)
        assert mcp1["target"] == "[data-testid=my-button]"

        # ARIA priority (no test ID)
        event2 = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "selector_aria": "Submit",
            "element_id": "btn",
            "selector_css": ".btn.primary",
        }
        mcp2 = format_event_for_mcp(event2)
        assert mcp2["target"] == "[aria-label=Submit]"

        # Element ID priority (no test ID or ARIA)
        event3 = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "element_id": "btn",
            "selector_css": ".btn.primary",
        }
        mcp3 = format_event_for_mcp(event3)
        assert mcp3["target"] == "#btn"

        # CSS selector (fallback)
        event4 = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "selector_css": ".btn.primary",
        }
        mcp4 = format_event_for_mcp(event4)
        assert mcp4["target"] == ".btn.primary"

    def test_format_event_password_masking(self):
        """Test password field masking."""
        event = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "input",
            "element_type": "password",
            "value": "super-secret-password",
        }

        mcp_event = format_event_for_mcp(event)
        assert mcp_event["value"] == "***"

    def test_format_event_value_truncation(self):
        """Test long value truncation."""
        long_value = "x" * 300
        event = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "input",
            "value": long_value,
        }

        mcp_event = format_event_for_mcp(event)
        assert len(mcp_event["value"]) == 200

    def test_format_event_with_coordinates(self):
        """Test event with click coordinates."""
        event = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "click",
            "coordinates": {"x": 425, "y": 38},
        }

        mcp_event = format_event_for_mcp(event)
        assert mcp_event["pos"] == {"x": 425, "y": 38}

    def test_format_event_with_key_info(self):
        """Test event with keyboard info."""
        event = {
            "sequence": 1,
            "timestamp": "2026-06-17T14:30:00Z",
            "event_type": "keydown",
            "key_info": {"key": "Enter", "ctrl": True, "shift": False},
        }

        mcp_event = format_event_for_mcp(event)
        assert mcp_event["key"] == {"key": "Enter", "ctrl": True, "shift": False}

    def test_format_session_summary(self):
        """Test session metadata formatting."""
        session = {
            "id": str(uuid4()),
            "name": "Test Session",
            "url": "https://app.example.com",
            "domain": "app.example.com",
            "status": "recording",
            "user_agent": "Chrome",
            "viewport_width": 1920,
            "viewport_height": 1080,
            "created_at": "2026-06-17T14:30:00Z",
            "stopped_at": None,
            "event_count": 45,
            "client_ip": "203.0.113.42",
        }

        summary = format_session_summary_for_mcp(session)

        assert summary["name"] == "Test Session"
        assert summary["domain"] == "app.example.com"
        assert summary["viewport"] == "1920x1080"
        assert summary["event_count"] == 45
        assert summary["stopped"] is None


@pytest.fixture
def api_key_header(db: Session, test_project) -> dict:
    """Create API key and return header dict."""
    import bcrypt

    key_string = "test_api_key_12345678"
    key_hash = bcrypt.hashpw(key_string.encode(), bcrypt.gensalt()).decode()

    api_key = ApiKey(
        name="Test Key",
        key_hash=key_hash,
        key_prefix=key_string[:8],
        project_id=test_project.id,
        active=True,
    )
    db.add(api_key)
    db.commit()

    return {"X-API-Key": key_string}


@pytest.fixture
def test_project(db: Session):
    """Create test project."""
    project = Project(
        name="Test Project",
        slug="test-project",
    )
    db.add(project)
    db.commit()
    return project
