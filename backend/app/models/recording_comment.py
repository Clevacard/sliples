"""Comment models for recording sessions (user feedback on the journey)."""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CommentType(str, enum.Enum):
    """Type of comment left on a recording."""
    bug = "bug"
    issue = "issue"
    improvement = "improvement"


class RecordingComment(Base):
    """A comment attached to a point in a recorded session's journey."""

    __tablename__ = "recording_comments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("recording_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(Enum(CommentType), nullable=False)
    text = Column(Text, nullable=False)

    # Journey anchor (where in the recording the comment applies)
    anchor_sequence = Column(Integer, nullable=True)  # RecordedEvent.sequence semantics
    anchor_timestamp = Column(DateTime, nullable=True)
    anchor_url = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("RecordingSession", back_populates="comments")
    user = relationship("User")
    edits = relationship("RecordingCommentEdit", back_populates="comment", cascade="all, delete-orphan", order_by="RecordingCommentEdit.created_at")


class RecordingCommentEdit(Base):
    """Append-only log of edits to a recording comment (who, when, previous text)."""

    __tablename__ = "recording_comment_edits"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    comment_id = Column(PG_UUID(as_uuid=True), ForeignKey("recording_comments.id", ondelete="CASCADE"), nullable=False)
    editor_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    previous_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    comment = relationship("RecordingComment", back_populates="edits")
    editor = relationship("User")
