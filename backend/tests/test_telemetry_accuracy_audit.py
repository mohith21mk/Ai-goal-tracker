import asyncio
import datetime
import pytest
from app.database import get_connection, init_db
from app.api.progress import compute_telemetry

def setup_module(module):
    init_db()

def test_controlled_telemetry_accuracy_sequence_and_isolation():
    conn = get_connection()
    cursor = conn.cursor()

    today_str = datetime.date.today().strftime("%Y-%m-%d")

    cursor.execute("DELETE FROM users WHERE username IN ('audit_user_a', 'audit_user_b')")
    conn.commit()

    # 1. Create User A and User B
    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, mkc_id, is_active) VALUES ('audit_user_a', 'audit_a@example.com', 'hash', 'Audit User A', 'MKC-AUD-A', 1)"
    )
    user_a_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (username, email, password_hash, full_name, mkc_id, is_active) VALUES ('audit_user_b', 'audit_b@example.com', 'hash', 'Audit User B', 'MKC-AUD-B', 1)"
    )
    user_b_id = cursor.lastrowid
    conn.commit()

    # --- STEP 1: Fresh Account Verification (User A) ---
    tel_a_step1 = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_step1["discipline_score"] == 0
    assert tel_a_step1["mindset_strength"] == 0
    assert tel_a_step1["consistency"] == 0
    assert tel_a_step1["growth_index"] == 0
    assert tel_a_step1["financial_goal"] == 0
    assert tel_a_step1["streak_days"] == 0
    assert tel_a_step1["xp_earned"] == 0
    assert tel_a_step1["mission_completion"]["completed"] == 0
    assert tel_a_step1["mission_completion"]["total"] == 0

    for key, spark in tel_a_step1["sparklines"].items():
        assert spark == [0, 0, 0, 0, 0, 0, 0], f"Sparkline for {key} is not zero-state"

    # --- STEP 2: Complete 1 Mission ---
    cursor.execute(
        "INSERT INTO missions (user_id, title, category, xp_reward, completed, completed_at) VALUES (?, 'Audit Mission 1', 'general', 10, 1, CURRENT_TIMESTAMP)",
        (user_a_id,)
    )
    cursor.execute(
        "INSERT INTO missions (user_id, title, category, xp_reward, completed) VALUES (?, 'Audit Mission 2', 'mindset', 15, 0)",
        (user_a_id,)
    )
    conn.commit()

    tel_a_step2 = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_step2["mission_completion"]["completed"] == 1
    assert tel_a_step2["mission_completion"]["total"] == 2
    assert tel_a_step2["mission_completion"]["percentage"] == 50
    assert tel_a_step2["xp_earned"] == 10
    # Formula: mission_pct(50)*0.50 + habit_weekly(0)*0.30 + streak_comp(10)*0.20 = 25 + 0 + 2 = 27
    assert tel_a_step2["discipline_score"] == 27
    assert tel_a_step2["sparklines"]["missions_completed"] == [0, 0, 0, 0, 0, 0, 1]
    assert tel_a_step2["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 27]
    assert tel_a_step2["discipline_score_change"] == 27
    assert tel_a_step2["missions_completed_change"] == 1

    # --- STEP 3: Complete 2nd Mission (Mindset) ---
    cursor.execute(
        "UPDATE missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE user_id = ? AND title = 'Audit Mission 2'",
        (user_a_id,)
    )
    conn.commit()

    tel_a_step3 = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_step3["mission_completion"]["completed"] == 2
    assert tel_a_step3["mission_completion"]["total"] == 2
    assert tel_a_step3["mission_completion"]["percentage"] == 100
    assert tel_a_step3["xp_earned"] == 25  # 10 + 15
    # Formula: mission_pct(100)*0.50 + habit_weekly(0)*0.30 + streak_comp(10)*0.20 = 50 + 0 + 2 = 52
    assert tel_a_step3["discipline_score"] == 52
    assert tel_a_step3["mindset_strength"] == 100  # 100% mindset completed
    assert tel_a_step3["sparklines"]["missions_completed"] == [0, 0, 0, 0, 0, 0, 2]
    assert tel_a_step3["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 52]
    assert tel_a_step3["discipline_score_change"] == 52

    # --- STEP 4: Log 1 Habit ---
    cursor.execute(
        "INSERT INTO habits (user_id, title, category, frequency, target_days_per_week, status) VALUES (?, 'Audit Habit', 'health', 'daily', 7, 'active')",
        (user_a_id,)
    )
    habit_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, ?)",
        (habit_id, user_a_id, today_str)
    )
    conn.commit()

    tel_a_step4 = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_step4["habits"]["total_active_habits"] == 1
    assert tel_a_step4["habits"]["habits_completed_today"] == 1
    assert tel_a_step4["habits"]["overall_7day_completion_pct"] == 14  # 1 log out of 7 possible = 14%
    # Formula: mission_pct(100)*0.50 + habit_weekly(14)*0.30 + streak_comp(10)*0.20 = 50 + 4.2 + 2 = 56
    assert tel_a_step4["discipline_score"] == 56
    assert tel_a_step4["sparklines"]["discipline_score"] == [0, 0, 0, 0, 0, 0, 56]
    assert tel_a_step4["financial_goal"] == 0  # Unrelated metric unaffected

    # --- STEP 5: Add 1 Reflection ---
    cursor.execute(
        """
        INSERT INTO journal_entries (user_id, entry_date, mood, energy_level, wins_text, challenges_text, learnings_text, growth_next_text)
        VALUES (?, ?, 'focused', 8, 'Won test audit', 'None', 'Learned pytest', 'Keep building')
        """,
        (user_a_id, today_str)
    )
    conn.commit()

    tel_a_step5 = asyncio.run(compute_telemetry(user_a_id))
    assert tel_a_step5["journal"]["total_entries"] == 1
    assert tel_a_step5["journal"]["journal_streak"] == 1
    assert tel_a_step5["journal"]["avg_energy_7d"] == 8.0
    # Mindset Strength = mindset_base(100)*0.40 + streak(20)*0.30 + energy(80)*0.30 = 40 + 6 + 24 = 70
    assert tel_a_step5["mindset_strength"] == 70
    # Discipline Score remains unaffected by journal entry (remains 56)
    assert tel_a_step5["discipline_score"] == 56

    # --- STEP 6: Multi-User Isolation Verification (User B) ---
    tel_b = asyncio.run(compute_telemetry(user_b_id))
    assert tel_b["discipline_score"] == 0
    assert tel_b["mindset_strength"] == 0
    assert tel_b["consistency"] == 0
    assert tel_b["growth_index"] == 0
    assert tel_b["financial_goal"] == 0
    assert tel_b["streak_days"] == 0
    assert tel_b["xp_earned"] == 0
    assert tel_b["mission_completion"]["completed"] == 0
    for key, spark in tel_b["sparklines"].items():
        assert spark == [0, 0, 0, 0, 0, 0, 0], f"User B sparkline for {key} leaked User A data"

    conn.close()
