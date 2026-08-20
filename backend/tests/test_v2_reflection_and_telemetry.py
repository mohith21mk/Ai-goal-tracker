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
    c.execute("DELETE FROM habits WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM journal_entries WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
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
    c.execute("DELETE FROM habits WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM journal_entries WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_daily_reflection_generates_structure():
    uid, token = setup_test_user("v2refl_gen")
    try:
        res = client.get("/api/reflection/daily", cookies={"mkc_session": token})
        assert res.status_code == 200
        data = res.json()
        assert "headline" in data or "summary" in data or "quote" in data or "reflection" in data or "status" in data
    finally:
        cleanup_test_user(uid)


def test_progress_endpoint_empty_and_with_missions():
    uid, token = setup_test_user("v2prog_msn")
    try:
        # Initial empty progress
        res_init = client.get("/api/progress", cookies={"mkc_session": token})
        assert res_init.status_code == 200
        data_init = res_init.json()
        assert data_init["total"] == 0
        assert data_init["completed"] == 0

        # Create 2 missions, complete 1
        m1 = client.post("/api/missions", json={"title": "M1"}, cookies={"mkc_session": token}).json()
        client.post("/api/missions", json={"title": "M2"}, cookies={"mkc_session": token})
        client.patch(f"/api/missions/{m1['id']}/toggle", cookies={"mkc_session": token})

        res_after = client.get("/api/progress", cookies={"mkc_session": token})
        assert res_after.status_code == 200
        data_after = res_after.json()
        assert data_after["total"] == 2
        assert data_after["completed"] == 1
        assert data_after["percentage"] == 50
    finally:
        cleanup_test_user(uid)


def test_telemetry_endpoint_structure():
    uid, token = setup_test_user("v2telem_str")
    try:
        res = client.get("/api/progress/telemetry", cookies={"mkc_session": token})
        assert res.status_code == 200
        data = res.json()
        assert "discipline_score" in data
        assert "mindset_strength" in data
        assert "growth_index" in data
        assert "sparklines" in data
        assert "mission_completion" in data
        assert "habits" in data
    finally:
        cleanup_test_user(uid)


def test_reflection_and_telemetry_unauthenticated():
    res_refl = client.get("/api/reflection/daily")
    assert res_refl.status_code == 401

    res_prog = client.get("/api/progress")
    assert res_prog.status_code == 401

    res_telem = client.get("/api/progress/telemetry")
    assert res_telem.status_code == 401
