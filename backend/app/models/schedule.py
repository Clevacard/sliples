"""Schedule model for test run scheduling."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class Schedule(Base):
    """A scheduled test run configuration."""

    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    cron_expression = Column(String(100), nullable=False)

    # Timezone for cron evaluation (defaults to UTC)
    timezone = Column(String(50), default="UTC")

    # What to run
    scenario_tags = Column(ARRAY(String), default=[])
    scenario_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])

    # Where and how to run
    environment_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    browsers = Column(ARRAY(String), default=["chromium"])

    # Status
    enabled = Column(Boolean, default=True)

    # Tracking
    created_by = Column(String(255), nullable=True)  # User email or API key name
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_run_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to last test run

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="schedules")
