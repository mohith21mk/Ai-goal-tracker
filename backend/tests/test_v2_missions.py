import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

app = create_app()
client = TestClient(app)


def setup_test_user(prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
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
