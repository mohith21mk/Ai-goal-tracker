from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index, func
)
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Integer, default=1)
    mkc_id = Column(String(255), unique=True, nullable=True, index=True)
    avatar_initials = Column(String(10), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AppSessionORM(Base):
    __tablename__ = "app_sessions"

    token = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)

class GoalORM(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="general")
    status = Column(String(50), default="active")
    target_date = Column(String(20), nullable=True)
    blueprint_id = Column(Integer, nullable=True)
    milestone_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MissionORM(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="general")
    time = Column(String(50), default="15 min")
    difficulty = Column(String(50), default="easy")
    xp_reward = Column(Integer, default=10)
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MessageORM(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class HabitORM(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="general")
    frequency = Column(String(50), default="daily")
    target_days_per_week = Column(Integer, default=7)
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class HabitLogORM(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    completed_date = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JournalEntryORM(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entry_date = Column(String(20), nullable=False)
    mood = Column(String(50), default="focused")
    energy_level = Column(Integer, default=7)
    wins_text = Column(Text, nullable=True)
    challenges_text = Column(Text, nullable=True)
    learnings_text = Column(Text, nullable=True)
    growth_next_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class LifeBlueprintORM(Base):
    __tablename__ = "life_blueprints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vision_statement = Column(Text, nullable=True)
    core_values = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BlueprintAreaORM(Base):
    __tablename__ = "blueprint_areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="target")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlueprintPhaseORM(Base):
    __tablename__ = "blueprint_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    area_id = Column(Integer, ForeignKey("blueprint_areas.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=1)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlueprintMilestoneORM(Base):
    __tablename__ = "blueprint_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("blueprint_phases.id"), nullable=False, index=True)
    blueprint_id = Column(Integer, ForeignKey("life_blueprints.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    target_date = Column(String(20), nullable=True)
    completed = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class UserSettingORM(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    theme = Column(String(50), default="dark")
    notifications_enabled = Column(Integer, default=1)
    email_notifications = Column(Integer, default=1)
    daily_reminder_time = Column(String(20), default="09:00")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommunityPostORM(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(100), default="general")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommunityLikeORM(Base):
    __tablename__ = "community_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CommunityCommentORM(Base):
    __tablename__ = "community_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationORM(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ConversationMemberORM(Base):
    __tablename__ = "conversation_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

class NotificationORM(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(50), default="info")
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
