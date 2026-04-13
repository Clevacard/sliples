"""Recording session models for UI event capture."""

import enum
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base


class RecordingStatus(str, enum.Enum):
    """Recording session status."""
    recording = "recording"
    stopped = "stopped"
    converted = "converted"


class RecordingSession(Base):
    """A recording session capturing UI events from a website."""

    __tablename__ = "recording_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)  # Starting URL
    status = Column(Enum(RecordingStatus), default=RecordingStatus.recording)
    user_agent = Column(Text, nullable=True)
    viewport_width = Column(Integer, nullable=True)
    viewport_height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="recording_sessions")
    events = relationship("RecordedEvent", back_populates="session", cascade="all, delete-orphan", order_by="RecordedEvent.sequence")


class RecordedEvent(Base):
    """A single recorded UI event."""

    __tablename__ = "recorded_events"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("recording_sessions.id"), nullable=False)
    sequence = Column(Integer, nullable=False)  # Order of events
    timestamp = Column(DateTime, nullable=False)
    event_type = Column(String(50), nullable=False)  # click, input, select, navigation, etc.

    # Element identification (multiple strategies for resilient playback)
    selector_css = Column(Text, nullable=True)
    selector_xpath = Column(Text, nullable=True)
    selector_text = Column(Text, nullable=True)  # Text content for text-based selection
    selector_test_id = Column(String(255), nullable=True)  # data-testid attribute
    selector_aria = Column(String(255), nullable=True)  # aria-label

    # Element metadata
    tag_name = Column(String(50), nullable=True)
    element_id = Column(String(255), nullable=True)
    element_classes = Column(Text, nullable=True)  # JSON array
    element_name = Column(String(255), nullable=True)  # form field name
    element_type = Column(String(50), nullable=True)  # input type
    element_role = Column(String(50), nullable=True)  # ARIA role
    label_text = Column(Text, nullable=True)  # Associated label text
    placeholder = Column(Text, nullable=True)

    # Event data
    value = Column(Text, nullable=True)  # Input value, selected option, etc.
    url = Column(Text, nullable=True)  # Current page URL
    coordinates = Column(JSON, nullable=True)  # {x, y} for clicks
    key_info = Column(JSON, nullable=True)  # For keyboard events

    # Additional context
    extra_data = Column(JSON, nullable=True)  # Any additional event-specific data

    # Relationships
    session = relationship("RecordingSession", back_populates="events")
