"""
SQLAlchemy ORM Models Compatibility Layer.
Re-exports canonical models from app.models with *ORM aliases for backward compatibility.
"""
from .models import (
    Base,
    User,
    AppSession,
    PasswordReset,
    EmailVerification,
    UserSettings,
    Goal,
    Habit,
    HabitLog,
    Mission,
    JournalEntry,
    LifeBlueprint,
    BlueprintArea,
    BlueprintPhase,
    BlueprintMilestone,
    CommunityPost,
    CommunityLike,
    CommunityComment,
    UserConnection,
    Conversation,
    ConversationMember,
    Message,
    ChatMessage,
    Notification,
    AIActivityLog,
    UserCredential,
)

# Compatibility Aliases for tests and legacy references
UserORM = User
AppSessionORM = AppSession
PasswordResetORM = PasswordReset
EmailVerificationORM = EmailVerification
UserSettingORM = UserSettings
UserSettingsORM = UserSettings
GoalORM = Goal
HabitORM = Habit
HabitLogORM = HabitLog
MissionORM = Mission
JournalEntryORM = JournalEntry
LifeBlueprintORM = LifeBlueprint
BlueprintAreaORM = BlueprintArea
BlueprintPhaseORM = BlueprintPhase
BlueprintMilestoneORM = BlueprintMilestone
CommunityPostORM = CommunityPost
CommunityLikeORM = CommunityLike
CommunityCommentORM = CommunityComment
UserConnectionORM = UserConnection
ConversationORM = Conversation
ConversationMemberORM = ConversationMember
MessageORM = Message
ChatMessageORM = ChatMessage
NotificationORM = Notification
AIActivityLogORM = AIActivityLog
UserCredentialORM = UserCredential

__all__ = [
    "Base",
    "User", "UserORM",
    "AppSession", "AppSessionORM",
    "PasswordReset", "PasswordResetORM",
    "EmailVerification", "EmailVerificationORM",
    "UserSettings", "UserSettingORM", "UserSettingsORM",
    "Goal", "GoalORM",
    "Habit", "HabitORM",
    "HabitLog", "HabitLogORM",
    "Mission", "MissionORM",
    "JournalEntry", "JournalEntryORM",
    "LifeBlueprint", "LifeBlueprintORM",
    "BlueprintArea", "BlueprintAreaORM",
    "BlueprintPhase", "BlueprintPhaseORM",
    "BlueprintMilestone", "BlueprintMilestoneORM",
    "CommunityPost", "CommunityPostORM",
    "CommunityLike", "CommunityLikeORM",
    "CommunityComment", "CommunityCommentORM",
    "UserConnection", "UserConnectionORM",
    "Conversation", "ConversationORM",
    "ConversationMember", "ConversationMemberORM",
    "Message", "MessageORM",
    "ChatMessage", "ChatMessageORM",
    "Notification", "NotificationORM",
    "AIActivityLog", "AIActivityLogORM",
    "UserCredential", "UserCredentialORM",
]
