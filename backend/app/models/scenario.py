"""Scenario and ScenarioRepo models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


class ScenarioRepo(Base):
    """Git repository containing test scenarios."""

    __tablename__ = "scenario_repos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    git_url = Column(String(500), nullable=False)
    branch = Column(String(100), default="main")
    sync_path = Column(String(255), default="scenarios")
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="repos")
    scenarios = relationship("Scenario", back_populates="repo", cascade="all, delete-orphan")
    custom_steps = relationship("CustomStep", back_populates="repo", cascade="all, delete-orphan")


class Scenario(Base):
    """Test scenario parsed from a .feature file."""

    __tablename__ = "scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("scenario_repos.id"), nullable=True)
    name = Column(String(255), nullable=False)
    feature_path = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="scenarios")
    repo = relationship("ScenarioRepo", back_populates="scenarios")
