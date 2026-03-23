"""Page model for named URL mappings."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Page(Base):
    """Named page with URL path mapping.

    Pages belong to a project and define named locations (e.g., "Login", "Dashboard")
    with their corresponding paths. The full URL is constructed as:
    environment.base_url + page.path

    For Gherkin steps like: When I navigate to the "Login" page
    """

    __tablename__ = "pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    name = Column(String(100), nullable=False)  # "Login", "Dashboard", "Product List"
    path = Column(String(500), nullable=False)  # "/login", "/dashboard", "/products"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="pages")
    overrides = relationship(
        "PageEnvironmentOverride",
        back_populates="page",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_page_project_name"),
    )


class PageEnvironmentOverride(Base):
    """Override page path for a specific environment.

    Allows different paths per environment when they don't follow the standard pattern.
    For example, if staging uses /auth/login instead of /login.
    """

    __tablename__ = "page_environment_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False
    )
    environment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False
    )
    path = Column(String(500), nullable=False)  # Override path for this environment
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    page = relationship("Page", back_populates="overrides")
    environment = relationship("Environment")

    __table_args__ = (
        UniqueConstraint("page_id", "environment_id", name="uq_page_env_override"),
    )
