"""Playback run models for recording replay."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base


class PlaybackStatus(str, enum.Enum):
    """Playback run status."""
    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"


class PlaybackStepStatus(str, enum.Enum):
    """Individual step status."""
    pending = "pending"
    passed = "passed"
    failed = "failed"
    skipped = "skipped"


class PlaybackRun(Base):
    """A playback execution of a recording session."""

    __tablename__ = "playback_runs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("recording_sessions.id"), nullable=False)
    environment_id = Column(PG_UUID(as_uuid=True), ForeignKey("environments.id"), nullable=False)
    browser = Column(String(50), nullable=False)  # chrome, firefox
    status = Column(Enum(PlaybackStatus), default=PlaybackStatus.pending)

    # Viewport from recording (or override)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)

    # Timing
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Progress tracking
    progress_message = Column(String(500), nullable=True)

    # Results summary
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)

    # Report HTML (like test runs)
    report_html = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("RecordingSession")
    environment = relationship("Environment")
    step_results = relationship("PlaybackStepResult", back_populates="playback_run", cascade="all, delete-orphan", order_by="PlaybackStepResult.sequence")


class PlaybackStepResult(Base):
    """Result of a single playback step."""

    __tablename__ = "playback_step_results"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    playback_run_id = Column(PG_UUID(as_uuid=True), ForeignKey("playback_runs.id"), nullable=False)
    event_id = Column(PG_UUID(as_uuid=True), ForeignKey("recorded_events.id"), nullable=False)
    sequence = Column(Integer, nullable=False)

    status = Column(Enum(PlaybackStepStatus), default=PlaybackStepStatus.pending)
    duration_ms = Column(Integer, nullable=True)

    # Error details
    error_message = Column(Text, nullable=True)
    selector_used = Column(Text, nullable=True)  # Which selector worked

    # Screenshot (S3 key)
    screenshot_url = Column(String(500), nullable=True)

    # Failure diagnostics
    console_logs = Column(Text, nullable=True)  # Browser console logs (JSON)
    dom_snapshot_url = Column(String(500), nullable=True)  # S3 key for DOM HTML
    page_url = Column(Text, nullable=True)  # Current page URL at failure

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    playback_run = relationship("PlaybackRun", back_populates="step_results")
    event = relationship("RecordedEvent")
