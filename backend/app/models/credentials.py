from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class UserCredential(Base):
    __tablename__ = "user_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_type = Column(String(50), nullable=False)  # streak_badge, mission_badge, blueprint_badge, mastery_badge
    slug = Column(String(100), nullable=False)  # streak_7, streak_30, streak_100, missions_50, blueprint_milestone_1, mastery_level_20
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tier = Column(String(50), default="bronze")  # bronze, silver, gold, platinum, diamond
    xp_value = Column(Integer, default=50)
    evidence_type = Column(String(50), nullable=False)  # habit_streak, mission_count, milestone_completed, mastery_level
    evidence_id = Column(String(255), nullable=True)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "slug", name="uq_user_credential_slug"),
    )
