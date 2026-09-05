import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.services.progression import calculate_user_xp

app = create_app()
client = TestClient(app)


def setup_test_user(prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM mission_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM missions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()
    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials) VALUES (?, ?, ?, ?, ?, 1, 1, ?)",
        (f"{prefix}@test.mkc", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TU"),
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()
    token = create_session(uid)
    return uid, token


def cleanup_test_user(uid: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM mission_logs WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM missions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_create_mission_success():
    uid, token = setup_test_user("v2msn_cr")
    try:
        res = client.post(
            "/api/missions",
            json={
                "title": "Complete Morning Protocol",
                "description": "5 AM wake up and hydration",
                "category": "Discipline",
                "time": "20 min",
                "difficulty": "medium",
                "xp_reward": 25,
            },
            cookies={"mkc_session": token},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["title"] == "Complete Morning Protocol"
        assert data["completed"] is False
        assert data["xp_reward"] == 25
    finally:
        cleanup_test_user(uid)


def test_toggle_mission_idempotency_and_state():
    uid, token = setup_test_user("v2msn_tg")
    try:
        res = client.post(
            "/api/missions",
            json={"title": "Mission to toggle", "category": "General"},
            cookies={"mkc_session": token},
        )
        mid = res.json()["id"]

        # Toggle on
        res_t1 = client.patch(f"/api/missions/{mid}/toggle", cookies={"mkc_session": token})
        assert res_t1.status_code == 200
        assert res_t1.json()["completed"] is True

        # Toggle off
        res_t2 = client.patch(f"/api/missions/{mid}/toggle", cookies={"mkc_session": token})
        assert res_t2.status_code == 200
        assert res_t2.json()["completed"] is False
    finally:
        cleanup_test_user(uid)


def test_toggle_nonexistent_mission_rejected():
    uid, token = setup_test_user("v2msn_nonex")
    try:
        res = client.patch("/api/missions/9999999/toggle", cookies={"mkc_session": token})
        assert res.status_code == 404
    finally:
        cleanup_test_user(uid)


def test_toggle_other_users_mission_rejected():
    uid_a, token_a = setup_test_user("v2msn_ua")
    uid_b, token_b = setup_test_user("v2msn_ub")
    try:
        res = client.post(
            "/api/missions",
            json={"title": "User A Private Mission"},
            cookies={"mkc_session": token_a},
        )
        mid = res.json()["id"]

        # User B tries to toggle User A's mission
        res_b = client.patch(f"/api/missions/{mid}/toggle", cookies={"mkc_session": token_b})
        assert res_b.status_code == 404
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_missions_unauthenticated_guards():
    res_list = client.get("/api/missions")
    assert res_list.status_code == 401

    res_post = client.post("/api/missions", json={"title": "No auth mission"})
    assert res_post.status_code == 401


def test_daily_mission_auto_reset_on_next_day():
    """
    CRITICAL USER REQUIREMENT:
    When a daily mission is completed on Day 1, on Day 2 (next day) the checklist
    must automatically reset to unchecked, while Day 1's history and XP are preserved.
    Completing it again on Day 2 accumulates XP and maintains streak.
    """
    uid, token = setup_test_user("v2msn_rst")
    try:
        # Create 2 starter daily missions
        m1 = client.post(
            "/api/missions",
            json={"title": "Morning Protocol & System Architecture Block", "xp_reward": 15},
            cookies={"mkc_session": token},
        ).json()
        m2 = client.post(
            "/api/missions",
            json={"title": "Complete Morning Deep Work Protocol", "xp_reward": 15},
            cookies={"mkc_session": token},
        ).json()

        m1_id = m1["id"]
        m2_id = m2["id"]

        # 1. Day 1: Complete m1 on Day 1 (2026-09-04)
        day1 = "2026-09-04"
        res_t1 = client.patch(f"/api/missions/{m1_id}/toggle?target_date={day1}", cookies={"mkc_session": token})
        assert res_t1.status_code == 200
        assert res_t1.json()["completed"] is True

        # Check Day 1 status: m1 is completed, m2 is not completed
        res_day1 = client.get(f"/api/missions?target_date={day1}", cookies={"mkc_session": token})
        assert res_day1.status_code == 200
        day1_missions = {m["id"]: m["completed"] for m in res_day1.json()}
        assert day1_missions[m1_id] is True
        assert day1_missions[m2_id] is False

        # Verify Day 1 XP: exactly 15 XP
        xp_day1 = calculate_user_xp(uid)
        assert xp_day1["total_xp"] == 15

        # 2. Day 2 arrives (2026-09-05)
        # THE CHECKLIST MUST AUTOMATICALLY RESET TO UNCHECKED FOR BOTH MISSIONS!
        day2 = "2026-09-05"
        res_day2 = client.get(f"/api/missions?target_date={day2}", cookies={"mkc_session": token})
        assert res_day2.status_code == 200
        day2_missions = {m["id"]: m["completed"] for m in res_day2.json()}
        # Both missions must be unchecked (auto-reset)!
        assert day2_missions[m1_id] is False, "Completed mission from Day 1 must reset to unchecked on Day 2"
        assert day2_missions[m2_id] is False, "Uncompleted mission from Day 1 must remain unchecked on Day 2"

        # Overall XP must NOT reset on Day 2
        xp_day2_morning = calculate_user_xp(uid)
        assert xp_day2_morning["total_xp"] == 15, "XP must persist across days"

        # 3. User completes both missions on Day 2!
        res_t1_d2 = client.patch(f"/api/missions/{m1_id}/toggle?target_date={day2}", cookies={"mkc_session": token})
        assert res_t1_d2.status_code == 200
        assert res_t1_d2.json()["completed"] is True

        res_t2_d2 = client.patch(f"/api/missions/{m2_id}/toggle?target_date={day2}", cookies={"mkc_session": token})
        assert res_t2_d2.status_code == 200
        assert res_t2_d2.json()["completed"] is True

        # Now on Day 2: 2/2 Protocol Completed Today
        res_day2_after = client.get(f"/api/missions?target_date={day2}", cookies={"mkc_session": token})
        day2_missions_after = {m["id"]: m["completed"] for m in res_day2_after.json()}
        assert day2_missions_after[m1_id] is True
        assert day2_missions_after[m2_id] is True

        # Total XP has accumulated: 15 (from Day 1) + 15 (m1 Day 2) + 15 (m2 Day 2) = 45 XP!
        xp_day2_night = calculate_user_xp(uid)
        assert xp_day2_night["total_xp"] == 45, "XP must be cumulative across days"

        # 4. Day 3 arrives (2026-09-06)
        # THE CHECKLIST MUST RESET AGAIN!
        day3 = "2026-09-06"
        res_day3 = client.get(f"/api/missions?target_date={day3}", cookies={"mkc_session": token})
        day3_missions = {m["id"]: m["completed"] for m in res_day3.json()}
        assert day3_missions[m1_id] is False, "Checklist must reset again on Day 3"
        assert day3_missions[m2_id] is False, "Checklist must reset again on Day 3"
        # Total XP remains 45!
        assert calculate_user_xp(uid)["total_xp"] == 45

    finally:
        cleanup_test_user(uid)
