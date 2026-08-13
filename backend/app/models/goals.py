from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), default="general")
    status = Column(String(50), default="active")
    target_date = Column(String(100))
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id", ondelete="SET NULL"))
    milestone_id = Column(Integer, ForeignKey("blueprint_milestones.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    user = relationship("User")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), default="general")
    frequency = Column(String(50), default="daily")
    target_days_per_week = Column(Integer, default=7)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    logs = relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan")


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey("habits.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    completed_date = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("habit_id", "completed_date", name="uq_habit_date"),
    )

    habit = relationship("Habit", back_populates="logs")


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), default="general")
    time = Column(String(50), default="15 min")
    difficulty = Column(String(50), default="easy")
    xp_reward = Column(Integer, default=10)
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    entry_date = Column(String(50), nullable=False)
    mood = Column(String(50), nullable=False, default="focused")
    energy_level = Column(Integer, nullable=False, default=7)
    wins_text = Column(Text)
    challenges_text = Column(Text)
    learnings_text = Column(Text)
    growth_next_text = Column(Text)
    ai_analysis = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("user_id", "entry_date", name="uq_journal_date"),
    )


class LifeBlueprint(Base):
    __tablename__ = "life_blueprints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    vision = Column(Text)
    target_date = Column(String(100))
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))


class BlueprintArea(Base):
    __tablename__ = "blueprint_areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default="🎯")
    position = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())


class BlueprintPhase(Base):
    __tablename__ = "blueprint_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id", ondelete="CASCADE"), nullable=False)
    area_id = Column(Integer, ForeignKey("blueprint_areas.id", ondelete="SET NULL"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    phase_number = Column(Integer, nullable=False)
    status = Column(String(50), default="pending")
    position = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))


class BlueprintMilestone(Base):
    __tablename__ = "blueprint_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("blueprint_phases.id", ondelete="CASCADE"), nullable=False)
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    target_date = Column(String(100))
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime)
    position = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))
