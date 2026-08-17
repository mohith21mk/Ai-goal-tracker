from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="Normal", nullable=False)
    status = Column(String(20), default="new", nullable=False, index=True)
    admin_notes = Column(Text, nullable=True)
    page_url = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="feedback_submissions")
