from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Integer, default=1)
    mkc_id = Column(String(255), unique=True, index=True)
    avatar_initials = Column(String(10))
    bio = Column(Text)
    role = Column(String(50), default="user", nullable=False)
    email_verified = Column(Integer, default=0)
    verified_at = Column(DateTime)
    onboarding_completed = Column(Integer, default=0)
    onboarding_data = Column(Text)
    deactivated_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("AppSession", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(50), default="dark")
    notifications_enabled = Column(Integer, default=1)
    coach_style = Column(String(50), default="strategic")
    daily_reminder_time = Column(String(50), default="08:00")
    profile_visibility = Column(String(50), default="public")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="settings")


class AppSession(Base):
    __tablename__ = "app_sessions"

    token = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    revoked_at = Column(DateTime)
    user_agent = Column(Text)
    ip_address = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)

    user = relationship("User", back_populates="password_resets")


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    token_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime)

    user = relationship("User", back_populates="email_verifications")
