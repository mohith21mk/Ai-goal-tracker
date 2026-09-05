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


def test_1_zero_state_user_clean_baseline():
    """11. New users do not receive artificially high scores (clean 0.0 baseline)."""
    uid, token = setup_perf_user("zero_state")
    client.cookies.set(COOKIE_NAME, token)

    res_daily = client.get("/api/progress/daily")
    assert res_daily.status_code == 200
    daily = res_daily.json()
    assert daily["completed_actions"] == 0
    assert daily["completion_percentage"] == 0
    assert daily["xp_earned_today"] == 0

    res_telem = client.get("/api/progress/telemetry")
    assert res_telem.status_code == 200
    telem = res_telem.json()
    assert telem["discipline_score"] == 0.0
    assert telem["mindset_strength"] == 0.0
    assert telem["consistency"] == 0.0
    assert telem["growth_index"] == 0.0
    assert telem["active_days"] == 0
    assert telem["current_streak"] == 0
    assert telem["progression"]["total_xp"] == 0
    assert telem["progression"]["level"] == 1


def test_2_single_action_cannot_jump_overall_scores_to_high_numbers():
    """
    1, 2, 3, 4: Completing one mission (100% daily) cannot jump Discipline, Consistency,
    or Growth to 100, proving today's 100% completion != Overall 100.
    """
    uid, token = setup_perf_user("single_action")
    client.cookies.set(COOKIE_NAME, token)

    res_create = client.post("/api/missions", json={
        "title": "Execute Deep Focus Protocol",
        "category": "discipline",
        "xp_reward": 50,
        "difficulty": "medium"
    })
    assert res_create.status_code == 200
    mission_id = res_create.json()["id"]

    res_toggle = client.patch(f"/api/missions/{mission_id}/toggle")
    assert res_toggle.status_code == 200

    daily = client.get("/api/progress/daily").json()
    assert daily["completed_actions"] == 1
    assert daily["completion_percentage"] == 100
    assert daily["xp_earned_today"] == 50

    overall = client.get("/api/progress/telemetry").json()
    # Overall score must be modest and confidence-adjusted (<= 15.0), NEVER 90-100!
    assert 0 < overall["discipline_score"] <= 15.0
    assert overall["consistency"] <= 15.0
    assert overall["growth_index"] <= 15.0
    assert overall["active_days"] == 1
    assert overall["current_streak"] == 1


def test_3_new_day_resets_daily_progress_only_and_preserves_overall():
    """
    5, 6, 7: Moving to a new day resets daily progress to 0, but does NOT reset overall metrics.
    Yesterday's history continues to affect today's overall performance.
    """
    uid, token = setup_perf_user("new_day_persist")
    client.cookies.set(COOKIE_NAME, token)

    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_datetime = f"{yesterday_str} 10:00:00"

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO missions (user_id, title, category, xp_reward, completed, created_at, completed_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
        (uid, "Yesterday Protocol", "mindset", 25, yesterday_datetime, yesterday_datetime)
    )
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

    # 1. Today's Daily Progress is 0
    daily = client.get("/api/progress/daily").json()
    assert daily["completed_actions"] == 0
    assert daily["missions_completed"] == 0
    assert daily["habits_completed"] == 0
    assert daily["xp_earned_today"] == 0
    assert daily["completion_percentage"] == 0

    # 2. Overall Performance persists and does NOT reset to 0
    telem = client.get("/api/progress/telemetry").json()
    assert telem["active_days"] == 1
    assert telem["current_streak"] == 1
    assert telem["progression"]["total_xp"] == 40
    assert telem["discipline_score"] > 0
    assert telem["mindset_strength"] > 0


def test_4_multi_horizon_historical_activity_compounds_scores():
    """
    8, 9, 10, 12, 13, 14: 30-day, 90-day, and lifetime activity builds sustained Discipline,
    Consistency, cumulative XP, Level, and streaks.
    """
    uid, token = setup_perf_user("multi_horizon")
    client.cookies.set(COOKIE_NAME, token)

    today = datetime.date.today()
    conn = get_connection()
    c = conn.cursor()

    # User created 60 days ago
    created_60d = (today - datetime.timedelta(days=60)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET created_at = ? WHERE id = ?", (created_60d, uid))

    # Insert 40 completed missions spread over 50 days
    for i in range(49, 9, -1):
        d_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        dt_str = f"{d_str} 12:00:00"
        c.execute(
            "INSERT INTO missions (user_id, title, category, xp_reward, completed, created_at, completed_at) VALUES (?, ?, 'discipline', 50, 1, ?, ?)",
            (uid, f"Historical Protocol {i}", dt_str, dt_str)
        )

    # Insert habits logged for the past 14 consecutive days up to today
    c.execute(
        "INSERT INTO habits (user_id, title, category, frequency, target_days_per_week, created_at) VALUES (?, 'Daily Focus', 'discipline', 'daily', 7, ?)",
        (uid, created_60d)
    )
    h_id = c.lastrowid
    for i in range(13, -1, -1):
        d_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        c.execute(
            "INSERT INTO habit_logs (user_id, habit_id, completed_date) VALUES (?, ?, ?)",
            (uid, h_id, d_str)
        )

    # Insert 1 completed goal
    c.execute(
        "INSERT INTO goals (user_id, title, category, status, created_at) VALUES (?, 'Reach Mastery', 'career', 'completed', ?)",
        (uid, created_60d)
    )

    conn.commit()
    conn.close()

    telem = client.get("/api/progress/telemetry").json()
    assert telem["active_days"] >= 40
    assert telem["current_streak"] == 50
    assert telem["longest_streak"] == 50
    assert telem["discipline_score"] >= 45.0  # High sustained historical execution
    assert telem["consistency"] >= 45.0
    assert telem["progression"]["total_xp"] == (40 * 50) + (14 * 15)  # 2210 XP
    assert telem["progression"]["level"] == 5  # floor(2210 / 500) + 1 = 5


def test_5_today_single_action_creates_only_gradual_change_on_mature_account():
    """
    15: On a mature account, 1 new completed action creates a small incremental bump (e.g. +0.2 to +0.8),
    proving today's completion percentage CANNOT dominate overall performance.
    """
    uid, token = setup_perf_user("mature_gradual")
    client.cookies.set(COOKIE_NAME, token)

    today = datetime.date.today()
    conn = get_connection()
    c = conn.cursor()

    created_90d = (today - datetime.timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE users SET created_at = ? WHERE id = ?", (created_90d, uid))

    # Insert 50 historical missions
    for i in range(70, 20, -1):
        d_str = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        dt_str = f"{d_str} 12:00:00"
        c.execute(
            "INSERT INTO missions (user_id, title, category, xp_reward, completed, created_at, completed_at) VALUES (?, ?, 'discipline', 50, 1, ?, ?)",
            (uid, f"Mature Protocol {i}", dt_str, dt_str)
        )
    conn.commit()
    conn.close()

    # Pre-action baseline
    pre_telem = client.get("/api/progress/telemetry").json()
    score_pre = pre_telem["discipline_score"]

    # Complete 1 mission today
    res_create = client.post("/api/missions", json={
        "title": "Today's Action",
        "category": "discipline",
        "xp_reward": 50,
        "difficulty": "easy"
    })
    m_id = res_create.json()["id"]
    client.patch(f"/api/missions/{m_id}/toggle")

    # Post-action telemetry
    post_telem = client.get("/api/progress/telemetry").json()
    score_post = post_telem["discipline_score"]

    diff = round(score_post - score_pre, 1)
    # The change should be small and incremental (<= 2.5), NOT jumping wildly to 100!
    assert 0.0 <= diff <= 2.5
    assert score_post < 90.0
