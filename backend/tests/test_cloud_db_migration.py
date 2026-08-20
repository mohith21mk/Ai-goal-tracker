import pytest
from app.database import init_db
from app.db_session import SessionLocal
from app.models_orm import (
    UserORM, AppSessionORM, GoalORM, MissionORM, MessageORM, HabitORM, HabitLogORM,
    JournalEntryORM, LifeBlueprintORM, BlueprintAreaORM, BlueprintPhaseORM, BlueprintMilestoneORM,
    UserSettingORM, CommunityPostORM, CommunityLikeORM, CommunityCommentORM, ConversationORM,
    ConversationMemberORM, ChatMessageORM, NotificationORM
)

def setup_module(module):
    init_db()

def test_sqlalchemy_orm_models_cloud_migration_readiness():
    db = SessionLocal()
    try:
        # Clean up test user
        existing_users = db.query(UserORM).filter((UserORM.username == "cloud_test_user") | (UserORM.email == "cloud_test@example.com") | (UserORM.mkc_id == "MKC-CLOUD-001")).all()
        for u in existing_users:
            db.query(HabitLogORM).filter(HabitLogORM.user_id == u.id).delete()
            db.query(HabitORM).filter(HabitORM.user_id == u.id).delete()
            db.query(JournalEntryORM).filter(JournalEntryORM.user_id == u.id).delete()
            db.query(MissionORM).filter(MissionORM.user_id == u.id).delete()
            db.query(GoalORM).filter(GoalORM.user_id == u.id).delete()
            db.query(UserORM).filter(UserORM.id == u.id).delete()
        db.commit()

        # 1. Create User via ORM
        user = UserORM(
            email="cloud_test@example.com",
            full_name="Cloud Test User",
            username="cloud_test_user",
            mkc_id="MKC-CLOUD-001",
            avatar_initials="CT",
            bio="Cloud DB Migration Test User"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None

        # 2. Create Goal & Mission via ORM
        goal = GoalORM(user_id=user.id, title="Cloud Goal", category="wealth")
        db.add(goal)
        db.commit()
        db.refresh(goal)

        mission = MissionORM(user_id=user.id, goal_id=goal.id, title="Cloud Mission", xp_reward=20, completed=1)
        db.add(mission)
        db.commit()
        db.refresh(mission)

        assert mission.id is not None
        assert mission.goal_id == goal.id

        # 3. Create Habit & Habit Log via ORM
        habit = HabitORM(user_id=user.id, title="Cloud Habit", category="health")
        db.add(habit)
        db.commit()
        db.refresh(habit)

        log = HabitLogORM(habit_id=habit.id, user_id=user.id, completed_date="2026-08-12")
        db.add(log)
        db.commit()

        # 4. Create Journal Entry via ORM
        journal = JournalEntryORM(user_id=user.id, entry_date="2026-08-12", mood="focused", energy_level=9)
        db.add(journal)
        db.commit()

        # Query and verify
        fetched_user = db.query(UserORM).filter(UserORM.id == user.id).first()
        assert fetched_user.email == "cloud_test@example.com"

        fetched_missions = db.query(MissionORM).filter(MissionORM.user_id == user.id).all()
        assert len(fetched_missions) == 1
        assert fetched_missions[0].title == "Cloud Mission"

        # Cleanup
        db.query(HabitLogORM).filter(HabitLogORM.user_id == user.id).delete()
        db.query(HabitORM).filter(HabitORM.user_id == user.id).delete()
        db.query(JournalEntryORM).filter(JournalEntryORM.user_id == user.id).delete()
        db.query(MissionORM).filter(MissionORM.user_id == user.id).delete()
        db.query(GoalORM).filter(GoalORM.user_id == user.id).delete()
        db.query(UserORM).filter(UserORM.id == user.id).delete()
        db.commit()
    finally:
        db.close()
