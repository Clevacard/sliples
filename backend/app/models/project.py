"""Project and ProjectMember models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ProjectRole(str, Enum):
    """Project membership role enumeration."""
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class Project(Base):
    """Project - top-level organizational unit for grouping environments, scenarios, etc."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    environments = relationship("Environment", back_populates="project", cascade="all, delete-orphan")
    scenarios = relationship("Scenario", back_populates="project", cascade="all, delete-orphan")
    repos = relationship("ScenarioRepo", back_populates="project", cascade="all, delete-orphan")
    custom_steps = relationship("CustomStep", back_populates="project", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="project", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="project", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="project", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, slug={self.slug})>"


class ProjectMember(Base):
    """Association between User and Project with role."""

    __tablename__ = "project_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(ProjectRole), default=ProjectRole.member, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )

    def __repr__(self) -> str:
        return f"<ProjectMember(project_id={self.project_id}, user_id={self.user_id}, role={self.role})>"
