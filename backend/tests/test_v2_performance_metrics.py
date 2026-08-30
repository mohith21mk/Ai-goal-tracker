import os
import sys
import datetime
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.api.auth import COOKIE_NAME

app = create_app()
client = TestClient(app)


def setup_perf_user(prefix: str):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    
    # Clean up existing test data
    c.execute("DELETE FROM habit_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM habits WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM journal_entries WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM goals WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM missions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()

    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, role) VALUES (?, ?, ?, ?, ?, 1, 1, 'user')",
        (f"{prefix}@perf.test", f"u_{prefix}", pwd, f"Perf {prefix}", f"MKC-{prefix.upper()}"),
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()

    token = create_session(uid)
    return uid, token


def test_zero_state_user_metrics():
    """Verify zero-state user returns clean baselines without division by zero or fake data."""
    uid, token = setup_perf_user("zero_state")
    client.cookies.set(COOKIE_NAME, token)

    # 1. Daily Progress
    res_daily = client.get("/api/progress/daily")
    assert res_daily.status_code == 200
    daily = res_daily.json()
    assert daily["completed_actions"] == 0
    assert daily["total_actions"] == 0
    assert daily["completion_percentage"] == 0
    assert daily["xp_earned_today"] == 0

    # 2. Overall Performance Telemetry
    res_telem = client.get("/api/progress/telemetry")
    assert res_telem.status_code == 200
    telem = res_telem.json()
    assert telem["discipline_score"] == 0.0
    assert telem["mindset_strength"] == 0.0
    assert telem["consistency"] == 0.0
    assert telem["growth_index"] == 0.0
    assert telem["active_days"] == 0
    assert telem["current_streak"] == 0
    assert telem["longest_streak"] == 0
    assert telem["progression"]["total_xp"] == 0
    assert telem["progression"]["level"] == 1


def test_action_completed_today_updates_daily_and_overall_gradually():
    """Completing 1 mission today updates Daily Progress (100%) but keeps Overall Discipline gradual (<80%)."""
    uid, token = setup_perf_user("gradual_action")
    client.cookies.set(COOKIE_NAME, token)

    # Create a mission for today
    res_create = client.post("/api/missions", json={
        "title": "Execute Deep Focus Protocol",
        "category": "discipline",
        "xp_reward": 50,
        "difficulty": "medium"
    })
    assert res_create.status_code == 200
    mission_id = res_create.json()["id"]

    # Before completion:
    daily_pre = client.get("/api/progress/daily").json()
    assert daily_pre["completed_actions"] == 0
    assert daily_pre["total_actions"] >= 1
    assert daily_pre["completion_percentage"] == 0

    # Toggle mission to complete
    res_toggle = client.patch(f"/api/missions/{mission_id}/toggle")
    assert res_toggle.status_code == 200
    assert res_toggle.json()["completed"] is True

    # After completion:
    daily_post = client.get("/api/progress/daily").json()
    assert daily_post["completed_actions"] == 1
    assert daily_post["missions_completed"] == 1
    assert daily_post["completion_percentage"] == 100
    assert daily_post["xp_earned_today"] == 50

    # Overall Performance:
    overall_post = client.get("/api/progress/telemetry").json()
    # Discipline score should be normalized and stable (not 100!)
    assert 0 < overall_post["discipline_score"] < 80
    assert overall_post["active_days"] == 1
    assert overall_post["current_streak"] == 1
    assert overall_post["progression"]["total_xp"] == 50


def test_new_day_resets_daily_progress_without_resetting_overall_performance():
    """Yesterday's completed mission should yield 0 completed actions today in Daily Progress, but preserve Overall Performance."""
    uid, token = setup_perf_user("new_day_reset")
    client.cookies.set(COOKIE_NAME, token)

    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_datetime = f"{yesterday_str} 10:00:00"

    # Insert a mission completed yesterday
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO missions (user_id, title, category, xp_reward, completed, created_at, completed_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
        (uid, "Yesterday Protocol", "mindset", 25, yesterday_datetime, yesterday_datetime)
    )
    # Insert a habit log yesterday
    c.execute(
        "INSERT INTO habits (user_id, title, category, frequency, target_days_per_week, created_at) VALUES (?, ?, ?, ?, 7, ?)",
        (uid, "Morning Meditation", "mindset", "daily", yesterday_datetime)
    )
    habit_id = c.lastrowid
    c.execute(
        "INSERT INTO habit_logs (user_id, habit_id, completed_date) VALUES (?, ?, ?)",
        (uid, habit_id, yesterday_str)
    )
    conn.commit()
    conn.close()

    # 1. Check Daily Progress for TODAY -> must be 0 completed actions
    res_daily = client.get("/api/progress/daily")
    daily = res_daily.json()
    assert daily["completed_actions"] == 0
    assert daily["missions_completed"] == 0
    assert daily["habits_completed"] == 0
    assert daily["xp_earned_today"] == 0
    assert daily["completion_percentage"] == 0

    # 2. Check Overall Performance -> must reflect yesterday's activity
    res_telem = client.get("/api/progress/telemetry")
    telem = res_telem.json()
    assert telem["active_days"] == 1
    # Streak continues if active yesterday
    assert telem["current_streak"] == 1
    assert telem["progression"]["total_xp"] == 40  # 25 XP mission + 15 XP habit
    assert telem["discipline_score"] > 0
    assert telem["mindset_strength"] > 0


def test_historical_activity_multi_day_streak_and_consistency():
    """Verify multi-day activity builds streaks and increases Consistency score."""
    uid, token = setup_perf_user("multi_streak")
    client.cookies.set(COOKIE_NAME, token)

    today = datetime.date.today()
    conn = get_connection()
    c = conn.cursor()

    # Create habit
    c.execute(
        "INSERT INTO habits (user_id, title, category, frequency, target_days_per_week) VALUES (?, ?, ?, ?, 7)",
        (uid, "Daily Cold Shower", "discipline", "daily")
    )
    habit_id = c.lastrowid

    # Log 5 consecutive days up to today
    for i in range(4, -1, -1):
        d_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        c.execute(
            "INSERT INTO habit_logs (user_id, habit_id, completed_date) VALUES (?, ?, ?)",
            (uid, habit_id, d_str)
        )

    conn.commit()
    conn.close()

    # Telemetry should reflect 5-day streak and 5 active days
    telem = client.get("/api/progress/telemetry").json()
    assert telem["active_days"] == 5
    assert telem["current_streak"] == 5
    assert telem["longest_streak"] == 5
    assert telem["consistency"] > 40
    assert telem["progression"]["total_xp"] == 5 * 15


def test_progress_root_endpoint_returns_both_daily_and_overall():
    """GET /api/progress returns backward-compatible fields with embedded daily and overall models."""
    uid, token = setup_perf_user("root_endpoint")
    client.cookies.set(COOKIE_NAME, token)

    res = client.get("/api/progress")
    assert res.status_code == 200
    data = res.json()

    assert "completed" in data
    assert "total" in data
    assert "percentage" in data
    assert "daily" in data
    assert "overall" in data
    assert "discipline_score" in data["overall"]
    assert "completed_actions" in data["daily"]
