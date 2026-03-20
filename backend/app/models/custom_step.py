"""Custom step definition model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CustomStep(Base):
    """User-defined Gherkin step definition."""

    __tablename__ = "custom_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("scenario_repos.id"), nullable=True)
    name = Column(String(255), nullable=False)
    pattern = Column(String(500), nullable=False)  # Gherkin pattern
    code = Column(Text, nullable=False)  # Python implementation
    committed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repo = relationship("ScenarioRepo", back_populates="custom_steps")
