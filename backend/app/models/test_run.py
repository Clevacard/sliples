"""TestRun and TestResult models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class RunStatus(str, Enum):
    """Test run status."""

    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ERROR = "error"


class StepStatus(str, Enum):
    """Test step status."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestRun(Base):
    """A test execution run."""

    __tablename__ = "test_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    scenario_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id"), nullable=False)
    status = Column(SQLEnum(RunStatus), default=RunStatus.QUEUED)
    browser = Column(String(50), nullable=False)
    browser_version = Column(String(50), default="latest")
    triggered_by = Column(String(100), nullable=True)
    parallel = Column(Boolean, default=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    report_html = Column(Text, nullable=True)
    email_sent = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    progress_message = Column(String(500), nullable=True)  # Progress status during execution
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="test_runs")
    environment = relationship("Environment", back_populates="test_runs")
    results = relationship("TestResult", back_populates="test_run", cascade="all, delete-orphan")


class TestResult(Base):
    """Result of a single test step."""

    __tablename__ = "test_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_run_id = Column(UUID(as_uuid=True), ForeignKey("test_runs.id"), nullable=False)
    scenario_id = Column(UUID(as_uuid=True), nullable=True)
    scenario_name = Column(String(255), nullable=True)
    step_name = Column(String(500), nullable=False)
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING)
    duration_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_run = relationship("TestRun", back_populates="results")
