"""Environment and BrowserConfig models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Environment(Base):
    """Test environment configuration."""

    __tablename__ = "environments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(500), nullable=False)
    credentials_env = Column(String(100), nullable=True)
    variables = Column(JSON, default={})
    retention_days = Column(Integer, default=365)
    created_at = Column(DateTime, default=datetime.utcnow)

    browser_configs = relationship(
        "BrowserConfig", back_populates="environment", cascade="all, delete-orphan"
    )
    test_runs = relationship("TestRun", back_populates="environment")


class BrowserConfig(Base):
    """Browser configuration per environment."""

    __tablename__ = "browser_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    environment_id = Column(UUID(as_uuid=True), ForeignKey("environments.id"), nullable=False)
    browser = Column(String(50), nullable=False)  # chrome, firefox
    version = Column(String(50), default="latest")
    channel = Column(String(50), default="stable")  # stable, beta, dev

    environment = relationship("Environment", back_populates="browser_configs")
