import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_connection
from app.db_session import SessionLocal
from app.models_orm import UserORM, GoalORM, MissionORM, HabitORM, HabitLogORM, JournalEntryORM

client = TestClient(app)

def setup_module(module):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM habits WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM journal_entries WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM missions WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM goals WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com'))")
    cursor.execute("DELETE FROM users WHERE username IN ('user_2b_a', 'user_2b_b') OR email IN ('user2ba@example.com', 'user2bb@example.com')")
    conn.commit()
    conn.close()

def test_phase2b_end_to_end_cloud_orm_validation():
    # 1. Register User A
    resp_reg_a = client.post("/api/auth/register", json={
        "email": "user2ba@example.com",
        "password": "Password123!",
        "full_name": "User 2B A",
        "username": "user_2b_a"
    })
    assert resp_reg_a.status_code == 200
    token_a = resp_reg_a.cookies.get("mkc_session") or resp_reg_a.json().get("session_token")
    headers_a = {"Cookie": f"mkc_session={token_a}"}

    # 2. Register User B (for isolation validation)
    resp_reg_b = client.post("/api/auth/register", json={
        "email": "user2bb@example.com",
        "password": "Password123!",
        "full_name": "User 2B B",
        "username": "user_2b_b"
    })
    assert resp_reg_b.status_code == 200
    token_b = resp_reg_b.cookies.get("mkc_session") or resp_reg_b.json().get("session_token")
    headers_b = {"Cookie": f"mkc_session={token_b}"}

    # 3. Create Goal for User A
    resp_goal_a = client.post("/api/goals", json={
        "title": "Phase 2B Freedom Goal",
        "description": "Validation of cloud database goals API",
        "category": "finance",
        "target_date": "2028-12-31"
    }, headers=headers_a)
    assert resp_goal_a.status_code == 200
    goal_a_id = resp_goal_a.json()["id"]

    # 4. Create Mission for User A
    resp_mission_a = client.post("/api/missions", json={
        "title": "Phase 2B Protocol Mission",
        "category": "mindset",
        "xp_reward": 15,
        "goal_id": goal_a_id
    }, headers=headers_a)
    assert resp_mission_a.status_code == 200
    mission_a_id = resp_mission_a.json()["id"]

    # Toggle mission completed for User A
    resp_toggle = client.patch(f"/api/missions/{mission_a_id}/toggle", headers=headers_a)
    assert resp_toggle.status_code == 200
    assert resp_toggle.json()["completed"] is True or resp_toggle.json()["completed"] == 1

    # 5. Create Habit for User A
    resp_habit = client.post("/api/habits", json={
        "title": "Daily 2B Protocol Habit",
        "category": "health",
        "frequency": "daily",
        "target_days_per_week": 7
    }, headers=headers_a)
    assert resp_habit.status_code == 200

    # 6. Post Journal Reflection for User A
    resp_journal = client.post("/api/journal", json={
        "entry_date": "2026-08-12",
        "mood": "focused",
        "energy_level": 8,
        "wins_text": "Completed Phase 2B validation test suite.",
        "challenges_text": "None",
        "learnings_text": "SQLAlchemy ORM integration complete.",
        "growth_next_text": "Proceeding to Phase 2C RAG retrieval."
    }, headers=headers_a)
    assert resp_journal.status_code == 200

    # 7. Validate Telemetry API for User A
    resp_telem_a = client.get("/api/telemetry", headers=headers_a)
    assert resp_telem_a.status_code == 200
    telem_a = resp_telem_a.json()
    assert telem_a["mission_completion"]["completed"] >= 1
    assert telem_a["xp_earned"] >= 15
    assert len(telem_a["sparklines"]["discipline_score"]) == 7

    # 8. Validate User Isolation for User B (User B must have 0 missions, 0 XP, 0 goals)
    resp_telem_b = client.get("/api/telemetry", headers=headers_b)
    assert resp_telem_b.status_code == 200
    telem_b = resp_telem_b.json()
    assert telem_b["mission_completion"]["completed"] == 0
    assert telem_b["xp_earned"] == 0
    assert telem_b["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 0]

    # 9. Validate Existing AI Coach Chat Endpoint
    resp_coach = client.post("/api/coach/chat", json={
        "message": "What is my current protocol status?"
    }, headers=headers_a)
    assert resp_coach.status_code == 200
    assert "reply" in resp_coach.json() or "response" in resp_coach.json()

    print("Phase 2B End-to-End Cloud Validation PASSED successfully.")

def teardown_module(module):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('user_2b_a', 'user_2b_b')")
    conn.commit()
