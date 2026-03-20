"""TestSession model for interactive test sessions."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from sqlalchemy.orm import relationship

from app.database import Base


class SessionStatus(str, Enum):
    """Interactive test session status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


class TestSession(Base):
    """An interactive test session for human testers."""

    __tablename__ = "test_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=True)
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id"), nullable=False)
    status = Column(
        PgEnum('active', 'paused', 'completed', 'terminated', name='sessionstatus', create_type=False),
        default='active'
    )
    browser_type = Column(String(50), default="chromium")
    current_step_index = Column(String(50), default="0")
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Store executed step results as JSON
    step_results = Column(JSONB, default=list)

    # Store current browser state info
    current_url = Column(String(2000), nullable=True)
    current_title = Column(String(500), nullable=True)
    last_screenshot_url = Column(String(500), nullable=True)

    # Logs for the session
    logs = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", backref="test_sessions")
    scenario = relationship("Scenario", backref="test_sessions")
    environment = relationship("Environment", backref="test_sessions")
