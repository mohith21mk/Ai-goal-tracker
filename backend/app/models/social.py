from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), default="general")
    credential_id = Column(Integer, ForeignKey("user_credentials.id", ondelete="SET NULL"), nullable=True)
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    likes = relationship("CommunityLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("CommunityComment", back_populates="post", cascade="all, delete-orphan")


class CommunityLike(Base):
    __tablename__ = "community_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like"),
    )

    post = relationship("CommunityPost", back_populates="likes")


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    post = relationship("CommunityPost", back_populates="comments")


class UserConnection(Base):
    __tablename__ = "user_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")  # pending, accepted, blocked
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("requester_id", "recipient_id", name="uq_user_connection"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), default="direct")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), onupdate=lambda: datetime.now(UTC))

    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    conversation = relationship("Conversation", back_populates="members")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(50), nullable=False)  # user or coach
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())


class UserFollow(Base):
    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_user_follow"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")
    attachment_url = Column(Text, nullable=True)
    attachment_metadata = Column(Text, nullable=True)
    attachment_duration = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    read_at = Column(DateTime, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    data = Column(Text, nullable=True)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())


class AIActivityLog(Base):
    __tablename__ = "ai_activity_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String(100))
    target_id = Column(Integer)
    status = Column(String(50), default="success")
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
