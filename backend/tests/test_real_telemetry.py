import pytest
from app.database import get_connection, init_db
from app.api.progress import compute_telemetry

def setup_module(module):
    init_db()

def test_real_telemetry_historical_accuracy_and_isolation():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE username IN ('test_user_telemetry_a', 'test_user_telemetry_b')")
    conn.commit()

    # 1. Create User A
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, mkc_id, is_active) VALUES ('test_user_telemetry_a', 'tele_a@example.com', 'hash', 'User Telemetry A', 'MKC-TELE-A', 1)"
    )
    user_a_id = cursor.lastrowid

    # 2. Create User B
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, mkc_id, is_active) VALUES ('test_user_telemetry_b', 'tele_b@example.com', 'hash', 'User Telemetry B', 'MKC-TELE-B', 1)"
    )
    user_b_id = cursor.lastrowid
    conn.commit()
    conn.close()

    import asyncio

    # Test initial zero state for User A
    tel_a_initial = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_initial["discipline_score"] == 0
    assert tel_a_initial["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 0]
    assert tel_a_initial["sparklines"]["missions_completed"] == [0, 0, 0, 0, 0, 0, 0]
    assert tel_a_initial["discipline_score_change"] == 0

    # Add 2 missions for User A created today, complete 1 today
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO missions (user_id, title, category, completed, completed_at) VALUES (?, 'Mission 1', 'general', 1, CURRENT_TIMESTAMP)",
        (user_a_id,)
    )
    cursor.execute(
        "INSERT INTO missions (user_id, title, category, completed) VALUES (?, 'Mission 2', 'mindset', 0)",
        (user_a_id,)
    )
    conn.commit()
    conn.close()

    # Re-calculate telemetry for User A
    tel_a_active = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_active["mission_completion"]["completed"] == 1
    assert tel_a_active["mission_completion"]["total"] == 2
    assert tel_a_active["discipline_score"] > 0
    assert tel_a_active["sparklines"]["missions_completed"] == [0, 0, 0, 0, 0, 0, 1]
    assert tel_a_active["sparklines"]["discipline_score"][-1] == tel_a_active["discipline_score"]
    assert tel_a_active["discipline_score_change"] == tel_a_active["discipline_score"]
    assert tel_a_active["missions_completed_change"] == 1

    # Verify User B isolation
    tel_b = asyncio.run(compute_telemetry(user_b_id))
    assert tel_b["discipline_score"] == 0
    assert tel_b["mission_completion"]["completed"] == 0
    assert tel_b["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 0]
