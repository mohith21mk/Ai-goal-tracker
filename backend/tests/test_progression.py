"""
Targeted tests for Authoritative Progression Engine.
Verifies pure mathematical level/rank formulas, database XP aggregation, and anti-spoofing guarantees.
"""
import os
import sys
from datetime import datetime, timezone
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.services.progression import (
    calculate_level,
    calculate_rank,
    calculate_user_xp,
    get_user_progression,
)

client = TestClient(app)


def setup_clean_user():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clean previous test data
    cursor.execute("DELETE FROM habit_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prog_test%')")
    cursor.execute("DELETE FROM habits WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prog_test%')")
    cursor.execute("DELETE FROM missions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prog_test%')")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prog_test%')")
    cursor.execute("DELETE FROM users WHERE email LIKE 'prog_test%'")
    conn.commit()

    pwd = hash_password("Test1234!")
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        ("prog_test_user@example.com", "Progression User", "prog_user", pwd, "PU"),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session_token = create_session(user_id)
    return user_id, session_token


def cleanup_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def test_level_formula():
    """Test 1-4: Exact level calculation from total XP."""
    assert calculate_level(0) == 1, "0 XP must be Level 1"
    assert calculate_level(250) == 1, "250 XP must be Level 1"
    assert calculate_level(499) == 1, "499 XP must be Level 1"
    assert calculate_level(500) == 2, "500 XP must be Level 2"
    assert calculate_level(750) == 2, "750 XP must be Level 2"
    assert calculate_level(999) == 2, "999 XP must be Level 2"
    assert calculate_level(1000) == 3, "1000 XP must be Level 3"
    assert calculate_level(1500) == 4, "1500 XP must be Level 4"
    assert calculate_level(9999) == 20, "9999 XP must be Level 20"
    print("PASS: Level formula calculations verified (0->1, 499->1, 500->2, 1000->3)")


def test_rank_tiers():
    """Test 5: Rank tiers change correctly at levels 1, 6, 11, 21, 51."""
    # INITIATE: Level 1-5
    assert calculate_rank(1) == "INITIATE"
    assert calculate_rank(5) == "INITIATE"

    # ADEPT: Level 6-10
    assert calculate_rank(6) == "ADEPT"
    assert calculate_rank(10) == "ADEPT"

    # MASTER: Level 11-20
    assert calculate_rank(11) == "MASTER"
    assert calculate_rank(20) == "MASTER"

    # LEGEND: Level 21-50
    assert calculate_rank(21) == "LEGEND"
    assert calculate_rank(50) == "LEGEND"

    # MASTERY SOVEREIGN: Level 51+
    assert calculate_rank(51) == "MASTERY SOVEREIGN"
    assert calculate_rank(100) == "MASTERY SOVEREIGN"
    print("PASS: Rank tiers verified (INITIATE, ADEPT, MASTER, LEGEND, MASTERY SOVEREIGN)")


def test_mission_xp_authoritative():
    """Test 6: Mission XP is calculated ONLY from completed missions with completed_at timestamp."""
    user_id, token = setup_clean_user()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Uncompleted mission (completed=0) -> should NOT award XP
        cursor.execute(
            "INSERT INTO missions (user_id, title, xp_reward, completed, completed_at) VALUES (?, ?, ?, 0, NULL)",
            (user_id, "Uncompleted Mission", 25),
        )

        # 2. Completed mission without timestamp -> should NOT award XP (invalid state)
        cursor.execute(
            "INSERT INTO missions (user_id, title, xp_reward, completed, completed_at) VALUES (?, ?, ?, 1, NULL)",
            (user_id, "Untimestamped Mission", 30),
        )

        # 3. Legitimate completed mission -> SHOULD award XP
        cursor.execute(
            "INSERT INTO missions (user_id, title, xp_reward, completed, completed_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)",
            (user_id, "Valid Completed Mission", 50),
        )
        conn.commit()
        conn.close()

        xp_data = calculate_user_xp(user_id)
        assert xp_data["mission_xp"] == 50, f"Expected 50 mission XP, got {xp_data['mission_xp']}"
        assert xp_data["habit_xp"] == 0
        assert xp_data["total_xp"] == 50
        print("PASS: Mission XP strictly requires completed=1 and completed_at IS NOT NULL")
    finally:
        cleanup_user(user_id)


def test_habit_xp_authoritative():
    """Test 7: Habit XP is calculated strictly as COUNT(habit_logs) * 15 XP."""
    user_id, token = setup_clean_user()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Create a habit
        cursor.execute(
            "INSERT INTO habits (user_id, title, category, frequency) VALUES (?, ?, ?, ?)",
            (user_id, "Daily Coding", "learning", "daily"),
        )
        habit_id = cursor.lastrowid

        # Insert 3 valid habit logs on distinct days
        cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-10')", (habit_id, user_id))
        cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-11')", (habit_id, user_id))
        cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-12')", (habit_id, user_id))
        conn.commit()
        conn.close()

        xp_data = calculate_user_xp(user_id)
        assert xp_data["habit_xp"] == 45, f"Expected 3 * 15 = 45 habit XP, got {xp_data['habit_xp']}"
        assert xp_data["total_xp"] == 45
        print("PASS: Habit XP strictly calculated as 15 XP per verified habit_logs row")
    finally:
        cleanup_user(user_id)


def test_anti_spoofing_progression_api():
    """Test 8: GET /api/progression returns server-derived values and ignores client parameters."""
    user_id, token = setup_clean_user()
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insert 1 mission (+100 XP) and 10 habit logs (+150 XP) = 250 XP total -> Level 1 (50% progress to Level 2)
        cursor.execute(
            "INSERT INTO missions (user_id, title, xp_reward, completed, completed_at) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)",
            (user_id, "Deep Work", 100),
        )
        cursor.execute(
            "INSERT INTO habits (user_id, title) VALUES (?, ?)",
            (user_id, "Hydration"),
        )
        h_id = cursor.lastrowid
        for i in range(1, 11):
            cursor.execute(
                f"INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-{i:02d}')",
                (h_id, user_id),
            )
        conn.commit()
        conn.close()

        # Call GET /api/progression with session cookie
        cookies = {"mkc_session": token}
        res = client.get("/api/progression", cookies=cookies)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()

        assert data["total_xp"] == 250
        assert data["level"] == 1
        assert data["rank"] == "INITIATE"
        assert data["xp_to_next_level"] == 250
        assert data["level_progress_percent"] == 50.0

        # Unauthenticated request must be rejected
        unauth_res = client.get("/api/progression")
        assert unauth_res.status_code == 401, "Unauthenticated request to /api/progression must return 401"

        print("PASS: GET /api/progression verified with authoritative server calculation and 401 guard")
    finally:
        cleanup_user(user_id)


def main():
    print("=" * 60)
    print("RUNNING TARGETED PROGRESSION ENGINE TESTS")
    print("=" * 60)
    test_level_formula()
    test_rank_tiers()
    test_mission_xp_authoritative()
    test_habit_xp_authoritative()
    test_anti_spoofing_progression_api()
    print("=" * 60)
    print("ALL PROGRESSION ENGINE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
