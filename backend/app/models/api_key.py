"""API Key model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base


class ApiKey(Base):
    """API key for authentication."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(10), nullable=False)  # For identification (first 8 chars)
    environment_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
